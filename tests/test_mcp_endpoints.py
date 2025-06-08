"""
Tests for MCP server endpoints in SkillSprout
"""
import pytest
import requests
import json
import asyncio
import threading
import time
import subprocess
import sys
from typing import Dict, Any

@pytest.mark.integration
class TestMCPEndpoints:
    """Integration tests for MCP server endpoints"""
    
    @pytest.fixture(scope="class", autouse=True)
    def setup_test_server(self, test_server_url):
        """Start MCP server for testing"""
        # Try to connect to existing server first
        try:
            response = requests.get(test_server_url, timeout=2)
            if response.status_code == 200:
                print(f"✅ MCP server already running at {test_server_url}")
                yield
                return
        except:
            pass
        
        # Start server if not running
        print(f"🚀 Starting MCP server for testing...")
        server_process = subprocess.Popen(
            [sys.executable, "space_app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(test_server_url, timeout=1)
                if response.status_code == 200:
                    print(f"✅ MCP server started successfully")
                    break
            except:
                time.sleep(1)
        else:
            server_process.terminate()
            pytest.fail("Failed to start MCP server for testing")
        
        yield
        
        # Cleanup
        server_process.terminate()
        server_process.wait()
    
    def test_root_endpoint(self, test_server_url):
        """Test root endpoint returns server information"""
        # Act
        response = requests.get(test_server_url, timeout=10)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "SkillSprout" in data["name"]
        assert "version" in data
        assert "hackathon" in data
        assert data["track"] == "mcp-server-track"
    
    def test_get_available_skills(self, test_server_url):
        """Test getting list of available skills"""
        # Act
        response = requests.get(f"{test_server_url}/mcp/skills", timeout=10)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "predefined_skills" in data
        skills = data["predefined_skills"]
        assert isinstance(skills, list)
        assert len(skills) > 0
        assert "Python Programming" in skills
    
    def test_generate_lesson_valid_request(self, test_server_url):
        """Test lesson generation with valid request"""
        # Arrange
        lesson_data = {
            "skill": "Python Programming",
            "user_id": "test_user",
            "difficulty": "beginner"
        }
        
        # Act
        response = requests.post(
            f"{test_server_url}/mcp/lesson/generate",
            json=lesson_data,
            timeout=30
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "lesson" in data
        lesson = data["lesson"]
        assert lesson["skill"] == "Python Programming"
        assert lesson["difficulty"] == "beginner"
        assert "title" in lesson
        assert "content" in lesson
        assert "mcp_server" in data
        assert data["mcp_server"] == "SkillSprout"
    
    def test_generate_lesson_custom_skill(self, test_server_url):
        """Test lesson generation with custom skill"""
        # Arrange
        lesson_data = {
            "skill": "Custom Cooking Skill",
            "user_id": "chef_user",
            "difficulty": "intermediate"
        }
        
        # Act
        response = requests.post(
            f"{test_server_url}/mcp/lesson/generate",
            json=lesson_data,
            timeout=30
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["lesson"]["skill"] == "Custom Cooking Skill"
        assert data["lesson"]["difficulty"] == "intermediate"
    
    def test_generate_lesson_missing_skill(self, test_server_url):
        """Test lesson generation with missing skill parameter"""
        # Arrange
        lesson_data = {
            "user_id": "test_user",
            "difficulty": "beginner"
        }
        
        # Act
        response = requests.post(
            f"{test_server_url}/mcp/lesson/generate",
            json=lesson_data,
            timeout=10
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_get_user_progress_new_user(self, test_server_url):
        """Test getting progress for new user"""
        # Act
        response = requests.get(
            f"{test_server_url}/mcp/progress/new_test_user",
            timeout=10
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "new_test_user"
        assert "skills_progress" in data
        assert "total_skills_learning" in data
        assert "mcp_server" in data
        assert data["mcp_server"] == "SkillSprout"
    
    def test_get_user_progress_with_skill_filter(self, test_server_url):
        """Test getting progress filtered by skill"""
        # Act
        response = requests.get(
            f"{test_server_url}/mcp/progress/test_user?skill=Python%20Programming",
            timeout=10
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user"
    
    def test_submit_quiz_results(self, test_server_url):
        """Test submitting quiz results"""
        # Arrange
        quiz_data = {
            "user_id": "test_user",
            "skill": "Python Programming", 
            "lesson_title": "Variables and Data Types",
            "answers": ["A storage container", "True", "int"]
        }
        
        # Act
        response = requests.post(
            f"{test_server_url}/mcp/quiz/submit",
            json=quiz_data,
            timeout=15
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "feedback" in data
        assert data["user_id"] == "test_user"
        assert "mcp_server" in data
        assert data["mcp_server"] == "SkillSprout"
    
    def test_submit_quiz_empty_answers(self, test_server_url):
        """Test submitting quiz with empty answers"""
        # Arrange
        quiz_data = {
            "user_id": "test_user",
            "skill": "Data Science",
            "lesson_title": "Introduction to Data",
            "answers": []
        }
        
        # Act
        response = requests.post(
            f"{test_server_url}/mcp/quiz/submit",
            json=quiz_data,
            timeout=10
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 0
    
    def test_submit_quiz_invalid_data(self, test_server_url):
        """Test submitting quiz with invalid data"""
        # Arrange
        quiz_data = {
            "user_id": "test_user",
            # Missing required fields
        }
        
        # Act
        response = requests.post(
            f"{test_server_url}/mcp/quiz/submit",
            json=quiz_data,
            timeout=10
        )
        
        # Assert
        assert response.status_code == 422  # Validation error

@pytest.mark.integration
class TestMCPEndpointsSlow:
    """Slower integration tests that require more setup"""
    
    @pytest.mark.slow
    def test_end_to_end_learning_flow(self, test_server_url):
        """Test complete learning flow through MCP endpoints"""
        user_id = "e2e_test_user"
        skill = "JavaScript"
        
        # Step 1: Get available skills
        response = requests.get(f"{test_server_url}/mcp/skills")
        assert response.status_code == 200
        
        # Step 2: Generate a lesson
        lesson_data = {
            "skill": skill,
            "user_id": user_id,
            "difficulty": "beginner"
        }
        response = requests.post(
            f"{test_server_url}/mcp/lesson/generate",
            json=lesson_data,
            timeout=30
        )
        assert response.status_code == 200
        lesson_response = response.json()
        lesson_title = lesson_response["lesson"]["title"]
        
        # Step 3: Submit quiz results
        quiz_data = {
            "user_id": user_id,
            "skill": skill,
            "lesson_title": lesson_title,
            "answers": ["answer1", "answer2"]
        }
        response = requests.post(
            f"{test_server_url}/mcp/quiz/submit",
            json=quiz_data,
            timeout=15
        )
        assert response.status_code == 200
        
        # Step 4: Check progress
        response = requests.get(f"{test_server_url}/mcp/progress/{user_id}")
        assert response.status_code == 200
        progress_data = response.json()
        assert skill in progress_data["skills_progress"]
    
    @pytest.mark.slow
    def test_multiple_concurrent_requests(self, test_server_url):
        """Test server handling multiple concurrent requests"""
        import concurrent.futures
        
        def make_request(user_id):
            """Make a lesson generation request"""
            lesson_data = {
                "skill": "Python Programming",
                "user_id": f"concurrent_user_{user_id}",
                "difficulty": "beginner"
            }
            response = requests.post(
                f"{test_server_url}/mcp/lesson/generate",
                json=lesson_data,
                timeout=30
            )
            return response.status_code == 200
        
        # Act - Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Assert - All requests should succeed
        assert all(results)

@pytest.mark.unit
class TestMCPErrorHandling:
    """Unit tests for MCP error handling scenarios"""
    
    def test_invalid_endpoint(self, test_server_url):
        """Test accessing invalid endpoint"""
        try:
            response = requests.get(f"{test_server_url}/invalid/endpoint", timeout=5)
            assert response.status_code == 404
        except requests.exceptions.ConnectionError:
            pytest.skip("MCP server not running")
    
    def test_malformed_json_request(self, test_server_url):
        """Test sending malformed JSON"""
        try:
            response = requests.post(
                f"{test_server_url}/mcp/lesson/generate",
                data="invalid json",
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            assert response.status_code in [400, 422]
        except requests.exceptions.ConnectionError:
            pytest.skip("MCP server not running")

class TestMCPHelpers:
    """Helper functions for MCP testing"""
    
    @staticmethod
    def is_server_running(url: str) -> bool:
        """Check if MCP server is running"""
        try:
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def wait_for_server(url: str, timeout: int = 30) -> bool:
        """Wait for server to become available"""
        for _ in range(timeout):
            if TestMCPHelpers.is_server_running(url):
                return True
            time.sleep(1)
        return False
