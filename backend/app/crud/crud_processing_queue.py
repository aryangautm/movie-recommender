from sqlalchemy.orm import Session
from typing import List, Dict, Any
from sqlalchemy import insert
from app.models.processing_queue import ProcessingQueue, ProcessingStatus


def bulk_create_process(db: Session, movies: List[Dict[str, Any]]):
    if not movies:
        return

    try:
        db.execute(insert(ProcessingQueue), movies)
        db.commit()
    except Exception as e:
        with open("error_log.txt", "a") as error_file:
            error_file.write(f"Error during bulk create: {e}\n")
        db.rollback()


def get_movies_by_sources(db: Session, sources: List) -> List[ProcessingQueue]:
    """
    Fetches all movies from the processing queue by source.
    """
    try:
        return (
            db.query(ProcessingQueue)
            .filter(
                ProcessingQueue.trigger_source.in_(sources),
                ProcessingQueue.status == ProcessingStatus.PENDING,
            )
            .all()
        )
    except Exception as e:
        with open("error_log.txt", "a") as error_file:
            error_file.write(f"Error fetching movies by source {sources}: {e}\n")
        return []


def bulk_patch_process(
    db: Session, data: List[Dict[str, Any]]
) -> List[ProcessingQueue]:
    """
    Bulk updates the status of multiple movies in the processing queue.
    """
    if not data:
        return []

    try:
        for item in data:
            db.query(ProcessingQueue).filter_by(id=item["id"]).update(
                item, synchronize_session=False
            )
        db.commit()
        return data
    except Exception as e:
        with open("error_log.txt", "a") as error_file:
            error_file.write(f"Error during bulk patch process: {e}\n")
        db.rollback()
        raise
