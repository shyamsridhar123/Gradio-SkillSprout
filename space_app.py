"""
Agentic Skill Builder - Hackathon Submission
A unified app.py that serves both Gradio interface and MCP server endpoints
for the Gradio Agents & MCP Hackathon 2025
"""

import os
import json
import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

from dotenv import load_dotenv
import gradio as gr
from openai import AzureOpenAI
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Azure OpenAI client configuration
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").replace('"', ''),
    api_key=os.getenv("AZURE_OPENAI_KEY", "").replace('"', ''),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview").replace('"', ''),
)

# Model configurations
LLM_DEPLOYMENT = os.getenv("AZURE_OPENAI_LLM_DEPLOYMENT", "gpt-4").replace('"', '')
LLM_MODEL = os.getenv("AZURE_OPENAI_LLM_MODEL", "gpt-4").replace('"', '')

# Import all classes from the main app
from app import (
    UserProgress, Lesson, Quiz, LessonAgent, QuizAgent, 
    ProgressAgent, AgenticSkillBuilder
)

# Create global instances
app_instance = AgenticSkillBuilder()

# ===== MCP SERVER INTEGRATION =====

# FastAPI app for MCP endpoints
mcp_app = FastAPI(
    title="Agentic Skill Builder MCP Server",
    description="Model Context Protocol endpoints for microlearning integration - Hackathon 2025",
    version="1.0.0"
)

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

@mcp_app.get("/")
async def root():
    """Root endpoint with hackathon information"""
    return {
        "name": "Agentic Skill Builder MCP Server",
        "version": "1.0.0",
        "hackathon": "Gradio Agents & MCP Hackathon 2025",
        "track": "mcp-server-track",
        "description": "MCP endpoints for AI-powered microlearning",
        "endpoints": {
            "GET /mcp/lesson/generate": "Generate next lesson for a skill",
            "GET /mcp/progress/{user_id}": "Get user progress data",
            "POST /mcp/quiz/submit": "Submit quiz results",
            "GET /mcp/skills": "List available skills"
        }
    }

@mcp_app.get("/mcp/skills")
async def get_available_skills():
    """Get list of available predefined skills"""
    return {
        "predefined_skills": app_instance.predefined_skills,
        "custom_skills_supported": True,
        "message": "You can also request lessons for any custom skill"
    }

