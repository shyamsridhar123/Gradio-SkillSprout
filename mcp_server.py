"""
MCP Server Integration for SkillSprout
This module provides Model Context Protocol endpoints for external agent integration.
"""

import json
import asyncio
from typing import Dict, Any, List
from dataclasses import asdict
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import uvicorn

# Import from main app
from app import AgenticSkillBuilder, UserProgress

# FastAPI app for MCP endpoints
mcp_app = FastAPI(
    title="SkillSprout MCP Server",
    description="Model Context Protocol endpoints for microlearning integration",
    version="1.0.0"
)

# Global app instance
skill_builder = AgenticSkillBuilder()

# Pydantic models for API
class LessonRequest(BaseModel):
    skill: str
    user_id: str = "default_user"
    difficulty: str = "beginner"

class QuizSubmission(BaseModel):
    user_id: str
    skill: str
    lesson_title: str
    answers: List[str]

class ProgressResponse(BaseModel):
    user_id: str
    skill: str
    lessons_completed: int
    average_score: float
    current_difficulty: str
    recommendations: str

@mcp_app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "SkillSprout MCP Server",
        "version": "1.0.0",
        "description": "MCP endpoints for AI-powered microlearning",
        "endpoints": {
            "GET /lesson/{skill}": "Fetch next lesson for a skill",
            "GET /progress/{user_id}": "Get user progress data",
            "POST /quiz/submit": "Submit quiz results",
            "GET /skills": "List available skills"
        }
    }

@mcp_app.get("/skills")
async def get_available_skills():
    """Get list of available predefined skills"""
    return {
        "predefined_skills": skill_builder.predefined_skills,
        "custom_skills_supported": True,
        "message": "You can also request lessons for any custom skill"
    }

@mcp_app.post("/lesson/generate")
async def generate_lesson(request: LessonRequest):
    """Generate a new lesson for the specified skill and user"""
    try:
        # Set current user
        skill_builder.current_user = request.user_id
        
        # Get user progress
        progress = skill_builder.progress_agent.get_user_progress(
            request.user_id, request.skill
        )
        
        # Generate lesson
        lesson = await skill_builder.lesson_agent.generate_lesson(
            skill=request.skill,
            difficulty=request.difficulty or progress.current_difficulty,
            previous_lessons=[]  # Could be enhanced to track previous lessons
        )
        
        return {
            "lesson": {
                "title": lesson.title,
                "content": lesson.content,
                "skill": lesson.skill,
                "difficulty": lesson.difficulty,
                "duration_minutes": lesson.duration_minutes,
                "key_concepts": lesson.key_concepts
            },
            "user_context": {
                "user_id": request.user_id,
                "current_difficulty": progress.current_difficulty,
                "lessons_completed": progress.lessons_completed
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating lesson: {str(e)}")

@mcp_app.get("/progress/{user_id}")
async def get_user_progress(user_id: str, skill: str = None):
    """Get user progress data for all skills or a specific skill"""
    try:
        if skill:
            # Get progress for specific skill
            progress = skill_builder.progress_agent.get_user_progress(user_id, skill)
            recommendation = skill_builder.progress_agent.get_recommendation(progress)
            
            return ProgressResponse(
                user_id=progress.user_id,
                skill=progress.skill,
                lessons_completed=progress.lessons_completed,
                average_score=progress.get_average_score(),
                current_difficulty=progress.current_difficulty,
                recommendations=recommendation
            )
        else:
            # Get progress for all skills
            user_progress_data = {}
            for key, progress in skill_builder.progress_agent.user_data.items():
                if progress.user_id == user_id:
                    user_progress_data[progress.skill] = {
                        "lessons_completed": progress.lessons_completed,
                        "average_score": progress.get_average_score(),
                        "current_difficulty": progress.current_difficulty,
                        "quiz_scores": progress.quiz_scores,
                        "last_activity": progress.last_activity
                    }
            
            return {
                "user_id": user_id,
                "skills_progress": user_progress_data,
                "total_skills_learning": len(user_progress_data),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching progress: {str(e)}")

@mcp_app.post("/quiz/submit")
async def submit_quiz_results(submission: QuizSubmission):
    """Submit quiz results and get feedback"""
    try:
        # Set current user
        skill_builder.current_user = submission.user_id
        
        # Calculate score (simplified scoring)
        if not skill_builder.current_quiz or len(submission.answers) == 0:
            raise HTTPException(status_code=400, detail="No active quiz or no answers provided")
        
        correct_answers = 0
        total_questions = len(skill_builder.current_quiz.questions)
        
        for i, (question, answer) in enumerate(zip(skill_builder.current_quiz.questions, submission.answers)):
            if i >= len(submission.answers):
                break
                
            correct_answer = str(question['correct_answer']).lower()
            user_answer = answer.lower().strip()
            
            if user_answer == correct_answer:
                correct_answers += 1
        
        score = correct_answers / total_questions if total_questions > 0 else 0
        
        # Update progress
        progress = skill_builder.progress_agent.update_progress(
            submission.user_id, submission.skill, quiz_score=score
        )
        
        # Get recommendation
        recommendation = skill_builder.progress_agent.get_recommendation(progress)
        
        return {
            "quiz_results": {
                "score": score,
                "correct_answers": correct_answers,
                "total_questions": total_questions,
                "percentage": f"{score:.1%}"
            },
            "updated_progress": {
                "lessons_completed": progress.lessons_completed,
                "average_score": progress.get_average_score(),
                "current_difficulty": progress.current_difficulty
            },
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing quiz submission: {str(e)}")

@mcp_app.post("/quiz/generate")
async def generate_quiz_for_lesson(lesson_title: str, skill: str, user_id: str = "default_user"):
    """Generate a quiz for a specific lesson"""
    try:
        # Set current user
        skill_builder.current_user = user_id
        
        # Get user progress
        progress = skill_builder.progress_agent.get_user_progress(user_id, skill)
        
        # Create a mock lesson object for quiz generation
        from app import Lesson
        mock_lesson = Lesson(
            title=lesson_title,
            content=f"This is content for {lesson_title}",
            skill=skill,
            difficulty=progress.current_difficulty,
            duration_minutes=5,
            key_concepts=["concept1", "concept2"]
        )
        
        # Generate quiz
        quiz = await skill_builder.quiz_agent.generate_quiz(mock_lesson, progress)
        
        # Store current quiz for submission
        skill_builder.current_quiz = quiz
        
        return {
            "quiz": {
                "lesson_title": lesson_title,
                "skill": skill,
                "difficulty": quiz.difficulty,
                "questions": quiz.questions
            },
            "instructions": "Submit answers using the /quiz/submit endpoint",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")

@mcp_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "SkillSprout MCP Server"
    }

def run_mcp_server():
    """Run the MCP server"""
    uvicorn.run(
        "mcp_server:mcp_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    print("🚀 Starting SkillSprout MCP Server...")
    print("📚 MCP endpoints will be available at http://localhost:8000")
    print("📖 API documentation at http://localhost:8000/docs")
    run_mcp_server()
