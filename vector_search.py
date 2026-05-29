"""
Vector Search Engine for Semantic Candidate Matching
Implements embedding generation and pgvector-based similarity search with Redis caching
"""
import os
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

# Import Redis cache
from redis_cache import (
    get_embedding_from_cache,
    cache_embedding,
    REDIS_AVAILABLE
)

logger = logging.getLogger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Install with: pip install sentence-transformers")

# Try to import OpenAI for alternative embedding
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class VectorSearchEngine:
    """
    Vector search engine for semantic candidate matching.
    Supports both local (sentence-transformers) and API-based (OpenAI) embeddings.
    """
    
    # Model configurations
    LOCAL_MODEL = "all-mpnet-base-v2"  # 768 dimensions, higher quality
    LOCAL_DIMENSIONS = 768
    
    OPENAI_MODEL = "text-embedding-3-small"  # 1536 dimensions, API-based
    OPENAI_DIMENSIONS = 1536
    
    def __init__(
        self,
        embedding_provider: str = "local",
        model_name: str = None,
        api_key: str = None
    ):
        """
        Initialize Vector Search Engine
        
        Args:
            embedding_provider: "local" (sentence-transformers) or "openai"
            model_name: Custom model name (optional)
            api_key: OpenAI API key (required for openai provider)
        """
        self.embedding_provider = embedding_provider
        self.model = None
        self.dimensions = None
        
        if embedding_provider == "local":
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
            
            model_name = model_name or self.LOCAL_MODEL
            logger.info(f"Loading local embedding model: {model_name}")
            
            try:
                self.model = SentenceTransformer(model_name)
                self.dimensions = self.LOCAL_DIMENSIONS
                logger.info(f"Local model loaded successfully ({self.dimensions} dimensions)")
            except Exception as e:
                logger.error(f"Failed to load local model: {e}")
                raise
        
        elif embedding_provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "openai not installed. "
                    "Install with: pip install openai"
                )
            
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key required for openai provider")
            
            openai.api_key = self.api_key
            self.model_name = model_name or self.OPENAI_MODEL
            self.dimensions = self.OPENAI_DIMENSIONS
            logger.info(f"Using OpenAI embeddings: {self.model_name} ({self.dimensions} dimensions)")
        
        else:
            raise ValueError(f"Unknown embedding provider: {embedding_provider}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text with Redis caching
        
        Args:
            text: Input text to embed
        
        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.dimensions
        
        # Check Redis cache first
        if REDIS_AVAILABLE:
            cached_embedding = get_embedding_from_cache(text)
            if cached_embedding is not None:
                logger.debug(f"✓ Using cached embedding ({len(cached_embedding)} dims)")
                return cached_embedding
        
        try:
            # Generate new embedding
            if self.embedding_provider == "local":
                # Use sentence-transformers
                embedding = self.model.encode(text, convert_to_numpy=True)
                embedding_list = embedding.tolist()
            
            elif self.embedding_provider == "openai":
                # Use OpenAI API
                response = openai.embeddings.create(
                    model=self.model_name,
                    input=text
                )
                embedding_list = response.data[0].embedding
            
            # Cache the new embedding
            if REDIS_AVAILABLE:
                cache_embedding(text, embedding_list)
            
            return embedding_list
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing)
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            if self.embedding_provider == "local":
                # Batch encode with sentence-transformers
                embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
                return embeddings.tolist()
            
            elif self.embedding_provider == "openai":
                # OpenAI supports batch embedding
                response = openai.embeddings.create(
                    model=self.model_name,
                    input=texts
                )
                return [item.embedding for item in response.data]
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def build_embedding_text(self, intelligence: Dict) -> str:
        """
        Build text for embedding from intelligence data
        Combines key fields for semantic search
        
        Args:
            intelligence: CV intelligence dictionary
        
        Returns:
            Combined text for embedding
        """
        parts = []
        
        # Add cleaned narrative (main summary)
        narrative = intelligence.get("cleaned_narrative", "")
        if narrative:
            parts.append(narrative)
        
        # Add core technical skills
        core_skills = intelligence.get("core_technical_skills", [])
        if core_skills:
            parts.append("Skills: " + ", ".join(core_skills))
        
        # Add secondary skills
        secondary_skills = intelligence.get("secondary_technical_skills", [])
        if secondary_skills:
            parts.append("Additional skills: " + ", ".join(secondary_skills))
        
        # Add primary domain
        domain = intelligence.get("primary_domain", "")
        if domain:
            parts.append(f"Domain: {domain}")
        
        # Add seniority level and years
        seniority = intelligence.get("seniority_level", "")
        years = intelligence.get("years_experience", 0)
        if seniority:
            parts.append(f"{seniority} level with {years} years experience")
        
        # Add key strengths
        strengths = intelligence.get("key_strengths", [])
        if strengths:
            parts.append("Strengths: " + ". ".join(strengths[:3]))  # Top 3
        
        return " ".join(parts)
    
    def cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Similarity score (0.0 to 1.0)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Compute cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Clamp to [0, 1] range
        return float(max(0.0, min(1.0, similarity)))
    
    def search_local(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[Tuple[str, List[float]]],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Search candidates locally using cosine similarity
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of (candidate_id, embedding) tuples
            limit: Maximum results to return
            threshold: Minimum similarity threshold
        
        Returns:
            List of matching candidates with similarity scores
        """
        results = []
        
        for candidate_id, embedding in candidate_embeddings:
            similarity = self.cosine_similarity(query_embedding, embedding)
            
            if similarity >= threshold:
                results.append({
                    "candidate_id": candidate_id,
                    "similarity_score": round(similarity, 4)
                })
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Return top K
        return results[:limit]
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate embedding vector
        
        Args:
            embedding: Embedding vector to validate
        
        Returns:
            True if valid, False otherwise
        """
        if not embedding:
            return False
        
        if len(embedding) != self.dimensions:
            logger.error(f"Invalid embedding dimension: {len(embedding)} (expected {self.dimensions})")
            return False
        
        # Check for all zeros
        if all(x == 0.0 for x in embedding):
            logger.warning("Embedding is all zeros")
            return False
        
        return True
    
    def save_embedding_cache(
        self,
        cache_file: str,
        embeddings: Dict[str, List[float]]
    ) -> None:
        """
        Save embeddings to cache file
        
        Args:
            cache_file: Path to cache file
            embeddings: Dictionary mapping candidate_id to embedding
        """
        try:
            cache_path = Path(cache_file)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(cache_path, 'w') as f:
                json.dump(embeddings, f)
            
            logger.info(f"Saved {len(embeddings)} embeddings to cache: {cache_file}")
        
        except Exception as e:
            logger.error(f"Error saving embedding cache: {e}")
    
    def load_embedding_cache(self, cache_file: str) -> Dict[str, List[float]]:
        """
        Load embeddings from cache file
        
        Args:
            cache_file: Path to cache file
        
        Returns:
            Dictionary mapping candidate_id to embedding
        """
        try:
            cache_path = Path(cache_file)
            
            if not cache_path.exists():
                logger.info(f"Cache file not found: {cache_file}")
                return {}
            
            with open(cache_path, 'r') as f:
                embeddings = json.load(f)
            
            logger.info(f"Loaded {len(embeddings)} embeddings from cache: {cache_file}")
            return embeddings
        
        except Exception as e:
            logger.error(f"Error loading embedding cache: {e}")
            return {}


# Singleton instance for easy import
_vector_search_engine = None

def get_vector_search_engine(
    embedding_provider: str = None,
    force_reload: bool = False
) -> VectorSearchEngine:
    """
    Get or create singleton vector search engine instance
    
    Args:
        embedding_provider: "local" or "openai" (default: from env or "local")
        force_reload: Force reload of model
    
    Returns:
        VectorSearchEngine instance
    """
    global _vector_search_engine
    
    if _vector_search_engine is None or force_reload:
        provider = embedding_provider or os.getenv("EMBEDDING_PROVIDER", "local")
        _vector_search_engine = VectorSearchEngine(embedding_provider=provider)
    
    return _vector_search_engine


def generate_embedding_for_intelligence(intelligence: Dict) -> List[float]:
    """
    Convenience function to generate embedding for intelligence data
    
    Args:
        intelligence: CV intelligence dictionary
    
    Returns:
        Embedding vector
    """
    engine = get_vector_search_engine()
    text = engine.build_embedding_text(intelligence)
    return engine.generate_embedding(text)
