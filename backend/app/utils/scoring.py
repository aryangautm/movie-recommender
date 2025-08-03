import math

W_VOTE = 0.5
W_AI = 0.3
W_SIMILARITY = 0.2
CREDIBILITY_CONSTANT = 10


def calculate_effective_score(
    user_votes: int, ai_score: float | None, similarity_score: float | None
) -> float:
    """
    Calculates the unified effective score based on all available signals.
    Handles None values gracefully by treating them as 0.
    """
    norm_vote = math.log(1 + user_votes) / math.log(
        1 + user_votes + CREDIBILITY_CONSTANT
    )

    norm_ai = (ai_score / 10.0) if ai_score is not None else 0.0

    norm_sim = similarity_score if similarity_score is not None else 0.0

    effective_score = (
        (W_VOTE * norm_vote) + (W_AI * norm_ai) + (W_SIMILARITY * norm_sim)
    )

    return round(effective_score, 4)
