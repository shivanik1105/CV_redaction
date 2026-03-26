"""
Unit tests for Enhanced Triage Engine
"""
import pytest
from enhanced_triage import EnhancedTriageEngine


@pytest.fixture
def triage_engine():
    """Create triage engine with default settings"""
    return EnhancedTriageEngine()


@pytest.fixture
def sample_jd():
    """Sample job description"""
    return """
    Senior Python Developer
    
    We are looking for an experienced Python developer with 5+ years of experience.
    
    Required Skills:
    - Python, Django, Flask, FastAPI
    - PostgreSQL, MongoDB, Redis
    - AWS, Docker, Kubernetes
    - REST APIs, Microservices
    - Git, CI/CD, Jenkins
    
    Nice to have:
    - React.js, TypeScript
    - Machine Learning, TensorFlow
    - Agile, Scrum
    """


@pytest.fixture
def matching_cv():
    """CV that matches the JD well"""
    return """
    Professional Summary:
    Senior Python Developer with 7 years of experience building scalable web applications.
    
    Technical Skills:
    - Languages: Python, JavaScript, TypeScript
    - Frameworks: Django, Flask, FastAPI, React.js
    - Databases: PostgreSQL, MongoDB, Redis
    - Cloud: AWS (EC2, S3, Lambda), Docker, Kubernetes
    - Tools: Git, Jenkins, CI/CD pipelines
    
    Experience:
    - Built REST APIs and microservices architecture
    - Deployed applications on AWS with Docker
    - Implemented CI/CD pipelines with Jenkins
    - Worked in Agile/Scrum teams
    """


@pytest.fixture
def non_matching_cv():
    """CV that doesn't match the JD"""
    return """
    Professional Summary:
    Experienced Marketing Manager with 8 years in digital marketing.
    
    Skills:
    - Social Media Marketing
    - Content Strategy
    - SEO, SEM, Google Analytics
    - Email Marketing, Mailchimp
    - Adobe Creative Suite
    - Campaign Management
    
    Experience:
    - Managed social media campaigns
    - Developed content strategies
    - Analyzed marketing metrics
    - Led marketing teams
    """


