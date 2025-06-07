# 🎬 Demo Video Script - Agentic Skill Builder MCP Server

## Video Duration: 3-5 minutes
## Target Audience: Hackathon judges and MCP developers

---

## 🎯 **Opening (0:00 - 0:30)**

**Visual:** Screen showing the Gradio interface running on localhost:7860
**Narration:** 
> "Welcome to the Agentic Skill Builder - our submission for the Gradio Agents & MCP Hackathon 2025, Track 1: MCP Server/Tool. This is a unique AI-powered microlearning platform that serves both as a beautiful Gradio interface AND a fully functional MCP server."

---

## 🔗 **MCP Server Demonstration (0:30 - 2:00)**

### Part 1: Server Status & Endpoints (0:30 - 1:00)
**Visual:** Browser showing http://localhost:8001/
**Narration:**
> "First, let me show you our MCP server running on port 8001. This endpoint provides metadata about our hackathon submission."

**Action:** Show JSON response with hackathon information

**Visual:** Terminal/Postman showing MCP endpoints
**Narration:**
> "Our MCP server exposes four key endpoints:
> - GET /mcp/skills - Lists available learning skills
> - POST /mcp/lesson/generate - Creates personalized lessons
> - GET /mcp/progress/{user_id} - Tracks learning progress
> - POST /mcp/quiz/submit - Processes quiz submissions"

### Part 2: Live MCP Endpoint Testing (1:00 - 2:00)
**Visual:** Testing each MCP endpoint with curl or PowerShell
**Narration:**
> "Let me demonstrate these endpoints in action. First, getting available skills..."

**Action:** Show GET /mcp/skills response
```powershell
curl http://localhost:8001/mcp/skills
```
**Expected Response:**
```json
{
  "predefined_skills": ["Python Programming", "Spanish Language", "Public Speaking", "Data Science", "Machine Learning", "JavaScript", "Project Management", "Digital Marketing", "Creative Writing", "Photography"]
}
```

> "Now generating a personalized lesson for Python Programming..."

**Action:** Show POST /mcp/lesson/generate with request body and response
```powershell
curl -X POST http://localhost:8001/mcp/lesson/generate `
  -H "Content-Type: application/json" `
  -d '{
    "skill": "Python Programming",
    "level": "beginner",
    "user_context": "I want to learn Python for data analysis"
  }'
```
**Expected Response:**
```json
{
  "lesson_id": "lesson_12345",
  "skill": "Python Programming",
  "title": "Introduction to Python for Data Analysis",
  "content": "Python is a powerful programming language...",
  "difficulty": "beginner",
  "estimated_time": "15 minutes",
  "mcp_server": "Agentic Skill Builder"
}
```

> "Let's check user progress to see learning analytics..."

**Action:** Show GET /mcp/progress/demo_user response
```powershell
curl http://localhost:8001/mcp/progress/demo_user
```
**Expected Response:**
```json
{
  "user_id": "demo_user",
  "skills_progress": {
    "Python Programming": {
      "lessons_completed": 2,
      "quiz_scores": [85, 92],
      "current_level": "intermediate"
    }
  },
  "total_skills_learning": 1,
  "mcp_server": "Agentic Skill Builder",
  "timestamp": "2025-06-07T04:48:36.691517"
}
```

> "Finally, let's submit a quiz answer to show the interactive capabilities..."

**Action:** Show POST /mcp/quiz/submit with request body and response
```powershell
curl -X POST http://localhost:8001/mcp/quiz/submit `
  -H "Content-Type: application/json" `
  -d '{
    "user_id": "demo_user",
    "quiz_id": "quiz_python_001",
    "answers": ["list", "dictionary", "tuple"],
    "skill": "Python Programming"
  }'
```
**Expected Response:**
```json
{
  "quiz_id": "quiz_python_001",
  "user_id": "demo_user",
  "score": 85,
  "feedback": "Great job! You correctly identified Python data structures.",
  "passed": true,
  "mcp_server": "Agentic Skill Builder"
}
```

---

## 🎨 **Gradio Interface Demo (2:00 - 3:30)**

### Part 1: Learning Flow (2:00 - 3:00)
**Visual:** Gradio interface at localhost:7860
**Narration:**
> "Now let's see the beautiful Gradio interface in action. The same AI agents that power our MCP endpoints create this seamless learning experience."

**Action:** 
1. Select "Data Science" skill
2. Click "Start Learning"
3. Show generated lesson content
4. Complete lesson and start quiz
5. Answer quiz questions
6. Show results and progress

### Part 2: MCP Testing Interface (3:00 - 3:30)
**Visual:** Built-in MCP endpoint testing section in Gradio
**Narration:**
> "What makes this special is that we've built MCP endpoint testing directly into our Gradio interface. You can test all our MCP endpoints without leaving the app."

**Action:** Show the MCP endpoint testing interface working

---

## 🏆 **Hackathon Highlights (3:30 - 4:30)**

**Visual:** Split screen showing both Gradio UI and MCP endpoints
**Narration:**
> "This submission perfectly demonstrates the agentic architecture we've built:
> - Three specialized AI agents working together
> - Lesson Agent generates personalized content
> - Quiz Agent creates adaptive assessments  
> - Progress Agent tracks learning analytics
> - All coordinated by our main orchestrator"

**Visual:** Show the architecture diagram or code structure
**Narration:**
> "The same agents power both the beautiful user interface AND the MCP protocol endpoints, making our platform ready for integration with Claude Desktop, Cursor, or any MCP client."

---

## 🚀 **Call to Action (4:30 - 5:00)**

**Visual:** README.md showing deployment instructions
**Narration:**
> "You can deploy this immediately to Hugging Face Spaces using our space_app.py file, or run it locally following our comprehensive documentation. This represents the future of AI-powered education - agentic, interoperable, and ready for the Model Context Protocol ecosystem."

**Visual:** Final shot of both servers running simultaneously
**Narration:**
> "Thank you for watching our Agentic Skill Builder demo. We're excited to contribute to the MCP ecosystem and the future of AI agents working together!"

---

## 📝 **Recording Checklist**

### Before Recording:
- [ ] Ensure both servers are running (Gradio on 7860, MCP on 8001)
- [ ] Prepare browser tabs for all endpoints
- [ ] Have curl commands or Postman collection ready
- [ ] Test the complete learning flow works
- [ ] Check audio/screen recording quality

### During Recording:
- [ ] Speak clearly and at moderate pace
- [ ] Show actual JSON responses from MCP endpoints
- [ ] Demonstrate real-time lesson generation
- [ ] Highlight the dual-purpose architecture
- [ ] Keep within 5-minute time limit

### After Recording:
- [ ] Upload to YouTube/Vimeo
- [ ] Update README.md with video link
- [ ] Add video link to HF Spaces README
- [ ] Verify video is publicly accessible

---

## 🎥 **Technical Recording Tips**

1. **Use OBS Studio or similar** for high-quality screen recording
2. **Record at 1080p** for clear text visibility
3. **Use good microphone** for clear narration
4. **Multiple takes OK** - edit together the best parts
5. **Add captions** for accessibility
6. **Include timestamps** in video description

---

**Ready to showcase the future of agentic learning with MCP integration! 🚀**
