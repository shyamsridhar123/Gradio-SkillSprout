import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

from dotenv import load_dotenv
import gradio as gr
from openai import AzureOpenAI
import pandas as pd

# Load environment variables for local development
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure OpenAI client configuration
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").replace('"', ''),
    api_key=os.getenv("AZURE_OPENAI_KEY", "").replace('"', ''),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview").replace('"', ''),
)

# Model configurations
LLM_DEPLOYMENT = os.getenv("AZURE_OPENAI_LLM_DEPLOYMENT", "gpt-4.1").replace('"', '')
LLM_MODEL = os.getenv("AZURE_OPENAI_LLM_MODEL", "gpt-4.1").replace('"', '')

@dataclass
class UserProgress:
    """Data class to track user learning progress"""
    user_id: str
    skill: str
    lessons_completed: int = 0
    quiz_scores: List[float] = None
    current_difficulty: str = "beginner"
    streak_days: int = 0
    total_time_spent: int = 0  # minutes
    last_activity: str = ""
    
    def __post_init__(self):
        if self.quiz_scores is None:
            self.quiz_scores = []
    
    def get_average_score(self) -> float:
        """Calculate average quiz score"""
        return sum(self.quiz_scores) / len(self.quiz_scores) if self.quiz_scores else 0.0
    
    def add_quiz_score(self, score: float):
        """Add a new quiz score and update difficulty if needed"""
        self.quiz_scores.append(score)
        # Adaptive difficulty adjustment
        avg_score = self.get_average_score()
        if avg_score >= 0.8 and len(self.quiz_scores) >= 3:
            if self.current_difficulty == "beginner":
                self.current_difficulty = "intermediate"
            elif self.current_difficulty == "intermediate":
                self.current_difficulty = "advanced"
        elif avg_score < 0.6 and len(self.quiz_scores) >= 3:
            if self.current_difficulty == "advanced":
                self.current_difficulty = "intermediate"
            elif self.current_difficulty == "intermediate":
                self.current_difficulty = "beginner"

@dataclass
class Lesson:
    """Data class for lesson content"""
    title: str
    content: str
    skill: str
    difficulty: str
    duration_minutes: int
    key_concepts: List[str]

@dataclass
class Quiz:
    """Data class for quiz content"""
    questions: List[Dict]
    skill: str
    difficulty: str
    lesson_title: str

