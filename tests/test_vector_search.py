"""
Unit tests for Vector Search Engine
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from vector_search import VectorSearchEngine


@pytest.fixture
def mock_sentence_transformer():
    """Mock SentenceTransformer"""
    mock_model = MagicMock()
    mock_model.encode.return_value = np.random.rand(384)  # 384-dim embedding
    return mock_model


@pytest.fixture
def vector_engine_local(mock_sentence_transformer):
    """Create VectorSearchEngine with mocked local model"""
    with patch('vector_search.SentenceTransformer', return_value=mock_sentence_transformer):
        with patch('vector_search.SENTENCE_TRANSFORMERS_AVAILABLE', True):
            engine = VectorSearchEngine(embedding_provider="local")
            return engine


@pytest.fixture
def sample_intelligence():
    """Sample intelligence data"""
    return {
        "anonymized_id": "CAND_123",
        "cleaned_narrative": "Senior Python Developer with 7 years of experience",
        "core_technical_skills": ["Python", "Django", "Flask", "PostgreSQL"],
        "secondary_technical_skills": ["Docker", "AWS", "Redis"],
        "primary_domain": "Web Development",
        "seniority_level": "SENIOR",
        "years_experience": 7,
        "key_strengths": [
            "Strong backend development skills",
            "Experience with microservices",
            "Cloud infrastructure expertise"
        ]
    }


class TestVectorSearchEngine:
    """Test suite for VectorSearchEngine"""
    
    def test_init_local_provider(self, mock_sentence_transformer):
        """Test initialization with local provider"""
        with patch('vector_search.SentenceTransformer', return_value=mock_sentence_transformer):
            with patch('vector_search.SENTENCE_TRANSFORMERS_AVAILABLE', True):
                engine = VectorSearchEngine(embedding_provider="local")
                
                assert engine.embedding_provider == "local"
                assert engine.dimensions == 384
                assert engine.model is not None
    
    def test_init_openai_provider(self):
        """Test initialization with OpenAI provider"""
        with patch('vector_search.OPENAI_AVAILABLE', True):
            with patch('vector_search.openai'):
                engine = VectorSearchEngine(
                    embedding_provider="openai",
                    api_key="test-key"
                )
                
                assert engine.embedding_provider == "openai"
                assert engine.dimensions == 1536
                assert engine.api_key == "test-key"
    
    def test_init_invalid_provider(self):
        """Test initialization with invalid provider"""
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            VectorSearchEngine(embedding_provider="invalid")
    
    def test_generate_embedding_local(self, vector_engine_local):
        """Test embedding generation with local model"""
        text = "Python Django Flask PostgreSQL"
        embedding = vector_engine_local.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_embedding_empty_text(self, vector_engine_local):
        """Test embedding generation with empty text"""
        embedding = vector_engine_local.generate_embedding("")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(x == 0.0 for x in embedding)
    
    def test_build_embedding_text(self, vector_engine_local, sample_intelligence):
        """Test building text for embedding"""
        text = vector_engine_local.build_embedding_text(sample_intelligence)
        
        assert "Senior Python Developer" in text
        assert "Python" in text
        assert "Django" in text
        assert "Web Development" in text
        assert "SENIOR" in text
        assert "7 years" in text
    
    def test_build_embedding_text_minimal(self, vector_engine_local):
        """Test building text with minimal intelligence data"""
        minimal_intelligence = {
            "anonymized_id": "CAND_456",
            "cleaned_narrative": "Developer"
        }
        
        text = vector_engine_local.build_embedding_text(minimal_intelligence)
        
        assert "Developer" in text
        assert len(text) > 0
    
    def test_cosine_similarity_identical(self, vector_engine_local):
        """Test cosine similarity with identical vectors"""
        vec = [1.0, 2.0, 3.0, 4.0]
        similarity = vector_engine_local.cosine_similarity(vec, vec)
        
        assert similarity == pytest.approx(1.0, abs=0.01)
    
    def test_cosine_similarity_orthogonal(self, vector_engine_local):
        """Test cosine similarity with orthogonal vectors"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = vector_engine_local.cosine_similarity(vec1, vec2)
        
        assert similarity == pytest.approx(0.0, abs=0.01)
    
    def test_cosine_similarity_opposite(self, vector_engine_local):
        """Test cosine similarity with opposite vectors"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        similarity = vector_engine_local.cosine_similarity(vec1, vec2)
        
        # Cosine similarity of opposite vectors is -1, but we clamp to [0, 1]
        assert similarity == 0.0
    
    def test_cosine_similarity_zero_vector(self, vector_engine_local):
        """Test cosine similarity with zero vector"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]
        similarity = vector_engine_local.cosine_similarity(vec1, vec2)
        
        assert similarity == 0.0
    
    def test_search_local(self, vector_engine_local):
        """Test local search with candidate embeddings"""
        query_embedding = [1.0, 2.0, 3.0, 4.0]
        
        candidate_embeddings = [
            ("CAND_001", [1.0, 2.0, 3.0, 4.0]),  # Identical
            ("CAND_002", [1.1, 2.1, 3.1, 4.1]),  # Very similar
            ("CAND_003", [5.0, 6.0, 7.0, 8.0]),  # Different
            ("CAND_004", [0.0, 0.0, 0.0, 0.0]),  # Zero vector
        ]
        
        results = vector_engine_local.search_local(
            query_embedding,
            candidate_embeddings,
            limit=3,
            threshold=0.5
        )
        
        assert len(results) <= 3
        assert results[0]['candidate_id'] == "CAND_001"  # Most similar
        assert results[0]['similarity_score'] > 0.9
        
        # Results should be sorted by similarity
        for i in range(len(results) - 1):
            assert results[i]['similarity_score'] >= results[i + 1]['similarity_score']
    
    def test_search_local_no_matches(self, vector_engine_local):
        """Test local search with no matches above threshold"""
        query_embedding = [1.0, 0.0, 0.0, 0.0]
        
        candidate_embeddings = [
            ("CAND_001", [0.0, 1.0, 0.0, 0.0]),  # Orthogonal
            ("CAND_002", [0.0, 0.0, 1.0, 0.0]),  # Orthogonal
        ]
        
        results = vector_engine_local.search_local(
            query_embedding,
            candidate_embeddings,
            limit=10,
            threshold=0.9  # High threshold
        )
        
        assert len(results) == 0
    
    def test_validate_embedding_valid(self, vector_engine_local):
        """Test embedding validation with valid embedding"""
        embedding = [0.1] * 384
        
        assert vector_engine_local.validate_embedding(embedding) is True
    
    def test_validate_embedding_wrong_dimension(self, vector_engine_local):
        """Test embedding validation with wrong dimension"""
        embedding = [0.1] * 100  # Wrong dimension
        
        assert vector_engine_local.validate_embedding(embedding) is False
    
    def test_validate_embedding_all_zeros(self, vector_engine_local):
        """Test embedding validation with all zeros"""
        embedding = [0.0] * 384
        
        assert vector_engine_local.validate_embedding(embedding) is False
    
    def test_validate_embedding_empty(self, vector_engine_local):
        """Test embedding validation with empty list"""
        embedding = []
        
        assert vector_engine_local.validate_embedding(embedding) is False
    
    def test_save_and_load_embedding_cache(self, vector_engine_local, tmp_path):
        """Test saving and loading embedding cache"""
        cache_file = tmp_path / "embeddings.json"
        
        embeddings = {
            "CAND_001": [0.1, 0.2, 0.3],
            "CAND_002": [0.4, 0.5, 0.6]
        }
        
        # Save cache
        vector_engine_local.save_embedding_cache(str(cache_file), embeddings)
        
        assert cache_file.exists()
        
        # Load cache
        loaded = vector_engine_local.load_embedding_cache(str(cache_file))
        
        assert loaded == embeddings
    
    def test_load_embedding_cache_not_found(self, vector_engine_local):
        """Test loading non-existent cache file"""
        loaded = vector_engine_local.load_embedding_cache("nonexistent.json")
        
        assert loaded == {}
    
    def test_generate_embeddings_batch(self, vector_engine_local):
        """Test batch embedding generation"""
        texts = [
            "Python Django Flask",
            "JavaScript React Node.js",
            "Java Spring Boot"
        ]
        
        embeddings = vector_engine_local.generate_embeddings_batch(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
    
    def test_generate_embeddings_batch_empty(self, vector_engine_local):
        """Test batch embedding with empty list"""
        embeddings = vector_engine_local.generate_embeddings_batch([])
        
        assert embeddings == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
