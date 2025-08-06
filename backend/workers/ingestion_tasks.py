import logging
from tqdm import tqdm
from typing import List, Dict, Any
from app.core.database import SessionLocal
from datetime import datetime
from app.core.config import settings
from app.crud import crud_movie, crud_processing_queue
from app.models.processing_queue import TriggerSource, ProcessingStatus
from app.models.movie import MovieVisibility
from app.core.tmdb_client import tmdb_client


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .celery_config import celery_app


@celery_app.task(
    name="tasks.ingest_recommended_movies",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 60},
)
def ingest_recommended_movies():
    movies_to_create: List[Dict[str, Any]] = []
    processes_to_update: List[Dict[str, Any]] = []

    with SessionLocal() as db:
        try:
            pending_movies = crud_processing_queue.get_movies_by_sources(
                db, [TriggerSource.RECOMMENDATION]
            )
            crud_processing_queue.bulk_patch_process(
                db,
                [
                    {"id": movie.id, "status": ProcessingStatus.PROCESSING}
                    for movie in pending_movies
                ],
            )
            db.commit()

            if not pending_movies:
                logger.warning(
                    "No pending movies found in the processing queue. Exiting."
                )
                return

            genre_map = tmdb_client.get_genre_map()
            for movie in tqdm(pending_movies, desc="Processing movies"):
                if movie.release_year > datetime.now().year:
                    processes_to_update.append(
                        {
                            "id": movie.id,
                            "status": ProcessingStatus.FAILED,
                            "failure_reason": "FUTURE_RELEASE",
                        }
                    )
                    continue
                movie_data = tmdb_client.search_movie(
                    query=movie.title, release_year=movie.release_year
                )
                if not movie_data:
                    processes_to_update.append(
                        {
                            "id": movie.id,
                            "status": ProcessingStatus.FAILED,
                            "failure_reason": "NOT_FOUND",
                        }
                    )
                    continue

                genres = [
                    {"id": gid, "name": genre_map.get(gid, "Unknown")}
                    for gid in movie_data.get("genre_ids", [])
                ]

                release_date_str = movie_data.get("release_date", "")
                if not release_date_str:
                    processes_to_update.append(
                        {
                            "id": movie.id,
                            "status": ProcessingStatus.FAILED,
                            "failure_reason": "NO_RELEASE_DATE",
                        }
                    )
                    continue

                release_date = datetime.fromisoformat(release_date_str).date()
                release_year = release_date.year
                if release_date < datetime.now().date():
                    movies_to_create.append(
                        {
                            "id": movie_data.get("id"),
                            "title": movie_data.get("title"),
                            "overview": movie_data.get("overview"),
                            "release_date": release_date,
                            "release_year": release_year,
                            "poster_path": movie_data.get("poster_path"),
                            "backdrop_path": movie_data.get("backdrop_path"),
                            "genres": genres,
                            "additional_keywords": [
                                kw.capitalize()
                                for kw in movie.properties.get(
                                    "justification_keywords", []
                                )
                            ],
                            "vote_count": movie_data.get("vote_count"),
                            "vote_average": movie_data.get("vote_average"),
                            "visibility": MovieVisibility.PRIVATE,
                        }
                    )

                    processes_to_update.append(
                        {
                            "id": movie.id,
                            "source_movie_id": movie_data.get("id"),
                            "status": ProcessingStatus.COMPLETED,
                        }
                    )
                else:
                    processes_to_update.append(
                        {
                            "id": movie.id,
                            "status": ProcessingStatus.FAILED,
                            "failure_reason": "FUTURE_RELEASE",
                        }
                    )

            logger.info(f"Connecting to DB to ingest {len(movies_to_create)} movies.")
            crud_movie.bulk_create_movies(db, movies_to_create)
            logger.info(f"Successfully ingested {len(movies_to_create)} movies.")

            crud_processing_queue.bulk_patch_process(db, processes_to_update)

            db.commit()
            logger.info("Database ingestion successful.")
        except Exception as e:
            db.rollback()
            logger.error(f"Database ingestion failed: {e}")
            raise
