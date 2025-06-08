"""
Tests for the gamification system in SkillSprout
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from space_app import (
    GamificationManager, Achievement, UserStats, EnhancedUserProgress
)

class TestAchievement:
    """Test cases for Achievement data class"""
    
    def test_achievement_creation(self):
        """Test creating an achievement"""
        achievement = Achievement(
            id="test_achievement",
            name="Test Achievement",
            description="A test achievement",
            icon="🏆",
            unlocked=False,
            unlock_condition="Complete 1 lesson"
        )
        
        assert achievement.id == "test_achievement"
        assert achievement.name == "Test Achievement"
        assert achievement.unlocked is False
        assert achievement.icon == "🏆"
    
    def test_achievement_defaults(self):
        """Test achievement with default values"""
        achievement = Achievement(
            id="simple",
            name="Simple",
            description="Simple achievement",
            icon="⭐"
        )
        
        assert achievement.unlocked is False
        assert achievement.unlock_condition == ""

class TestUserStats:
    """Test cases for UserStats class"""
    
    def test_user_stats_creation(self):
        """Test creating user stats"""
        stats = UserStats(user_id="test_user")
        
        assert stats.user_id == "test_user"
        assert stats.total_points == 0
        assert stats.level == 1
        assert stats.achievements == []
        assert stats.streak_days == 0
        assert stats.total_lessons == 0
        assert stats.total_quizzes == 0
        assert stats.correct_answers == 0
    
    def test_add_points_no_level_up(self):
        """Test adding points without level up"""
        stats = UserStats(user_id="test_user")
        
        # Act
        stats.add_points(50)
        
        # Assert
        assert stats.total_points == 50
        assert stats.level == 1  # Should still be level 1
    
    def test_add_points_level_up(self):
        """Test adding points that triggers level up"""
        stats = UserStats(user_id="test_user")
        
        # Act
        stats.add_points(150)  # Should trigger level up
        
        # Assert
        assert stats.total_points == 150
        assert stats.level == 2
    
    def test_add_points_multiple_levels(self):
        """Test adding points that triggers multiple level ups"""
        stats = UserStats(user_id="test_user")
        
        # Act
        stats.add_points(450)  # Should reach level 5
        
        # Assert
        assert stats.total_points == 450
        assert stats.level == 5
    
    def test_add_points_max_level(self):
        """Test that level doesn't exceed maximum"""
        stats = UserStats(user_id="test_user")
        
        # Act
        stats.add_points(2000)  # Way more than needed for max level
        
        # Assert
        assert stats.level == 10  # Should cap at level 10
    
    def test_get_accuracy_no_quizzes(self):
        """Test accuracy calculation with no quizzes"""
        stats = UserStats(user_id="test_user")
        
        # Act & Assert
        assert stats.get_accuracy() == 0.0
    
    def test_get_accuracy_with_quizzes(self):
        """Test accuracy calculation with quiz data"""
        stats = UserStats(user_id="test_user")
        stats.total_quizzes = 10
        stats.correct_answers = 8
        
        # Act
        accuracy = stats.get_accuracy()
        
        # Assert
        assert accuracy == 80.0

class TestEnhancedUserProgress:
    """Test cases for EnhancedUserProgress class"""
    
    def test_enhanced_progress_creation(self):
        """Test creating enhanced user progress"""
        progress = EnhancedUserProgress(
            user_id="test_user",
            skill="Python Programming"
        )
        
        assert progress.user_id == "test_user"
        assert progress.skill == "Python Programming"
        assert progress.lessons_completed == 0
        assert progress.quiz_scores == []
        assert progress.time_spent == []
        assert progress.mastery_level == 0.0