class LessonAgent:
    """Agent responsible for generating personalized micro-lessons"""
    
    def __init__(self, client: AzureOpenAI):
        self.client = client
        self.model = LLM_DEPLOYMENT
    
    async def generate_lesson(self, skill: str, difficulty: str = "beginner", 
                            previous_lessons: List[str] = None) -> Lesson:
        """Generate a personalized micro-lesson"""
        try:
            previous_context = ""
            if previous_lessons:
                previous_context = f"\nPrevious lessons covered: {', '.join(previous_lessons[-3:])}"
            
            prompt = f"""
            Create a concise, engaging micro-lesson for the skill: {skill}
            Difficulty level: {difficulty}
            {previous_context}
            
            Requirements:
            - Lesson should be 3-5 minutes to read
            - Include practical examples
            - Focus on one key concept
            - Make it actionable
            - Include 3-5 key takeaways
            
            Format your response as JSON with these fields:
            {{
                "title": "Lesson title",
                "content": "Main lesson content (200-400 words)",
                "duration_minutes": 4,
                "key_concepts": ["concept1", "concept2", "concept3"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educator creating micro-lessons. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            lesson_data = json.loads(response.choices[0].message.content)
            
            return Lesson(
                title=lesson_data["title"],
                content=lesson_data["content"],
                skill=skill,
                difficulty=difficulty,
                duration_minutes=lesson_data["duration_minutes"],
                key_concepts=lesson_data["key_concepts"]
            )
            
        except Exception as e:
            logger.error(f"Error generating lesson: {e}")
            # Fallback lesson
            return Lesson(
                title=f"Introduction to {skill}",
                content=f"Let's start learning about {skill}. This is a fundamental skill that can help you grow professionally and personally.",
                skill=skill,
                difficulty=difficulty,
                duration_minutes=3,
                key_concepts=["basics", "fundamentals", "getting started"]
            )

class QuizAgent:
    """Agent responsible for generating adaptive quizzes"""
    
    def __init__(self, client: AzureOpenAI):
        self.client = client
        self.model = LLM_DEPLOYMENT
    
    async def generate_quiz(self, lesson: Lesson, user_progress: UserProgress) -> Quiz:
        """Generate an adaptive quiz based on the lesson content"""
        try:
            avg_score = user_progress.get_average_score()
            
            prompt = f"""
            Create a quiz for this lesson:
            Title: {lesson.title}
            Content: {lesson.content}
            Key concepts: {', '.join(lesson.key_concepts)}
            
            User's average score: {avg_score:.1f}
            Current difficulty: {lesson.difficulty}
            
            Create 3-5 questions that test understanding of the lesson.
            Mix question types: multiple choice, true/false, and short answer.
            
            Format as JSON:
            {{
                "questions": [
                    {{
                        "type": "multiple_choice",
                        "question": "Question text?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "A",
                        "explanation": "Why this is correct"
                    }},
                    {{
                        "type": "true_false",
                        "question": "Statement to evaluate",
                        "correct_answer": true,
                        "explanation": "Explanation"
                    }}
                ]
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a quiz expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1200
            )
            
            quiz_data = json.loads(response.choices[0].message.content)
            
            return Quiz(
                questions=quiz_data["questions"],
                skill=lesson.skill,
                difficulty=lesson.difficulty,
                lesson_title=lesson.title
            )
            
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            # Fallback quiz
            return Quiz(
                questions=[{
                    "type": "multiple_choice",
                    "question": f"What is the main topic of this lesson about {lesson.skill}?",
                    "options": [lesson.skill, "Something else", "Not sure", "All of the above"],
                    "correct_answer": lesson.skill,
                    "explanation": f"This lesson focuses on {lesson.skill}"
                }],
                skill=lesson.skill,
                difficulty=lesson.difficulty,
                lesson_title=lesson.title
            )

class ProgressAgent:
    """Agent responsible for tracking progress and making recommendations"""
    
    def __init__(self):
        self.user_data: Dict[str, UserProgress] = {}
    
    def get_user_progress(self, user_id: str, skill: str) -> UserProgress:
        """Get or create user progress tracking"""
        key = f"{user_id}_{skill}"
        if key not in self.user_data:
            self.user_data[key] = UserProgress(user_id=user_id, skill=skill)
        return self.user_data[key]
    
    def update_progress(self, user_id: str, skill: str, lesson_completed: bool = False, 
                       quiz_score: float = None) -> UserProgress:
        """Update user progress after lesson/quiz completion"""
        progress = self.get_user_progress(user_id, skill)
        
        if lesson_completed:
            progress.lessons_completed += 1
            progress.last_activity = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if quiz_score is not None:
            progress.add_quiz_score(quiz_score)
        
        return progress
    
    def get_recommendation(self, progress: UserProgress) -> str:
        """Generate learning recommendations based on progress"""
        avg_score = progress.get_average_score()
        
        if progress.lessons_completed == 0:
            return "🎯 Ready to start your learning journey! Begin with your first lesson."
        elif avg_score >= 0.8:
            return f"🌟 Excellent work! You're mastering {progress.skill}. Ready for the next challenge?"
        elif avg_score >= 0.6:
            return f"📈 Good progress! Keep practicing {progress.skill} to build confidence."
        else:
            return f"💪 Don't give up! Review the concepts and try again. Practice makes perfect!"

class AgenticSkillBuilder:
    """Main orchestrator for the agentic skill building platform"""
    
    def __init__(self):
        self.lesson_agent = LessonAgent(client)
        self.quiz_agent = QuizAgent(client)
        self.progress_agent = ProgressAgent()
        self.current_lesson: Optional[Lesson] = None
        self.current_quiz: Optional[Quiz] = None
        self.current_user = "demo_user"  # In a real app, this would be from authentication
        
        # Predefined skills
        self.predefined_skills = [
            "Python Programming", "Spanish Language", "Public Speaking", 
            "Data Science", "Machine Learning", "JavaScript", "Project Management",
            "Digital Marketing", "Creative Writing", "Photography"
        ]
    
    async def start_lesson(self, skill: str) -> Tuple[str, str, str]:
        """Start a new lesson for the selected skill"""
        try:
            progress = self.progress_agent.get_user_progress(self.current_user, skill)
            
            # Get list of previous lesson titles for context
            previous_lessons = []  # In a real app, you'd store this
            
            self.current_lesson = await self.lesson_agent.generate_lesson(
                skill, progress.current_difficulty, previous_lessons
            )
            
            lesson_content = f"""
            # 📚 {self.current_lesson.title}
            
            **Skill:** {self.current_lesson.skill} | **Level:** {self.current_lesson.difficulty.title()} | **Duration:** ~{self.current_lesson.duration_minutes} min
            
            {self.current_lesson.content}
            
            ### 🔑 Key Concepts:
            {chr(10).join([f"• {concept}" for concept in self.current_lesson.key_concepts])}
            """
            
            return lesson_content, "✅ Complete Lesson", ""
            
        except Exception as e:
            logger.error(f"Error starting lesson: {e}")
            return f"❌ Error generating lesson: {str(e)}", "Try Again", ""
    
    async def complete_lesson_and_start_quiz(self) -> Tuple[str, str, str]:
        """Mark lesson as complete and start the quiz"""
        if not self.current_lesson:
            return "⚠️ No active lesson to complete.", "", ""
        
        try:
            # Update progress
            progress = self.progress_agent.update_progress(
                self.current_user, self.current_lesson.skill, lesson_completed=True
            )
            
            # Generate quiz
            self.current_quiz = await self.quiz_agent.generate_quiz(self.current_lesson, progress)
            
            quiz_content = f"""
            # 🧠 Quiz: {self.current_lesson.title}
            
            Test your understanding of the lesson. Answer all questions to see your results!
            
            """
            
            # Add questions to the content
            for i, q in enumerate(self.current_quiz.questions, 1):
                quiz_content += f"\n**Question {i}:** {q['question']}\n"
                if q['type'] == 'multiple_choice':
                    quiz_content += f"Options: {', '.join(q['options'])}\n"
                elif q['type'] == 'true_false':
                    quiz_content += "Answer: True or False\n"
            
            return quiz_content, "📝 Submit Quiz", ""
            
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return f"❌ Error generating quiz: {str(e)}", "", ""
    
    def submit_quiz(self, *answers) -> Tuple[str, str, str]:
        """Process quiz submission and show results"""
        if not self.current_quiz:
            return "⚠️ No active quiz to submit.", "", ""
        
        try:
            correct_answers = 0
            total_questions = len(self.current_quiz.questions)
            results = []
            
            for i, (question, answer) in enumerate(zip(self.current_quiz.questions, answers)):
                if answer is None or answer == "":
                    continue
                    
                is_correct = False
                correct_answer = question['correct_answer']
                
                if question['type'] == 'multiple_choice':
                    is_correct = answer.strip().upper() == str(correct_answer).upper()
                elif question['type'] == 'true_false':
                    is_correct = answer.lower() == str(correct_answer).lower()
                
                if is_correct:
                    correct_answers += 1
                
                results.append({
                    'question': question['question'],
                    'your_answer': answer,
                    'correct_answer': correct_answer,
                    'is_correct': is_correct,
                    'explanation': question.get('explanation', '')
                })
            
            score = correct_answers / total_questions if total_questions > 0 else 0
            
            # Update progress with quiz score
            progress = self.progress_agent.update_progress(
                self.current_user, self.current_lesson.skill, quiz_score=score
            )
            
            # Generate results content
            results_content = f"""
            # 🎯 Quiz Results
            
            **Score:** {correct_answers}/{total_questions} ({score:.1%})
            
            **Performance:** {'🌟 Excellent!' if score >= 0.8 else '👍 Good work!' if score >= 0.6 else '💪 Keep practicing!'}
            
            ### Detailed Results:
            """
            
            for i, result in enumerate(results, 1):
                status = "✅" if result['is_correct'] else "❌"
                results_content += f"""
                **Q{i}:** {result['question']}
                {status} Your answer: {result['your_answer']}
                Correct answer: {result['correct_answer']}
                {result['explanation']}
                
                """
            
            # Add progress and recommendations
            recommendation = self.progress_agent.get_recommendation(progress)
            
            results_content += f"""
            ### 📊 Your Progress
            - **Lessons completed:** {progress.lessons_completed}
            - **Average score:** {progress.get_average_score():.1%}
            - **Current level:** {progress.current_difficulty.title()}
            
            ### 🎯 Recommendation
            {recommendation}
            """
            
            return results_content, "🔄 Start New Lesson", ""
            
        except Exception as e:
            logger.error(f"Error processing quiz: {e}")
            return f"❌ Error processing quiz: {str(e)}", "", ""

# Initialize the main application
app = AgenticSkillBuilder()

def create_interface():
    """Create the Gradio interface"""
    
    with gr.Blocks(
        title="SkillSprout",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 800px !important;
            margin: auto !important;
        }
        """
    ) as demo:
        
        # Header
        gr.Markdown("""
        # 🌱 SkillSprout
        ### AI-Powered Microlearning Platform
        
        Learn new skills through bite-sized lessons and adaptive quizzes powered by Azure OpenAI!
        """)
        
        # State variables
        current_skill = gr.State("")
        with gr.Tab("🎯 Start Learning"):
            gr.Markdown("### Choose a skill to begin your microlearning journey")
            
            with gr.Row():
                with gr.Column():
                    skill_dropdown = gr.Dropdown(
                        choices=app.predefined_skills,
                        label="📚 Select a Skill",
                        info="Choose from popular skills..."
                    )
                    custom_skill = gr.Textbox(
                        label="✍️ Or enter a custom skill",
                        info="e.g., Cooking, Guitar, Time Management..."
                    )
                    
                    start_btn = gr.Button("🚀 Start Learning", variant="primary", size="lg")
            
            # Lesson content area
            lesson_output = gr.Markdown(visible=False)
            lesson_btn = gr.Button("Complete Lesson", visible=False)
            
            # Quiz area
            quiz_output = gr.Markdown(visible=False)
            
            # Dynamic quiz inputs (will be created based on quiz content)
            quiz_inputs = []
            for i in range(5):  # Max 5 questions
                quiz_inputs.append(gr.Textbox(label=f"Answer {i+1}", visible=False))
            
            quiz_submit_btn = gr.Button("Submit Quiz", visible=False)
            
            # Results area
            results_output = gr.Markdown(visible=False)
            restart_btn = gr.Button("Start New Lesson", visible=False)
        
        with gr.Tab("📊 Progress Dashboard"):
            gr.Markdown("### Your Learning Analytics")
            
            progress_display = gr.Markdown("""
            **Welcome to your progress dashboard!**
            
            Complete some lessons to see your learning analytics here.
            """)
            
            refresh_progress_btn = gr.Button("🔄 Refresh Progress")
        
        with gr.Tab("🔗 MCP Endpoints"):
            gr.Markdown("""
            ### Model Context Protocol Integration
            
            This application exposes MCP endpoints for integration with external agents:
            
            - **GET /lesson/{skill}** - Fetch next lesson for a skill
            - **GET /progress/{user_id}** - Get user progress data  
            - **POST /quiz/submit** - Submit quiz results
            
            *Coming soon: Full MCP server implementation*
            """)
        
        # Event handlers
        async def handle_start_learning(skill_choice, custom_skill_input):
            skill = custom_skill_input.strip() if custom_skill_input.strip() else skill_choice
            if not skill:
                return [
                    gr.update(value="⚠️ Please select or enter a skill to continue."),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    skill
                ] + [gr.update(visible=False, value="") for _ in range(5)]
            
            lesson_content, btn_text, _ = await app.start_lesson(skill)
            
            return [
                gr.update(value=lesson_content),
                gr.update(value=btn_text, visible=True),
                gr.update(visible=False),
                skill
            ] + [gr.update(visible=False, value="") for _ in range(5)]
        
        async def handle_complete_lesson():
            quiz_content, btn_text, _ = await app.complete_lesson_and_start_quiz()
            
            # Show quiz inputs based on number of questions
            quiz_updates = []
            if app.current_quiz:
                for i, question in enumerate(app.current_quiz.questions):
                    if i < len(quiz_inputs):
                        label = f"Q{i+1}: {question['question'][:50]}..."
                        quiz_updates.append(gr.update(label=label, visible=True))
                    else:
                        quiz_updates.append(gr.update(visible=False))
                # Hide remaining inputs
                for i in range(len(app.current_quiz.questions), len(quiz_inputs)):
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
            # Filter out None values and empty strings
            valid_answers = [ans for ans in answers if ans is not None and ans != ""]
            
            results_content, btn_text, _ = app.submit_quiz(*valid_answers)
            
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
            if not app.progress_agent.user_data:
                return "**No learning data yet.** Complete some lessons to see your progress!"
            
            progress_content = "# 📊 Your Learning Progress\n\n"
            
            for key, progress in app.progress_agent.user_data.items():
                progress_content += f"""
                **Skill:** {progress.skill}
                - Lessons completed: {progress.lessons_completed}
                - Average quiz score: {progress.get_average_score():.1%}
                - Current difficulty: {progress.current_difficulty.title()}
                - Last activity: {progress.last_activity or 'Never'}
                
                """
            return progress_content
        
        # Wire up the events
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
    
    return demo

def main():
    """Main application entry point"""
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()
