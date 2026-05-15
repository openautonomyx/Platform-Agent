"""Platform Agent ML - SurrealDB-native ML integration."""

from typing import Any, Optional, List
from dataclasses import dataclass


# =============================================================================
# SurrealML - Native ML in Database
# =============================================================================

class SurrealML:
    """SurrealML integration - runs ML models directly in SurrealDB.
    
    Uses SurrealDB's native ml:: functions:
    - ml::predict() - Run inference
    - ml::embed() - Generate embeddings
    - Custom .surml model files
    """
    
    def __init__(self, db):
        self._db = db
    
    async def load_model(
        self,
        model_path: str,
        model_name: str,
    ) -> dict:
        """Load a .surml model into SurrealDB.
        
        Uses: DEFINE MODEL $name AS $path
        """
        await self._db.query(f"DEFINE MODEL {model_name} AS {model_path}")
        return {"status": "loaded", "model": model_name}
    
    async def predict(
        self,
        model_name: str,
        inputs: dict,
    ) -> dict:
        """Run inference using SurrealQL.
        
        Uses: SELECT ml::predict('model', $inputs)
        """
        result = await self._db.query(
            f"SELECT ml::predict('{model_name}', $inputs) AS prediction",
            {"inputs": inputs}
        )
        return result[0] if result else {}
    
    async def embed(
        self,
        model_name: str,
        texts: List[str],
    ) -> List[List[float]]:
        """Generate embeddings using in-db model.
        
        Uses: SELECT ml::embed('model', $texts)
        """
        result = await self._db.query(
            f"SELECT ml::embed('{model_name}', $texts) AS embeddings",
            {"texts": texts}
        )
        return result[0].get("embeddings", []) if result else []


# =============================================================================
# Native Vector Search
# =============================================================================

class InDBEmbeddings:
    """In-database embeddings using SurrealDB's native vector functions."""
    
    def __init__(self, db, dimension: int = 1536, metric: str = "cosine"):
        self._db = db
        self._dimension = dimension
        self._metric = metric
    
    async def similarity_search(
        self,
        query_vector: List[float],
        table: str = "documents",
        field: str = "embedding",
        limit: int = 5,
    ) -> List[dict]:
        """Vector similarity search using native SurrealDB functions."""
        
        distance_func = {
            "cosine": "vector::similarity::cosine",
            "euclidean": "vector::distance::euclidean", 
            "manhattan": "vector::distance::manhattan",
        }.get(self._metric, "vector::similarity::cosine")
        
        query = f"""
        SELECT *, {distance_func}({field}, $query) AS distance
        FROM {table}
        ORDER BY distance ASC
        LIMIT {limit}
        """
        
        return await self._db.query(query, {"query": query_vector})


# =============================================================================
# Hybrid Search - Native RRF
# =============================================================================

class HybridSearch:
    """Hybrid search using SurrealDB's native capabilities."""
    
    def __init__(self, db):
        self._db = db
    
    async def search(
        self,
        query: str,
        vector_results: List[dict],
        text_results: List[dict],
        k: int = 60,
    ) -> List[dict]:
        """RRF using native SurrealDB."""
        # Can also use native: SELECT * FROM table WHERE text @1@ query OR embedding <|k|> $vec
        all_results = {r.get("id"): r for r in vector_results + text_results}
        
        rrf_scores = {}
        for rank, result in enumerate(vector_results):
            doc_id = result.get("id")
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + (1 / (k + rank + 1))
        
        for rank, result in enumerate(text_results):
            doc_id = result.get("id")
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + (1 / (k + rank + 1))
        
        return sorted(
            [{"id": k, **all_results[k], "rrf_score": v} for k, v in rrf_scores.items()],
            key=lambda x: x["rrf_score"],
            reverse=True,
        )