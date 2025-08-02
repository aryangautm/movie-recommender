import time
import logging
import csv
from pathlib import Path
from google import genai
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
BATCH_RESULTS_DIR = Path(__file__).parent / "batch_results"
BATCH_MANIFEST_FILE = ARTIFACTS_DIR / "batch_job_manifest.csv"

COMPLETED_STATES = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED"}

POLLING_INTERVAL_SECONDS = 60


def process_succeeded_job(client, batch_job):
    """
    Handles a successfully completed job by downloading and printing its results.
    This logic is adapted from the "Retrieving results" section on page 8.
    """
    job_name = batch_job.name
    logging.info(f"Processing successful job: {job_name}")

    if batch_job.dest and batch_job.dest.file_name:
        result_file_name = batch_job.dest.file_name
        print(f"\n--- Results for Job: {job_name} ---")
        print(f"Results are in file: {result_file_name}")

        try:
            print("Downloading result file content...")
            file_content = client.files.download(file=result_file_name)

            output_filename = f"{BATCH_RESULTS_DIR}/batch_result_{result_file_name.split("/")[1][-5:]}.jsonl"
            with open(output_filename, "w") as f:
                f.write(file_content.decode("utf-8"))

            print(f"Results appended to {output_filename}")
            print(f"--- End of Results for Job: {job_name} ---\n")
        except Exception as e:
            logging.error(
                f"Failed to download or process results for {job_name}. Error: {e}"
            )
    else:
        print(
            f"Job {job_name} succeeded, but no output file was found in the response."
        )


def monitor_all_batch_jobs():
    """
    Reads job names from the manifest file and polls their status until all are complete.
    Updates the manifest file with the latest job status.
    """
    logging.info("Starting batch job monitoring process.")

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logging.info("Google GenAI Client initialized.")
    except Exception as e:
        logging.error(f"Failed to initialize Google GenAI Client. Error: {e}")
        return

    manifest_path = Path(BATCH_MANIFEST_FILE)
    if not manifest_path.exists():
        logging.error(
            f"Manifest file not found: {BATCH_MANIFEST_FILE}. Cannot monitor jobs."
        )
        return

    all_jobs_data = []
    fieldnames = []
    try:
        with open(manifest_path, mode="r", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            all_jobs_data = list(reader)
    except (IOError, KeyError) as e:
        logging.error(f"Failed to read or parse {BATCH_MANIFEST_FILE}. Error: {e}")
        return

    active_jobs = [
        row["job_name"]
        for row in all_jobs_data
        if row.get("job_status") not in COMPLETED_STATES
    ]

    if not active_jobs:
        logging.info("No active jobs found in the manifest file to monitor.")
        return

    logging.info(f"Found {len(active_jobs)} jobs to monitor.")

    while active_jobs:
        logging.info(f"Polling cycle starting. {len(active_jobs)} jobs remaining.")
        status_changed_in_cycle = False

        for job_name in list(active_jobs):
            try:
                batch_job = client.batches.get(name=job_name)
                current_state = batch_job.state.name

                # Find the job in our in-memory list and check for status change
                job_data_to_update = next(
                    (job for job in all_jobs_data if job["job_name"] == job_name), None
                )

                if (
                    job_data_to_update
                    and job_data_to_update.get("job_status") != current_state
                ):
                    logging.info(
                        f"Job '{job_name}' status changed from '{job_data_to_update.get('job_status')}' to '{current_state}'"
                    )
                    job_data_to_update["job_status"] = current_state
                    status_changed_in_cycle = True

                    if current_state in COMPLETED_STATES:
                        if current_state == "JOB_STATE_SUCCEEDED":
                            process_succeeded_job(client, batch_job)
                        elif current_state == "JOB_STATE_FAILED":
                            print(f"\n--- Job Failed: {job_name} ---")
                            print(f"Error: {batch_job.error}")
                            print(f"--- End of Error for Job: {job_name} ---\n")
                        else:  # JOB_STATE_CANCELLED
                            print(f"\n--- Job Cancelled: {job_name} ---\n")

                        active_jobs.remove(job_name)
                else:
                    logging.info(
                        f"Job '{job_name}' status unchanged. Current state: {current_state}"
                    )

            except Exception as e:
                logging.error(f"An error occurred while polling job '{job_name}': {e}")

        # Write back to CSV if any status changed during the cycle
        if status_changed_in_cycle:
            try:
                with open(manifest_path, mode="w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_jobs_data)
                logging.info(f"Updated manifest file: {manifest_path}")
            except IOError as e:
                logging.error(f"Failed to write updates to {manifest_path}. Error: {e}")

        if active_jobs:
            print(
                f"\nWaiting {POLLING_INTERVAL_SECONDS} seconds before next polling cycle..."
            )
            time.sleep(POLLING_INTERVAL_SECONDS)

    print("\nAll batch jobs have completed.")


if __name__ == "__main__":
    monitor_all_batch_jobs()
