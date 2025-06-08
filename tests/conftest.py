"""
Simple pytest configuration for SkillSprout tests
"""
import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def enhanced_user_progress():
    """Enhanced user progress for testing"""
    from space_app import EnhancedUserProgress
    return EnhancedUserProgress(
        user_id="test_user",
        skill="Python Programming",
        lessons_completed=3,
        quiz_scores=[80.0, 90.0, 70.0],
        mastery_level=75.0
    )

@pytest.fixture
def gamification_manager():
    """Gamification manager instance for testing"""
    from space_app import GamificationManager
    return GamificationManager()

# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings"""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow")