class TestEnhancedTriageEngine:
    """Test suite for Enhanced Triage Engine"""
    
    def test_extract_keywords_basic(self, triage_engine):
        """Test basic keyword extraction"""
        text = "Python Django Flask PostgreSQL AWS Docker Kubernetes"
        keywords = triage_engine.extract_keywords(text)
        
        assert 'python' in keywords
        assert 'django' in keywords
        assert 'flask' in keywords
        assert 'postgresql' in keywords
        assert 'docker' in keywords
        assert 'kubernetes' in keywords
    
    def test_extract_keywords_filters_stopwords(self, triage_engine):
        """Test stopwords are filtered out"""
        text = "Python developer with experience working on projects using Django"
        keywords = triage_engine.extract_keywords(text)
        
        assert 'python' in keywords
        assert 'django' in keywords
        assert 'developer' not in keywords  # Stopword
        assert 'experience' not in keywords  # Stopword
        assert 'working' not in keywords  # Stopword
    
    def test_extract_keywords_short_tech_terms(self, triage_engine):
        """Test short tech terms are included"""
        text = "C++ C# Go R AI ML SQL AWS GCP API UI UX"
        keywords = triage_engine.extract_keywords(text)
        
        assert 'c++' in keywords
        assert 'c#' in keywords
        assert 'go' in keywords
        assert 'r' in keywords
        assert 'ai' in keywords
        assert 'ml' in keywords
        assert 'sql' in keywords
        assert 'aws' in keywords
        assert 'api' in keywords
    
    def test_extract_keywords_filters_short_non_tech(self, triage_engine):
        """Test short non-tech words are filtered"""
        text = "the and for but was are"
        keywords = triage_engine.extract_keywords(text)
        
        assert len(keywords) == 0
    
    def test_compute_relevance_score_perfect_match(self, triage_engine):
        """Test relevance score with perfect match"""
        cv_keywords = {'python', 'django', 'postgresql', 'docker'}
        jd_keywords = {'python', 'django', 'postgresql', 'docker'}
        
        score = triage_engine.compute_relevance_score(cv_keywords, jd_keywords)
        
        assert score == 1.0  # 100% match
    
    def test_compute_relevance_score_partial_match(self, triage_engine):
        """Test relevance score with partial match"""
        cv_keywords = {'python', 'django', 'flask'}
        jd_keywords = {'python', 'django', 'postgresql', 'docker'}
        
        score = triage_engine.compute_relevance_score(cv_keywords, jd_keywords)
        
        assert score == 0.5  # 2/4 = 50% match
    
    def test_compute_relevance_score_no_match(self, triage_engine):
        """Test relevance score with no match"""
        cv_keywords = {'marketing', 'sales', 'advertising'}
        jd_keywords = {'python', 'django', 'postgresql', 'docker'}
        
        score = triage_engine.compute_relevance_score(cv_keywords, jd_keywords)
        
        assert score == 0.0  # 0% match
    
    def test_should_process_good_match(self, triage_engine, sample_jd, matching_cv):
        """Test CV with good match should be processed"""
        should_process, reason, score = triage_engine.should_process(matching_cv, sample_jd)
        
        assert should_process is True
        assert score > 0.30  # Above moderate threshold
        assert "Good match" in reason or "Moderate match" in reason
    
    def test_should_process_poor_match(self, triage_engine, sample_jd, non_matching_cv):
        """Test CV with poor match should be rejected"""
        should_process, reason, score = triage_engine.should_process(non_matching_cv, sample_jd)
        
        assert should_process is False
        assert score < 0.05  # Below extreme threshold
        assert "Extreme mismatch" in reason
    
    def test_should_process_cv_too_short(self, triage_engine, sample_jd):
        """Test CV that's too short is rejected"""
        short_cv = "Python developer"  # Only 2 words
        
        should_process, reason, score = triage_engine.should_process(short_cv, sample_jd)
        
        assert should_process is False
        assert "too short" in reason.lower()
        assert score == 0.0
    
    def test_should_process_empty_cv(self, triage_engine, sample_jd):
        """Test empty CV is rejected"""
        should_process, reason, score = triage_engine.should_process("", sample_jd)
        
        assert should_process is False
        assert score == 0.0
    
    def test_should_process_empty_jd(self, triage_engine, matching_cv):
        """Test with empty JD processes anyway"""
        should_process, reason, score = triage_engine.should_process(matching_cv, "")
        
        assert should_process is True  # Process if JD unclear
        assert score == 1.0
    
    def test_get_priority_from_score_high(self, triage_engine):
        """Test priority for high relevance score"""
        priority = triage_engine.get_priority_from_score(0.50)  # 50% match
        
        assert priority == 5  # NORMAL priority
    
    def test_get_priority_from_score_moderate(self, triage_engine):
        """Test priority for moderate relevance score"""
        priority = triage_engine.get_priority_from_score(0.20)  # 20% match
        
        assert priority == 10  # LOW priority
    
    def test_get_priority_from_score_low(self, triage_engine):
        """Test priority for low relevance score"""
        priority = triage_engine.get_priority_from_score(0.05)  # 5% match
        
        assert priority == 10  # LOW priority
    
    def test_custom_thresholds(self):
        """Test triage engine with custom thresholds"""
        engine = EnhancedTriageEngine(
            extreme_threshold=0.10,
            poor_threshold=0.25,
            moderate_threshold=0.40
        )
        
        assert engine.extreme_threshold == 0.10
        assert engine.poor_threshold == 0.25
        assert engine.moderate_threshold == 0.40
    
    def test_get_triage_stats(self, triage_engine, sample_jd):
        """Test triage statistics for batch of CVs"""
        cvs = [
            "Python Django Flask PostgreSQL AWS Docker",  # Good match
            "Python Flask MongoDB Redis",  # Moderate match
            "Java Spring Boot MySQL",  # Poor match
            "Marketing Sales Advertising",  # Extreme mismatch
            "Content Strategy SEO SEM"  # Extreme mismatch
        ]
        
        stats = triage_engine.get_triage_stats(cvs, sample_jd)
        
        assert stats['total_cvs'] == 5
        assert stats['rejected'] >= 2  # At least 2 extreme mismatches
        assert stats['api_calls_saved'] >= 2
        assert 0 <= stats['avg_relevance_score'] <= 1.0
        assert 0 <= stats['rejection_rate'] <= 100
    
    def test_tier_classification(self, triage_engine):
        """Test all four tier classifications"""
        jd = "Python Django Flask PostgreSQL AWS Docker Kubernetes Redis"
        
        # Tier 1: Extreme mismatch (< 5%)
        cv1 = "Marketing Sales Advertising Content Strategy"
        should_process, reason, score = triage_engine.should_process(cv1, jd)
        assert not should_process
        assert score < 0.05
        
        # Tier 2: Poor match (5-15%)
        cv2 = "Python Java JavaScript HTML CSS"
        should_process, reason, score = triage_engine.should_process(cv2, jd)
        # May or may not process depending on exact overlap
        
        # Tier 3: Moderate match (15-30%)
        cv3 = "Python Django MySQL MongoDB"
        should_process, reason, score = triage_engine.should_process(cv3, jd)
        assert should_process
        
        # Tier 4: Good match (> 30%)
        cv4 = "Python Django Flask PostgreSQL AWS Docker"
        should_process, reason, score = triage_engine.should_process(cv4, jd)
        assert should_process
        assert score > 0.30


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
