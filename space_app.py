"""
SkillSprout - Hackathon Submission
A unified app.py that serves both Gradio interface and MCP server endpoints
for the Gradio Agents & MCP Hackathon 2025
"""

import os
import json
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
import logging
import math
import base64
from io import BytesIO

from dotenv import load_dotenv
import gradio as gr
from openai import AzureOpenAI
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Voice narration imports
try:
    import azure.cognitiveservices.speech as speechsdk
    SPEECH_SDK_AVAILABLE = True
except ImportError:
    SPEECH_SDK_AVAILABLE = False
    print("⚠️ Azure Speech SDK not available. Voice narration will be disabled.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables (works locally with .env, in Spaces with secrets)
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

# Voice configuration
VOICE_KEY = os.getenv("AZURE_SPEECH_KEY", "").replace('"', '')
VOICE_REGION = os.getenv("AZURE_SPEECH_REGION", "eastus2").replace('"', '')
VOICE_NAME = os.getenv("AZURE_SPEECH_VOICE", "en-US-AvaMultilingualNeural").replace('"', '')

# Import all classes from the main app
from app import (
    UserProgress, Lesson, Quiz, LessonAgent, QuizAgent, 
    ProgressAgent, AgenticSkillBuilder
)

# Gamification System Classes
@dataclass
class Achievement:
    """Achievement system for gamification"""
    id: str
    name: str
    description: str
    icon: str
    unlocked: bool = False
    unlock_condition: str = ""

@dataclass
class UserStats:
    """Enhanced user statistics for gamification"""
    user_id: str
    total_points: int = 0
    level: int = 1
    achievements: List[str] = field(default_factory=list)
    streak_days: int = 0
    total_lessons: int = 0
    total_quizzes: int = 0
    correct_answers: int = 0
    
    def add_points(self, points: int):
        """Add points and check for level up"""
        self.total_points += points
        new_level = min(10, (self.total_points // 100) + 1)
        if new_level > self.level:
            self.level = new_level
    
    def get_accuracy(self) -> float:
        """Calculate quiz accuracy"""
        if self.total_quizzes == 0:
            return 0.0
        return (self.correct_answers / self.total_quizzes) * 100

@dataclass 
class EnhancedUserProgress:
    """Enhanced progress tracking with detailed analytics"""
    user_id: str
    skill: str
    lessons_completed: int = 0
    quiz_scores: List[float] = field(default_factory=list)
    time_spent: List[float] = field(default_factory=list)
    mastery_level: float = 0.0
    last_activity: datetime = field(default_factory=datetime.now)
    
    def calculate_mastery(self) -> float:
        """Calculate skill mastery based on performance"""
        if not self.quiz_scores:
            return 0.0
        
        avg_score = sum(self.quiz_scores) / len(self.quiz_scores)
        consistency_bonus = min(len(self.quiz_scores) * 5, 20)  # Max 20% bonus
        lesson_bonus = min(self.lessons_completed * 2, 10)  # Max 10% bonus
        
        self.mastery_level = min(100, avg_score + consistency_bonus + lesson_bonus)
        return self.mastery_level
    
    def update_mastery(self):
        """Update mastery level"""
        self.calculate_mastery()

class GamificationManager:
    """Manages achievements and gamification"""
    
    def __init__(self):
        self.user_stats: Dict[str, UserStats] = {}
        self.achievements = {
            "first_steps": Achievement("first_steps", "First Steps", "Complete your first lesson", "🎯"),
            "quiz_master": Achievement("quiz_master", "Quiz Master", "Score 100% on a quiz", "🧠"),
            "persistent": Achievement("persistent", "Persistent Learner", "Complete 5 lessons", "💪"),
            "scholar": Achievement("scholar", "Scholar", "Complete 10 lessons", "🎓"),
            "expert": Achievement("expert", "Domain Expert", "Master a skill (20 lessons)", "⭐"),
            "polyglot": Achievement("polyglot", "Polyglot", "Learn 3 different skills", "🌍"),
            "perfectionist": Achievement("perfectionist", "Perfectionist", "Score 100% on 5 quizzes", "💯"),
            "speed": Achievement("speed", "Speed Learner", "Complete lesson in under 3 minutes", "⚡"),
            "consistent": Achievement("consistent", "Consistent", "Learn for 7 days in a row", "📅"),
            "explorer": Achievement("explorer", "Explorer", "Try voice narration feature", "🎧"),
        }
    
    def get_user_stats(self, user_id: str) -> UserStats:
        """Get or create user stats"""
        if user_id not in self.user_stats:
            self.user_stats[user_id] = UserStats(user_id=user_id)
        return self.user_stats[user_id]
    
    def check_achievements(self, user_id: str, progress: EnhancedUserProgress) -> List[Achievement]:
        """Check and unlock achievements"""
        stats = self.get_user_stats(user_id)
        newly_unlocked = []
        
        # Check each achievement
        achievements_to_check = [
            ("first_steps", stats.total_lessons >= 1),
            ("quiz_master", any(score == 100 for score in progress.quiz_scores)),
            ("persistent", stats.total_lessons >= 5),
            ("scholar", stats.total_lessons >= 10),
            ("expert", stats.total_lessons >= 20),
            ("perfectionist", sum(1 for score in progress.quiz_scores if score == 100) >= 5),
            ("consistent", stats.streak_days >= 7),
        ]
        
        for achievement_id, condition in achievements_to_check:
            if condition and achievement_id not in stats.achievements:
                stats.achievements.append(achievement_id)
                newly_unlocked.append(self.achievements[achievement_id])
                stats.add_points(50)  # Bonus points for achievements
        
        return newly_unlocked

# Create global instances
app_instance = AgenticSkillBuilder()
gamification = GamificationManager()

def generate_voice_narration(text: str, voice_name: str = VOICE_NAME) -> Optional[str]:
    """Generate voice narration using Azure Speech Services"""
    if not SPEECH_SDK_AVAILABLE or not VOICE_KEY:
        logger.warning("Voice narration not available - missing Speech SDK or API key")
        return None
    
    try:
        # Configure speech service
        speech_config = speechsdk.SpeechConfig(subscription=VOICE_KEY, region=VOICE_REGION)
        speech_config.speech_synthesis_voice_name = voice_name
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"narration_{timestamp}.wav"
        
        # Configure audio output
        audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_filename)
        
        # Create synthesizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # Create SSML for educational content
        ssml_text = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice_name}">
                <prosody rate="0.9" pitch="medium">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        # Synthesize speech
        result = speech_synthesizer.speak_ssml_async(ssml_text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.info(f"Voice narration generated: {audio_filename}")
            return audio_filename
        else:
            logger.error(f"Speech synthesis failed: {result.reason}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating voice narration: {e}")
        return None

# ===== MCP SERVER INTEGRATION =====

# FastAPI app for MCP endpoints
mcp_app = FastAPI(
    title="SkillSprout MCP Server",
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
        "name": "SkillSprout MCP Server",
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
                "lessons_completed": progress.lessons_completed            },
            "mcp_server": "SkillSprout",
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
                "average_score": progress.get_average_score(),                "current_difficulty": progress.current_difficulty,
                "recommendations": recommendation,
                "mcp_server": "SkillSprout"
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
                "skills_progress": user_progress_data,                "total_skills_learning": len(user_progress_data),
                "mcp_server": "SkillSprout",
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
                "current_difficulty": progress.current_difficulty            },
            "recommendation": recommendation,
            "mcp_server": "SkillSprout",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing quiz submission: {str(e)}")

# ===== GRADIO INTERFACE =====

def create_interface():
    """Create the Gradio interface with enhanced hackathon features"""
    
    with gr.Blocks(
        title="SkillSprout - MCP Hackathon 2025",
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
            <h1>🌱 SkillSprout</h1>
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
            
            # Voice narration controls
            with gr.Row(visible=False) as voice_controls:
                voice_btn = gr.Button("🎧 Generate Voice Narration", variant="secondary")
                voice_audio = gr.Audio(label="Lesson Audio", visible=False)
            
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
          # Event handlers with gamification integration
        def handle_start_learning(skill_choice, custom_skill_input, user_id="default"):
            """Enhanced learning session handler with gamification"""
            skill = custom_skill_input.strip() if custom_skill_input.strip() else skill_choice
            if not skill:                return [
                    gr.update(value="⚠️ Please select or enter a skill to continue."),
                    gr.update(visible=False),  # voice_controls
                    gr.update(visible=False),
                    gr.update(visible=False),
                    skill
                ] + [gr.update(visible=False, value="") for _ in range(5)]
            
            try:
                # Start lesson using the app instance (sync call)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                lesson_content, btn_text, _ = loop.run_until_complete(app_instance.start_lesson(skill))
                app_instance.current_user = user_id
                
                # Update user stats
                stats = gamification.get_user_stats(user_id)
                stats.total_lessons += 1
                stats.add_points(10)  # Points for starting lesson
                
                # Check for achievements
                progress = EnhancedUserProgress(user_id=user_id, skill=skill)
                progress.lessons_completed = stats.total_lessons
                newly_unlocked = gamification.check_achievements(user_id, progress)
                return [
                    gr.update(value=lesson_content),
                    gr.update(visible=True),  # voice_controls
                    gr.update(value=btn_text, visible=True),
                    gr.update(visible=False),
                    skill
                ] + [gr.update(visible=False, value="") for _ in range(5)]
                
            except Exception as e:
                logger.error(f"Error starting lesson: {e}")                
                return [
                    gr.update(value=f"❌ Error starting lesson: {str(e)}"),
                    gr.update(visible=False),  # voice_controls
                    gr.update(visible=False),
                    gr.update(visible=False),
                    skill
                ] + [gr.update(visible=False, value="") for _ in range(5)]

        def handle_complete_lesson(user_id="default"):
            """Handle lesson completion and start quiz with gamification"""
            try:
                # Complete lesson and generate quiz (sync call)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                quiz_content, btn_text, _ = loop.run_until_complete(app_instance.complete_lesson_and_start_quiz())
                
                # Update user stats - lesson completed
                stats = gamification.get_user_stats(user_id)
                stats.add_points(20)  # Points for completing lesson
                
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
            except Exception as e:
                logger.error(f"Error completing lesson: {e}")
                return [
                    gr.update(visible=False),
                    gr.update(value=f"❌ Error completing lesson: {str(e)}", visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False)
                ] + [gr.update(visible=False) for _ in range(len(quiz_inputs))]

        def handle_submit_quiz(*answers, user_id="default"):
            """Handle quiz submission with gamification"""
            try:
                valid_answers = [ans for ans in answers if ans is not None and ans != ""]
                results_content, btn_text, _ = app_instance.submit_quiz(*valid_answers)
                
                # Update user stats for quiz completion
                stats = gamification.get_user_stats(user_id)
                stats.total_quizzes += 1
                
                # Calculate quiz score and update stats
                if app_instance.current_quiz and app_instance.current_quiz.questions:
                    total_questions = len(app_instance.current_quiz.questions)
                    # Simple scoring: assume each correct answer is worth points
                    score_points = len(valid_answers) * 20  # Base points per answer
                    stats.add_points(score_points)
                    
                    # Check if perfect score (simplified check)
                    if "100%" in results_content or "Perfect" in results_content:
                        stats.correct_answers += total_questions
                        stats.add_points(50)  # Bonus for perfect score
                    else:
                        # Estimate correct answers based on content (simplified)
                        stats.correct_answers += max(1, len(valid_answers) // 2)
                
                return [
                    gr.update(visible=False),
                    gr.update(value=results_content, visible=True),
                    gr.update(value=btn_text, visible=True),
                    gr.update(visible=False)
                ] + [gr.update(visible=False) for _ in range(len(quiz_inputs))]
                
            except Exception as e:
                logger.error(f"Error submitting quiz: {e}")
                return [
                    gr.update(visible=False),
                    gr.update(value=f"❌ Error submitting quiz: {str(e)}", visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False)
                ] + [gr.update(visible=False) for _ in range(len(quiz_inputs))]
        def handle_restart():
            return [
                gr.update(visible=False),
                gr.update(visible=False),  # voice_controls
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
        
        def handle_voice_generation(lesson_content, user_id="default"):
            """Generate voice narration for lesson content"""
            if not lesson_content or lesson_content == "":
                return gr.update(value=None, visible=False), "❌ No lesson content to narrate"
            
            try:
                # Extract text content from markdown
                import re
                # Remove markdown formatting for better speech
                text_content = re.sub(r'[#*`]', '', lesson_content)
                text_content = text_content.replace('\n', ' ').strip()
                
                # Limit text length for better narration
                if len(text_content) > 1000:
                    text_content = text_content[:1000] + "..."
                
                # Generate voice narration
                audio_file = generate_voice_narration(text_content)
                
                if audio_file:
                    # Award achievement for using voice feature
                    stats = gamification.get_user_stats(user_id)
                    if "explorer" not in stats.achievements:
                        stats.achievements.append("explorer")
                        stats.add_points(25)
                    
                    return gr.update(value=audio_file, visible=True), "🎧 Voice narration generated!"
                else:
                    return gr.update(value=None, visible=False), "❌ Voice narration not available"
                    
            except Exception as e:
                logger.error(f"Error generating voice: {e}")
                return gr.update(value=None, visible=False), f"❌ Error: {str(e)}"
        
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
                            "lessons_completed": progress.lessons_completed                        },
                        "mcp_server": "SkillSprout",
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
            outputs=[lesson_output, voice_controls, lesson_btn, quiz_output, current_skill] + quiz_inputs[:5]
        )
        
        voice_btn.click(
            handle_voice_generation,
            inputs=[lesson_output],
            outputs=[voice_audio, lesson_output]
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
            outputs=[lesson_output, voice_controls, quiz_output, results_output, lesson_btn, restart_btn, current_skill] + quiz_inputs
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
    """Main function to launch the Gradio interface."""
    try:
        demo = create_interface()
        
        # For Hugging Face Spaces, we need specific launch parameters
        demo.launch(
            server_name="0.0.0.0",  # Allow external connections
            server_port=7860,       # HF Spaces default port
            share=True,            # Don't create public link on HF Spaces
            show_error=True,        # Show errors in the UI
            debug=True             # Disable debug mode in production
        )
    except Exception as e:
        print(f"Error launching app: {e}")
        # Fallback launch configuration
        demo.launch()

if __name__ == "__main__":
    main()
