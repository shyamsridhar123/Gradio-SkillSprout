---
title: Agentic Skill Builder - MCP Hackathon 2025
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: space_app.py
pinned: false
license: mit
tags:
  - mcp-server-track
  - agents
  - education
  - microlearning
  - azure-openai
  - model-context-protocol
short_description: AI-powered microlearning platform with MCP integration
---

# 🚀 Agentic Skill Builder

**Track:** mcp-server-track

An AI-powered microlearning platform that leverages Azure OpenAI, Gradio, and Model Context Protocol (MCP) to deliver personalized bite-sized lessons and adaptive quizzes.

🎓 **Submitted for the Gradio Agents & MCP Hackathon 2025** 🚀

## 🎬 Demo Video

**MCP Server in Action:** [Demo Video Link](https://your-demo-video-link.com)

*Note: The video demonstrates the MCP server endpoints being used by various MCP clients, showcasing the seamless integration between the Gradio interface and Model Context Protocol functionality.*

## 🏆 Hackathon Highlights

This submission demonstrates several key innovations for the **Gradio Agents & MCP Hackathon 2025**:

### 🤖 **Track 1: MCP Server/Tool**
- ✅ **Dual-Purpose Application**: Single app serving both Gradio interface AND MCP server
- ✅ **Full MCP Protocol Implementation**: Complete endpoints for lesson generation, progress tracking, and quiz submission
- ✅ **External Agent Integration**: Ready for use by Claude Desktop, Cursor, or any MCP client

### 🧠 **Agentic Architecture Innovation**
- **🎓 Lesson Agent**: AI-powered content generation with Azure OpenAI
- **🧪 Quiz Agent**: Adaptive quiz creation based on lesson content and user performance  
- **📊 Progress Agent**: Smart difficulty adjustment and learning recommendations
- **🎯 Orchestrator**: Seamless coordination between all agents and user interactions

### 🔗 **MCP Endpoints Showcase**
- `GET /mcp/skills` - Discover available learning skills
- `POST /mcp/lesson/generate` - Generate personalized micro-lessons
- `GET /mcp/progress/{user_id}` - Access detailed learning analytics
- `POST /mcp/quiz/submit` - Submit and score quiz attempts

### 💡 **Unique Features**
- **Microlearning Focus**: 3-5 minute bite-sized lessons perfect for busy learners
- **Adaptive Difficulty**: AI automatically adjusts based on quiz performance
- **Any Skill Learning**: Works for both predefined and custom skills
- **Real-time Analytics**: Live progress tracking and personalized recommendations

## ✨ Features

- 🎯 **Skill Selection**: Choose from predefined skills or enter custom topics
- 📚 **AI-Generated Micro-Lessons**: Concise, focused lessons (3-5 minutes)
- 🧠 **Adaptive Quizzes**: Smart quizzes that adjust difficulty based on performance
- 📊 **Progress Tracking**: Visual progress monitoring and analytics
- 🤖 **Agentic Architecture**: Multiple specialized AI agents working together
- 🔗 **MCP Integration**: Model Context Protocol endpoints for external integration
- 🎨 **Modern UI**: Clean, responsive Gradio interface

## 🏗️ Architecture

The application uses an agentic architecture with specialized AI agents:

- **Lesson Agent**: Generates personalized micro-lessons
- **Quiz Agent**: Creates adaptive quizzes based on lesson content
- **Progress Agent**: Tracks learning progress and provides recommendations
- **Orchestrator**: Coordinates agent interactions and user flow

## 🚀 Quick Start

### Prerequisites

- **Python 3.10.16** installed
- Azure OpenAI subscription with API key
- Access to GPT-4 model deployment

### Installation

1. **Clone and navigate to the project:**
   ```powershell
   cd c:\Users\shyamsridhar\code\hf-hackathon
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate
   ```
   *(On macOS/Linux, use `source .venv/bin/activate`)*

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Your `.env` file is already configured with Azure OpenAI credentials
   - Verify the credentials are correct and models are deployed

5. **Run the application:**
   ```powershell
   python run.py
   ```

   Choose from three options:
   - **Option 1**: Gradio App only (recommended for demo)
   - **Option 2**: MCP Server only
   - **Option 3**: Both services

## 🎯 Usage

### Learning Flow

1. **Select a Skill**: Choose from predefined skills or enter a custom topic
2. **Read the Lesson**: Engage with AI-generated micro-content
3. **Take the Quiz**: Test your understanding with adaptive questions
4. **View Results**: Get detailed feedback and progress updates
5. **Continue Learning**: Follow AI recommendations for next steps

### Available Skills

- Python Programming
- Spanish Language
- Public Speaking
- Data Science
- Machine Learning
- JavaScript
- Project Management
- Digital Marketing
- Creative Writing
- Photography

*Plus any custom skill you can imagine!*

## 🔗 MCP Endpoints

The application exposes Model Context Protocol endpoints at `http://localhost:8000`:

- `GET /skills` - List available skills
- `POST /lesson/generate` - Generate lesson for a skill
- `GET /progress/{user_id}` - Get user progress data
- `POST /quiz/submit` - Submit quiz results
- `POST /quiz/generate` - Generate quiz for a lesson

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## 📊 Progress Dashboard

Track your learning journey with:

- **Lessons Completed**: Number of lessons finished per skill
- **Quiz Performance**: Average scores and improvement trends
- **Difficulty Progression**: Automatic difficulty adjustment
- **Learning Streaks**: Consistent learning tracking
- **AI Recommendations**: Personalized next steps

## 🔧 Configuration

### Environment Variables

The `.env` file contains your Azure OpenAI configuration:

```properties
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT="your-endpoint"
AZURE_OPENAI_KEY="your-api-key"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"
AZURE_OPENAI_LLM_DEPLOYMENT="gpt-4.1"
AZURE_OPENAI_LLM_MODEL="gpt-4.1"
```

### Optional Settings

You can add these optional environment variables:

```properties
DEBUG=false
LOG_LEVEL=INFO
GRADIO_PORT=7860
MCP_PORT=8000
MAX_QUIZ_QUESTIONS=5
DEFAULT_LESSON_DURATION=5
```

## 🧪 Development

### Running in Development Mode

```powershell
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
python app.py
```

### Testing MCP Endpoints

```bash
# Test lesson generation
curl -X POST "http://localhost:8000/lesson/generate" \
  -H "Content-Type: application/json" \
  -d '{"skill": "Python Programming", "user_id": "test_user"}'

# Get user progress
curl "http://localhost:8000/progress/test_user?skill=Python%20Programming"
```

## 📱 Deployment

### Local Deployment

```powershell
python run.py
```

### Hugging Face Spaces

1. Create a new Space on Hugging Face
2. Upload your code
3. Set environment variables in Space settings
4. The app will auto-deploy

### Azure App Service

1. Create an Azure App Service
2. Deploy using Git or ZIP
3. Configure environment variables
4. Set startup command: `python app.py`

## 🔍 Troubleshooting

### Common Issues

1. **Azure OpenAI Connection Error**
   - Verify your endpoint URL and API key
   - Check if your model deployment is active
   - Ensure you have sufficient quota

2. **Module Import Errors**
   - Activate your virtual environment
   - Install requirements: `pip install -r requirements.txt`

3. **Port Already in Use**
   - Change ports in environment variables
   - Kill existing processes: `netstat -ano | findstr :7860`

### Logs

Check application logs in `agentic_skill_builder.log` for detailed error information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of a hackathon submission. See the full requirements in `i dont want the code but a detailed prd document.md`.

## 🏆 Hackathon Features

This implementation demonstrates:

- ✅ **Agentic Workflows**: Multiple AI agents collaborating
- ✅ **Azure OpenAI Integration**: Modern SDK usage with best practices
- ✅ **Adaptive Learning**: Smart difficulty adjustment
- ✅ **Modern UI**: Gradio-based responsive interface
- ✅ **MCP Protocol**: External agent integration capability
- ✅ **Progress Analytics**: Comprehensive learning tracking
- ✅ **Error Handling**: Robust error management and fallbacks

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the logs in `agentic_skill_builder.log`
3. Verify your Azure OpenAI configuration
4. Ensure all dependencies are installed correctly

---

**Happy Learning! 🎓**
