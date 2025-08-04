from .batch_processing import create_keyword_generation_batch_jobs
from .monitor_jobs import monitor_all_batch_jobs
from .save_keywords import process_results_and_update_db
import logging
import argparse

logging.basicConfig(level=logging.INFO)


def main():
    """
    Main function to run the keyword generation pipeline steps.
    """
    parser = argparse.ArgumentParser(
        description="Keyword Generation Pipeline Runner.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--run-batch", action="store_true", help="Run only the batch job creation step."
    )
    parser.add_argument(
        "--monitor", action="store_true", help="Run only the job monitoring step."
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Run only the results processing and saving step.",
    )

    args = parser.parse_args()

    run_specific_step = args.run_batch or args.monitor or args.save

    try:
        if not run_specific_step or args.run_batch:
            logging.info("Executing: Create keyword generation batch jobs...")
            create_keyword_generation_batch_jobs()
            logging.info("Completed: Create keyword generation batch jobs.")

        if not run_specific_step or args.monitor:
            logging.info("Executing: Monitor all batch jobs...")
            monitor_all_batch_jobs()
            logging.info("Completed: Monitor all batch jobs.")

        if not run_specific_step or args.save:
            logging.info("Executing: Process results and update DB...")
            process_results_and_update_db()
            logging.info("Completed: Process results and update DB.")

    except Exception as e:
        logging.error(
            f"An unexpected error occurred during script execution: {e}", exc_info=True
        )
        exit(1)


if __name__ == "__main__":
    main()
