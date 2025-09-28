import hashlib

from app import schemas
from app.core.database import SessionLocal, get_async_db
from app.crud import crud_movie, crud_recommendation
from app.services import llm_client
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post(
    "",
    response_model=schemas.recommendation.RecResponse,
    status_code=status.HTTP_200_OK,
)
async def get_advanced_recommendations(
    request: schemas.recommendation.RecRequest,
    db: AsyncSession = Depends(get_async_db),
):
    # Fetching and Validating the Source Movie
    source_movie_id = request.source_movie_id
    source_movie = await crud_movie.get_movie_by_id(db, source_movie_id)
    if not source_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source movie with ID {source_movie_id} not found.",
        )

    # Validating Selected Keywords
    valid_keywords = {
        kw.replace(".", "").lower() for kw in (source_movie.ai_keywords or [])
    }
    selected_keywords = set()
    if request.selected_keywords:
        selected_keywords = {
            kw.replace(".", "").lower() for kw in request.selected_keywords
        }

        if not selected_keywords.issubset(valid_keywords):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more selected keywords are not valid for this movie.",
            )

    keywords_str = "".join(sorted(request.selected_keywords))

    trigger_hash = hashlib.sha256(
        f"{source_movie_id}:{keywords_str}".encode()
    ).hexdigest()

    print(f"{source_movie_id}: {' ,'.join(selected_keywords)}")

    results = await crud_recommendation.get_recommendations_by_trigger_hash(
        db, trigger_hash
    )

    if results:
        return {
            "status": "complete",
            "results": results,
        }

    # If no cache generate recommendations using LLM
    async def recommendation_stream():

        with SessionLocal() as sync_db:
            for parsed_chunk in llm_client.multi_turn_rec(
                source_movie, request.selected_keywords
            ):
                print("Parsed Chunk:", parsed_chunk)

                enriched_chunk = crud_movie.enrich_recommendations(
                    sync_db, parsed_chunk
                )

                recs_to_save = [
                    {
                        "source_movie_id": source_movie_id,
                        "trigger_keywords_hash": trigger_hash,
                        "recommended_movie_id": rec["id"],
                        "llm_justification": rec["justification"],
                        "llm_score": rec["ai_score"],
                    }
                    for rec in enriched_chunk
                ]

                _ = crud_recommendation.bulk_create_llm_recommendations(
                    sync_db, recs_to_save
                )

                yield schemas.recommendation.RecResponse(
                    **{
                        "status": "partial",
                        "results": enriched_chunk,
                    }
                ).model_dump_json() + "\n"

        print("---Completed---")

    return StreamingResponse(recommendation_stream(), media_type="application/x-ndjson")
