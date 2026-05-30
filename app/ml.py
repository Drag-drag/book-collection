import numpy as np
from sentence_transformers import SentenceTransformer

class MLService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def generate_embedding(self, title: str, author: str, genre: str, description: str = "") -> np.ndarray:
        text = f"{title} {author} {genre} {description or ''}"
        embedding = self.model.encode(text)
        return embedding

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if not norm_v1 or not norm_v2:
            return 0.0
        return float(dot_product / (norm_v1 * norm_v2))


ml_service = MLService()