class TestGamificationManager:
    """Test cases for GamificationManager class"""
    
    @pytest.fixture
    def gamification_manager(self):
        """Create a GamificationManager instance for testing"""
        return GamificationManager()
    
    def test_gamification_manager_initialization(self, gamification_manager):
        """Test GamificationManager initialization"""
        assert len(gamification_manager.user_stats) == 0
        assert len(gamification_manager.achievements) > 0
        
        # Check that all required achievements exist
        required_achievements = [
            "first_steps", "quiz_master", "persistent", "scholar",
            "expert", "polyglot", "perfectionist", "speed", 
            "consistent", "explorer"
        ]
        
        for achievement_id in required_achievements:
            assert achievement_id in gamification_manager.achievements
    
    def test_get_user_stats_new_user(self, gamification_manager):
        """Test getting stats for a new user"""
        # Act
        stats = gamification_manager.get_user_stats("new_user")
        
        # Assert
        assert isinstance(stats, UserStats)
        assert stats.user_id == "new_user"
        assert stats.total_points == 0
        assert stats.level == 1
    
    def test_get_user_stats_existing_user(self, gamification_manager):
        """Test getting stats for existing user"""
        # Arrange
        user_id = "existing_user"
        stats1 = gamification_manager.get_user_stats(user_id)
        stats1.total_points = 100
        
        # Act
        stats2 = gamification_manager.get_user_stats(user_id)
        
        # Assert
        assert stats2.total_points == 100
        assert stats1 is stats2  # Should be same object
    
    def test_check_achievements_first_steps(self, gamification_manager):
        """Test unlocking first steps achievement"""
        # Arrange
        user_id = "test_user"
        progress = EnhancedUserProgress(user_id=user_id, skill="Python")
        
        # Set up conditions for first steps achievement
        stats = gamification_manager.get_user_stats(user_id)
        stats.total_lessons = 1
        
        # Act
        newly_unlocked = gamification_manager.check_achievements(user_id, progress)
        
        # Assert
        assert len(newly_unlocked) > 0
        achievement_ids = [a.id for a in newly_unlocked]
        assert "first_steps" in achievement_ids
        assert "first_steps" in stats.achievements
    
    def test_check_achievements_quiz_master(self, gamification_manager):
        """Test unlocking quiz master achievement"""
        # Arrange
        user_id = "quiz_master_user"
        progress = EnhancedUserProgress(user_id=user_id, skill="Python")
        progress.quiz_scores = [100, 80, 100]  # Has perfect score
        
        # Act
        newly_unlocked = gamification_manager.check_achievements(user_id, progress)
        
        # Assert
        achievement_ids = [a.id for a in newly_unlocked]
        assert "quiz_master" in achievement_ids
    
    def test_check_achievements_persistent(self, gamification_manager):
        """Test unlocking persistent learner achievement"""
        # Arrange
        user_id = "persistent_user"
        progress = EnhancedUserProgress(user_id=user_id, skill="Python")
        
        stats = gamification_manager.get_user_stats(user_id)
        stats.total_lessons = 5
        
        # Act
        newly_unlocked = gamification_manager.check_achievements(user_id, progress)
        
        # Assert
        achievement_ids = [a.id for a in newly_unlocked]
        assert "persistent" in achievement_ids
    
    def test_check_achievements_no_new_unlocks(self, gamification_manager):
        """Test checking achievements when none should be unlocked"""
        # Arrange
        user_id = "minimal_user"
        progress = EnhancedUserProgress(user_id=user_id, skill="Python")
        # User has minimal progress, shouldn't unlock anything
        
        # Act
        newly_unlocked = gamification_manager.check_achievements(user_id, progress)
        
        # Assert
        assert len(newly_unlocked) == 0
    
    def test_check_achievements_already_unlocked(self, gamification_manager):
        """Test that already unlocked achievements aren't returned again"""
        # Arrange
        user_id = "repeat_user"
        progress = EnhancedUserProgress(user_id=user_id, skill="Python")
        
        stats = gamification_manager.get_user_stats(user_id)
        stats.total_lessons = 1
        stats.achievements = ["first_steps"]  # Already unlocked
        
        # Act
        newly_unlocked = gamification_manager.check_achievements(user_id, progress)
        
        # Assert
        achievement_ids = [a.id for a in newly_unlocked]
        assert "first_steps" not in achievement_ids
    
    def test_check_achievements_points_awarded(self, gamification_manager):
        """Test that bonus points are awarded for achievements"""
        # Arrange
        user_id = "points_user"
        progress = EnhancedUserProgress(user_id=user_id, skill="Python")
        
        stats = gamification_manager.get_user_stats(user_id)
        initial_points = stats.total_points
        stats.total_lessons = 1  # Will unlock first_steps
        
        # Act
        newly_unlocked = gamification_manager.check_achievements(user_id, progress)
        
        # Assert
        assert len(newly_unlocked) > 0
        assert stats.total_points > initial_points  # Should have bonus points
    
    def test_achievement_perfectionist(self, gamification_manager):
        """Test perfectionist achievement (5 perfect scores)"""
        # Arrange
        user_id = "perfectionist_user"
        progress = EnhancedUserProgress(user_id=user_id, skill="Python")
        progress.quiz_scores = [100, 100, 100, 100, 100, 90]  # 5 perfect scores
        
        # Act
        newly_unlocked = gamification_manager.check_achievements(user_id, progress)
        
        # Assert
        achievement_ids = [a.id for a in newly_unlocked]
        assert "perfectionist" in achievement_ids
    
    def test_achievement_consistent(self, gamification_manager):
        """Test consistent achievement (7-day streak)"""
        # Arrange
        user_id = "consistent_user"
        progress = EnhancedUserProgress(user_id=user_id, skill="Python")
        
        stats = gamification_manager.get_user_stats(user_id)
        stats.streak_days = 7
        
        # Act
        newly_unlocked = gamification_manager.check_achievements(user_id, progress)
        
        # Assert
        achievement_ids = [a.id for a in newly_unlocked]
        assert "consistent" in achievement_ids