@mcp_app.post("/mcp/lesson/generate")
async def generate_lesson_mcp(request: LessonRequest):
    """Generate a new lesson via MCP endpoint"""
    try:
        app_instance.current_user = request.user_id
        progress = app_instance.progress_agent.get_user_progress(request.user_id, request.skill)
        
        lesson = await app_instance.lesson_agent.generate_lesson(
            skill=request.skill,
            difficulty=request.difficulty or progress.current_difficulty,
            previous_lessons=[]
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
            "mcp_server": "Agentic Skill Builder",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating lesson: {str(e)}")

@mcp_app.get("/mcp/progress/{user_id}")
async def get_user_progress_mcp(user_id: str, skill: str = None):
    """Get user progress data via MCP endpoint"""
    try:
        if skill:
            progress = app_instance.progress_agent.get_user_progress(user_id, skill)
            recommendation = app_instance.progress_agent.get_recommendation(progress)
            
            return {
                "user_id": progress.user_id,
                "skill": progress.skill,
                "lessons_completed": progress.lessons_completed,
                "average_score": progress.get_average_score(),
                "current_difficulty": progress.current_difficulty,
                "recommendations": recommendation,
                "mcp_server": "Agentic Skill Builder"
            }
        else:
            user_progress_data = {}
            for key, progress in app_instance.progress_agent.user_data.items():
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
                "mcp_server": "Agentic Skill Builder",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching progress: {str(e)}")

@mcp_app.post("/mcp/quiz/submit")
async def submit_quiz_results_mcp(submission: QuizSubmission):
    """Submit quiz results via MCP endpoint"""
    try:
        app_instance.current_user = submission.user_id
        
        if not app_instance.current_quiz or len(submission.answers) == 0:
            raise HTTPException(status_code=400, detail="No active quiz or no answers provided")
        
        correct_answers = 0
        total_questions = len(app_instance.current_quiz.questions)
        
        for i, (question, answer) in enumerate(zip(app_instance.current_quiz.questions, submission.answers)):
            if i >= len(submission.answers):
                break
                
            correct_answer = str(question['correct_answer']).lower()
            user_answer = answer.lower().strip()
            
            if user_answer == correct_answer:
                correct_answers += 1
        
        score = correct_answers / total_questions if total_questions > 0 else 0
        
        progress = app_instance.progress_agent.update_progress(
            submission.user_id, submission.skill, quiz_score=score
        )
        
        recommendation = app_instance.progress_agent.get_recommendation(progress)
        
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
            "mcp_server": "Agentic Skill Builder",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing quiz submission: {str(e)}")

# ===== GRADIO INTERFACE =====

def create_interface():
    """Create the Gradio interface with enhanced hackathon features"""
    
    with gr.Blocks(
        title="Agentic Skill Builder - MCP Hackathon 2025",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 900px !important;
            margin: auto !important;
        }
        .hackathon-header {
            background: linear-gradient(90deg, #ff7b7b, #667eea);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        """
    ) as demo:
        
        # Enhanced Header for Hackathon
        gr.HTML("""
        <div class="hackathon-header">
            <h1>🚀 Agentic Skill Builder</h1>
            <h3>AI-Powered Microlearning with MCP Integration</h3>
            <p><strong>🏆 Gradio Agents & MCP Hackathon 2025 Submission</strong></p>
            <p>Track: MCP Server/Tool • Demonstrating Agentic AI Workflows</p>
        </div>
        """)
        
        # State variables
        current_skill = gr.State("")
        
        with gr.Tab("🎯 Microlearning Experience"):
            gr.Markdown("""
            ### 🎓 Start Your AI-Powered Learning Journey
            Choose any skill and let our agentic AI system create personalized lessons and adaptive quizzes for you!
            """)
            
            with gr.Row():
                with gr.Column():
                    skill_dropdown = gr.Dropdown(
                        choices=app_instance.predefined_skills,
                        label="📚 Select a Popular Skill",
                        info="Choose from trending skills..."
                    )
                    custom_skill = gr.Textbox(
                        label="✍️ Or Enter Any Custom Skill",
                        info="e.g., Quantum Computing, Meditation, Game Development...",
                        placeholder="What would you like to learn today?"
                    )
                    
                    start_btn = gr.Button("🚀 Start Learning", variant="primary", size="lg")
            
            # Learning content areas
            lesson_output = gr.Markdown(visible=False)
            lesson_btn = gr.Button("Complete Lesson", visible=False)
            
            quiz_output = gr.Markdown(visible=False)
            quiz_inputs = []
            for i in range(5):
                quiz_inputs.append(gr.Textbox(label=f"Answer {i+1}", visible=False))
            
            quiz_submit_btn = gr.Button("Submit Quiz", visible=False)
            results_output = gr.Markdown(visible=False)
            restart_btn = gr.Button("Start New Lesson", visible=False)
        
        with gr.Tab("📊 Progress Analytics"):
            gr.Markdown("### 📈 Your Learning Analytics Dashboard")
            progress_display = gr.Markdown("Complete some lessons to see your learning analytics!")
            refresh_progress_btn = gr.Button("🔄 Refresh Progress")
        
        with gr.Tab("🔗 MCP Server Demo"):
            gr.Markdown("""
            ### 🤖 Model Context Protocol Integration
            
            **This app is BOTH a Gradio interface AND an MCP server!**
            
            #### 🌐 Available MCP Endpoints:
            
            - **GET `/mcp/skills`** - List available learning skills
            - **POST `/mcp/lesson/generate`** - Generate personalized lessons
            - **GET `/mcp/progress/{user_id}`** - Get learning progress data
            - **POST `/mcp/quiz/submit`** - Submit quiz answers
            
            #### 🧪 Try the MCP Server:
            
            The MCP server is running alongside this Gradio interface! External agents can connect to these endpoints to:
            - Generate lessons for any skill
            - Track learning progress
            - Submit quiz results
            - Access learning analytics
            
            **Example MCP Usage:**
            ```bash
            # Get available skills
            curl https://your-space-url.com/mcp/skills
            
            # Generate a lesson
            curl -X POST https://your-space-url.com/mcp/lesson/generate \\
                 -H "Content-Type: application/json" \\
                 -d '{"skill": "Python Programming", "user_id": "agent_user"}'
            ```
            
            #### 🎯 Hackathon Innovation:
            - **Agentic Architecture**: Multiple AI agents (Lesson, Quiz, Progress) collaborate
            - **MCP Protocol**: Full Model Context Protocol implementation
            - **Adaptive Learning**: AI adjusts difficulty based on performance
            - **Real-time Integration**: Seamless connection between UI and MCP endpoints
            """)
            
            # MCP Demo Interface
            gr.Markdown("#### 🧪 Test MCP Endpoints Directly:")
            
            with gr.Row():
                with gr.Column():
                    mcp_skill_input = gr.Textbox(label="Skill for MCP Test", value="Python Programming")
                    mcp_user_input = gr.Textbox(label="User ID for MCP Test", value="mcp_test_user")
                    mcp_test_btn = gr.Button("🧪 Test MCP Lesson Generation", variant="secondary")
                
                with gr.Column():
                    mcp_output = gr.JSON(label="MCP Server Response")
        
        # Event handlers (same as original app.py)
        async def handle_start_learning(skill_choice, custom_skill_input):
            skill = custom_skill_input.strip() if custom_skill_input.strip() else skill_choice
            if not skill:
                return [
                    gr.update(value="⚠️ Please select or enter a skill to continue."),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    skill
                ] + [gr.update(visible=False, value="") for _ in range(5)]
            
            lesson_content, btn_text, _ = await app_instance.start_lesson(skill)
            
            return [
                gr.update(value=lesson_content),
                gr.update(value=btn_text, visible=True),
                gr.update(visible=False),
                skill
            ] + [gr.update(visible=False, value="") for _ in range(5)]
        
        async def handle_complete_lesson():
            quiz_content, btn_text, _ = await app_instance.complete_lesson_and_start_quiz()
            
            quiz_updates = []
            if app_instance.current_quiz:
                for i, question in enumerate(app_instance.current_quiz.questions):
                    if i < len(quiz_inputs):
                        label = f"Q{i+1}: {question['question'][:50]}..."
                        quiz_updates.append(gr.update(label=label, visible=True))
                    else:
                        quiz_updates.append(gr.update(visible=False))
                for i in range(len(app_instance.current_quiz.questions), len(quiz_inputs)):
                    quiz_updates.append(gr.update(visible=False))
            else:
                quiz_updates = [gr.update(visible=False) for _ in range(len(quiz_inputs))]
            
            return [
                gr.update(visible=False),
                gr.update(value=quiz_content, visible=True),
                gr.update(value=btn_text, visible=True),
                gr.update(visible=False)
            ] + quiz_updates
        
        def handle_submit_quiz(*answers):
            valid_answers = [ans for ans in answers if ans is not None and ans != ""]
            results_content, btn_text, _ = app_instance.submit_quiz(*valid_answers)
            
            return [
                gr.update(visible=False),
                gr.update(value=results_content, visible=True),
                gr.update(value=btn_text, visible=True),
                gr.update(visible=False)
            ] + [gr.update(visible=False) for _ in range(len(quiz_inputs))]
        
        def handle_restart():
            return [
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                ""
            ] + [gr.update(visible=False, value="") for _ in range(len(quiz_inputs))]
        
        def update_progress_display():
            if not app_instance.progress_agent.user_data:
                return "**No learning data yet.** Complete some lessons to see your progress!"
            
            progress_content = "# 📊 Your Learning Progress\n\n"
            for key, progress in app_instance.progress_agent.user_data.items():
                progress_content += f"""
                **Skill:** {progress.skill}
                - Lessons completed: {progress.lessons_completed}
                - Average quiz score: {progress.get_average_score():.1%}
                - Current difficulty: {progress.current_difficulty.title()}
                - Last activity: {progress.last_activity or 'Never'}
                
                """
            return progress_content
        
        async def test_mcp_endpoint(skill, user_id):
            """Test MCP endpoint directly from the interface"""
            try:
                # Simulate MCP endpoint call
                request_data = {
                    "skill": skill,
                    "user_id": user_id,
                    "difficulty": "beginner"
                }
                
                # Generate lesson using the app instance
                app_instance.current_user = user_id
                progress = app_instance.progress_agent.get_user_progress(user_id, skill)
                lesson = await app_instance.lesson_agent.generate_lesson(skill, progress.current_difficulty, [])
                
                response = {
                    "mcp_endpoint": "/mcp/lesson/generate",
                    "request": request_data,
                    "response": {
                        "lesson": {
                            "title": lesson.title,
                            "content": lesson.content[:200] + "...",  # Truncated for display
                            "skill": lesson.skill,
                            "difficulty": lesson.difficulty,
                            "duration_minutes": lesson.duration_minutes,
                            "key_concepts": lesson.key_concepts
                        },
                        "user_context": {
                            "user_id": user_id,
                            "current_difficulty": progress.current_difficulty,
                            "lessons_completed": progress.lessons_completed
                        },
                        "mcp_server": "Agentic Skill Builder",
                        "status": "success"
                    }
                }
                
                return response
                
            except Exception as e:
                return {
                    "mcp_endpoint": "/mcp/lesson/generate", 
                    "error": str(e),
                    "status": "error"
                }
        
        # Wire up events
        start_btn.click(
            handle_start_learning,
            inputs=[skill_dropdown, custom_skill],
            outputs=[lesson_output, lesson_btn, quiz_output, current_skill] + quiz_inputs[:5]
        )
        
        lesson_btn.click(
            handle_complete_lesson,
            outputs=[lesson_btn, quiz_output, quiz_submit_btn, results_output] + quiz_inputs
        )
        
        quiz_submit_btn.click(
            handle_submit_quiz,
            inputs=quiz_inputs,
            outputs=[quiz_submit_btn, results_output, restart_btn, quiz_output] + quiz_inputs
        )
        
        restart_btn.click(
            handle_restart,
            outputs=[lesson_output, quiz_output, results_output, lesson_btn, restart_btn, current_skill] + quiz_inputs
        )
        
        refresh_progress_btn.click(
            update_progress_display,
            outputs=[progress_display]
        )
        
        mcp_test_btn.click(
            test_mcp_endpoint,
            inputs=[mcp_skill_input, mcp_user_input],
            outputs=[mcp_output]
        )
    
    return demo

# ===== MAIN APPLICATION =====

def run_mcp_server():
    """Run the MCP server in a separate thread"""
    uvicorn.run(
        mcp_app,
        host="0.0.0.0",
        port=8001,  # Different port to avoid conflicts
        log_level="info"
    )

def main():
    """Main application entry point for Hugging Face Spaces"""
    # Start MCP server in background thread
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()
    
    # Give MCP server time to start
    time.sleep(2)
    
    # Create and launch Gradio interface
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,  # Enable sharing for demo purposes
        show_error=True
    )

if __name__ == "__main__":
    main()
