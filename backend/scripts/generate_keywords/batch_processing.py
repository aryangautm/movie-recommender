import json
from pathlib import Path
import logging
import math

from google import genai
from google.genai import types

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from datetime import datetime
from app.core.database import AsyncSessionLocal
from app.models.movie import Movie

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

REQUESTS_PER_BATCH = 1500
GEMINI_MODEL = "gemini-2.5-flash"

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
BATCH_REQUESTS_DIR = ARTIFACTS_DIR / "batch_requests"
BATCH_MANIFEST_PATH = ARTIFACTS_DIR / "batch_job_manifest.csv"
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.txt"


def initialize_genai_client() -> genai.Client | None:
    """Initializes and returns the Google GenAI Client."""
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logging.info("Google GenAI Client initialized.")
        return client
    except Exception as e:
        logging.error(f"Failed to initialize Google GenAI Client. Error: {e}")
        return None


def read_system_prompt(prompt_path: Path) -> str | None:
    """Reads the system prompt from a local file."""
    try:
        system_prompt = prompt_path.read_text().strip()
        logging.info(f"Successfully read system prompt from {prompt_path}.")
        return system_prompt
    except FileNotFoundError:
        logging.error(f"Error: {prompt_path} not found.")
        return None


async def fetch_all_movies(session: AsyncSession) -> list:
    """Fetches all movie entries from the database that do not have AI keywords yet."""
    logging.info("Connecting to the database to fetch movies without AI keywords.")
    try:
        query = (
            select(Movie.id, Movie.title, Movie.release_date)
            .where(
                Movie.ai_keywords.is_(None), Movie.release_date < datetime.now().date()
            )
            .order_by(Movie.vote_count.desc().nulls_last())
        )
        result = await session.execute(query)
        all_movies = result.all()
        logging.info(
            f"Fetched {len(all_movies)} movies without AI keywords from the database."
        )
        return all_movies
    except Exception as e:
        logging.error(f"An error occurred while fetching from the database: {e}")
        return []


def prepare_manifest_file(manifest_path: str):
    """
    Prepares the manifest file to log job details, writing a header if needed.
    """
    try:
        # Open in append mode, which creates the file if it doesn't exist.
        with open(manifest_path, "a") as f:
            if f.tell() == 0:
                f.write(
                    "job_name,input_file_name,start_movie_id,end_movie_id,request_count,job_status\n"
                )
    except IOError as e:
        logging.error(f"Could not open or write to manifest file {manifest_path}: {e}")
        raise


def prepare_batch_requests(movie_chunk: list, system_prompt: str) -> list:
    """Prepares a list of Gemini API requests for a chunk of movies."""
    requests_to_process = []
    for movie in movie_chunk:
        release_year = movie.release_date.year if movie.release_date else "Unknown"
        user_prompt_text = f"Movie Title: {movie.title}\nRelease Year: {release_year}"
        request_data = {
            "key": f"movie-{movie.id}",
            "request": {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_prompt_text}]}],
                "tools": [{"google_search": {}}],
            },
        }
        requests_to_process.append(request_data)
    return requests_to_process


def create_batch_request_file(requests: list, batch_index: int) -> str:
    """Writes a list of requests to a uniquely named JSONL file."""
    input_file_name = f"{BATCH_REQUESTS_DIR}/batch_request_{batch_index}.jsonl"
    try:
        with open(input_file_name, "w") as f:
            for req in requests:
                f.write(json.dumps(req) + "\n")
        logging.info(f"Created JSONL file for batch {batch_index}: {input_file_name}")
        return input_file_name
    except IOError as e:
        logging.error(
            f"Failed to write to {input_file_name} for batch {batch_index}: {e}"
        )
        raise


def submit_batch_job(
    client: genai.Client, input_file_name: str, batch_index: int
) -> tuple[types.BatchJob, str] | None:
    """Uploads a request file and creates a Gemini batch job."""
    try:
        logging.info(f"Uploading {input_file_name}...")
        uploaded_file = client.files.upload(
            file=input_file_name,
            config=types.UploadFileConfig(
                display_name="ai-keywords-requests", mime_type="jsonl"
            ),
        )
        logging.info(f"File for batch {batch_index} uploaded: {uploaded_file.name}")

        logging.info(f"Creating batch job for batch {batch_index}...")
        file_batch_job = client.batches.create(
            model=GEMINI_MODEL,
            src=uploaded_file.name,
            config={"display_name": f"ai-keywords-job-part-{batch_index}"},
        )
        logging.info(
            f"Successfully created batch job {batch_index}: {file_batch_job.name}"
        )
        return file_batch_job, uploaded_file.name
    except Exception as e:
        logging.error(f"Failed to process batch {batch_index}. Error: {e}")
        return None


def log_job_to_manifest(
    manifest_path: str, job_name: str, uploaded_file_name: str, movie_chunk: list
):
    """Logs the details of a created job to the manifest file."""
    try:
        start_movie_id = movie_chunk[0].id
        end_movie_id = movie_chunk[-1].id
        with open(manifest_path, "a") as f:
            log_entry = (
                f"{job_name},{uploaded_file_name},"
                f"{start_movie_id},{end_movie_id},{len(movie_chunk)},JOB_STATE_PENDING\n"
            )
            f.write(log_entry)
        logging.info(f"Recorded job details to {manifest_path}")
        print(f"Created and logged job: {job_name}")
    except IOError as e:
        logging.error(f"Failed to write job details to manifest file: {e}")


async def create_keyword_generation_batch_jobs():
    """
    Reads movie data, breaks it into chunks, and creates a separate Gemini
    Batch API job for each chunk, tracking the jobs in a manifest file.
    """
    logging.info("Starting chunked batch job creation process.")

    client = initialize_genai_client()
    if not client:
        return

    system_prompt = read_system_prompt(Path(SYSTEM_PROMPT_PATH))
    if not system_prompt:
        return

    async with AsyncSessionLocal() as session:
        all_movies = await fetch_all_movies(session)

    if not all_movies:
        logging.warning(
            "No movies found in the database with empty ai_keywords. Exiting."
        )
        return

    try:
        prepare_manifest_file(BATCH_MANIFEST_PATH)
    except IOError:
        return

    total_batches = math.ceil(len(all_movies) / REQUESTS_PER_BATCH)
    logging.info(
        f"Processing will be split into {total_batches} batches of up to {REQUESTS_PER_BATCH} requests each."
    )

    for i in range(0, len(all_movies), REQUESTS_PER_BATCH):
        movie_chunk = all_movies[i : i + REQUESTS_PER_BATCH]
        batch_index = (i // REQUESTS_PER_BATCH) + 1

        if not movie_chunk:
            continue

        logging.info(f"--- Processing Batch {batch_index}/{total_batches} ---")

        try:
            requests = prepare_batch_requests(movie_chunk, system_prompt)
            input_file_name = create_batch_request_file(requests, batch_index)

            job_result = submit_batch_job(client, input_file_name, batch_index)
            if job_result:
                job, uploaded_file_name = job_result
                log_job_to_manifest(
                    BATCH_MANIFEST_PATH, job.name, uploaded_file_name, movie_chunk
                )

        except Exception as e:
            logging.error(
                f"An error occurred while processing batch {batch_index}: {e}"
            )
            continue

    logging.info("All batches have been processed and submitted.")