@pytest.mark.integration
class TestGamificationIntegration:
    """Integration tests for gamification with other systems"""
    
    def test_gamification_with_lesson_completion(self):
        """Test gamification integration when completing lessons"""
        # This would test the integration between the main app and gamification
        # Requires importing the enhanced app components
        pass
    
    def test_gamification_with_quiz_submission(self):
        """Test gamification integration when submitting quizzes"""
        pass

@pytest.mark.unit
class TestAchievementConditions:
    """Test specific achievement unlock conditions"""
    
    @pytest.fixture
    def sample_progress(self):
        """Create sample progress data for testing"""        
        return EnhancedUserProgress(
            user_id="test_user",
            skill="Python Programming",
            lessons_completed=0,
            quiz_scores=[],
            time_spent=[],
            mastery_level=0.0
        )
    
    def test_scholar_achievement_condition(self, gamification_manager, enhanced_user_progress):
        """Test scholar achievement (10 lessons)"""
        # Arrange
        stats = gamification_manager.get_user_stats("test_user")
        stats.total_lessons = 10
        
        # Act
        newly_unlocked = gamification_manager.check_achievements("test_user", enhanced_user_progress)
        
        # Assert
        achievement_ids = [a.id for a in newly_unlocked]
        assert "scholar" in achievement_ids
    
    def test_expert_achievement_condition(self, gamification_manager, enhanced_user_progress):
        """Test expert achievement (20 lessons)"""
        # Arrange
        stats = gamification_manager.get_user_stats("test_user")
        stats.total_lessons = 20
        
        # Act
        newly_unlocked = gamification_manager.check_achievements("test_user", enhanced_user_progress)
        
        # Assert
        achievement_ids = [a.id for a in newly_unlocked]
        assert "expert" in achievement_ids
        assert "scholar" in achievement_ids  # Should also unlock scholar
        assert "persistent" in achievement_ids  # Should also unlock persistent
