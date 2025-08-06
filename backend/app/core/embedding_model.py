from functools import lru_cache
from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL_NAME = "all-mpnet-base-v2"


class EmbeddingModel:
    _embedding_model = None

    @classmethod
    def get_model(cls):
        if cls._embedding_model is None:
            print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
            cls._embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            print(f"Embedding model loaded")
        return cls._embedding_model


@lru_cache()
def get_embedding_model():
    return EmbeddingModel().get_model()
