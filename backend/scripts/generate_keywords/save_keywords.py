import asyncio
import json
import logging
from pathlib import Path
from app.core.database import AsyncSessionLocal
from app.crud import crud_movie

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

RESULTS_DIR = Path(__file__).parent / "batch_results"


def read_jsonl(file_path):
    """
    Reads a JSONL file and yields each data as a Python dictionary.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        for data in f:
            yield json.loads(data)


async def process_results_and_update_db():
    jsonl_files = list(RESULTS_DIR.glob("*.jsonl"))

    if not jsonl_files:
        logging.warning(f"No .jsonl files found in {RESULTS_DIR}. Exiting.")
        return

    logging.info(f"Found {len(jsonl_files)} result files to process.")

    for result_file_path in jsonl_files:
        logging.info(f"--- Processing file: {result_file_path.name} ---")
        movies_data_to_upsert = []

        try:
            for data in read_jsonl(result_file_path):
                if not data:
                    continue

                try:
                    # Extract key and response as per the specified structure.
                    key = data.get("key")
                    response = data.get("response")

                    if not (key and response):
                        logging.warning(
                            f"Skipping data in {key if key else ""} due to missing key or response: {data}"
                        )
                        continue

                    # Extract movie ID from the key.
                    movie_id = int(key.replace("movie-", ""))

                    # Safely navigate the response to get the keywords text.
                    candidates = response.get("candidates", [])
                    if (
                        candidates
                        and "content" in candidates[0]
                        and "parts" in candidates[0]["content"]
                    ):
                        keyword_str = candidates[0]["content"]["parts"][0].get(
                            "text", ""
                        )

                        # Convert the keyword string into a list.
                        keyword_list = [
                            k.strip() for k in keyword_str.split(",") if k.strip()
                        ]

                        if keyword_list:
                            movies_data_to_upsert.append(
                                {"id": movie_id, "ai_keywords": keyword_list}
                            )
                        else:
                            logging.warning(
                                f"No keywords found for movie_id {movie_id} in {result_file_path.name}."
                            )
                    else:
                        logging.warning(
                            f"Could not find keywords for movie_id {movie_id} in expected response structure."
                        )

                except (json.JSONDecodeError, ValueError, KeyError, IndexError) as e:
                    logging.error(
                        f"Error parsing data in {result_file_path.name}: {data}. Error: {e}"
                    )

            # Perform bulk upsert for the current batch.
            if movies_data_to_upsert:
                logging.info(
                    f"Preparing to upsert {len(movies_data_to_upsert)} records for job {result_file_path.name}."
                )
                try:
                    async with AsyncSessionLocal() as db:
                        await crud_movie.bulk_patch_movies(db, movies_data_to_upsert)
                    logging.info(
                        f"Successfully upserted keywords for job {result_file_path.name}."
                    )
                except Exception as e:
                    logging.error(
                        f"Database upsert failed for job {result_file_path.name}. Error: {e}"
                    )
            else:
                logging.warning(
                    f"No valid data found to upsert for job {result_file_path.name}."
                )

        except Exception as e:
            logging.error(
                f"An unexpected error occurred while processing job {result_file_path.name}: {e}"
            )

    logging.info("All result files have been processed.")


if __name__ == "__main__":
    asyncio.run(process_results_and_update_db())
