# 🚀 Hugging Face Spaces Deployment Guide

## 📋 Pre-Deployment Checklist

### ✅ **Files Ready for Upload:**
- `space_app.py` - Main application file (Gradio + MCP server)
- `requirements.txt` - HF Spaces optimized dependencies  
- `README_spaces.md` - Spaces configuration (rename to README.md)
- `config.py` - Configuration utilities
- `.env` - Environment variables (handle separately)

### ✅ **Configuration Complete:**
- App file specified: `space_app.py`
- SDK: `gradio 4.44.0`
- Tags include: `mcp-server-track`
- License: MIT

---

## 🔧 **Deployment Steps**

### **Step 1: Create Hugging Face Space**

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. **Important:** Create under the `Agents-MCP-Hackathon` organization
4. Space name: `agentic-skill-builder`
5. Choose "Gradio" as SDK
6. Set to Public
7. Click "Create Space"

### **Step 2: Upload Files**

Upload these files to your new Space:

```
📁 agentic-skill-builder/
├── 📄 README.md (renamed from README_spaces.md)
├── 📄 space_app.py
├── 📄 requirements.txt
├── 📄 config.py
└── 📄 .env (create in Spaces settings)
```

### **Step 3: Configure Environment Variables**

In your HF Space settings, add these environment variables:

```env
AZURE_OPENAI_ENDPOINT=your-azure-endpoint
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_LLM_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_LLM_MODEL=gpt-4.1
```

**⚠️ Important:** Never commit your `.env` file with real credentials to a public repo!

### **Step 4: Verify Deployment**

Once deployed, your Space should:
- ✅ Show the Gradio interface
- ✅ Respond to MCP endpoints at `https://your-space-name.hf.space/mcp/skills`
- ✅ Generate lessons and quizzes
- ✅ Include hackathon branding and MCP testing interface

---

## 🔍 **Testing Your Deployed Space**

### **Gradio Interface Test:**
1. Visit your Space URL
2. Select a skill (e.g., "Python Programming")
3. Complete the full learning flow
4. Verify AI generates lessons and quizzes

### **MCP Endpoints Test:**
```bash
# Test from anywhere on the internet
curl https://your-space-name.hf.space/mcp/skills
curl https://your-space-name.hf.space/mcp/progress/test_user
```

---

## 📝 **Post-Deployment Updates**

### **Update README.md with:**
1. **Live demo link:** Replace local URLs with your HF Space URL
2. **Video link:** Add your demo video URL
3. **Deployment status:** Confirm it's live and working

### **Example Updates:**
```markdown
## 🎬 Demo Video
**MCP Server in Action:** [https://youtu.be/your-video-id](https://youtu.be/your-video-id)

## 🌐 Live Demo
**Try it now:** [https://huggingface.co/spaces/Agents-MCP-Hackathon/agentic-skill-builder](https://huggingface.co/spaces/Agents-MCP-Hackathon/agentic-skill-builder)

## 🔗 MCP Endpoints
Test our live MCP server at: `https://your-space-name.hf.space/mcp/`
```

---

## 🏆 **Final Hackathon Submission Checklist**

- [ ] ✅ Space deployed under Agents-MCP-Hackathon organization
- [ ] ✅ "mcp-server-track" tag in README
- [ ] ✅ Demo video uploaded and linked
- [ ] ✅ Live MCP endpoints working
- [ ] ✅ Gradio interface fully functional
- [ ] ✅ All dependencies working in cloud environment
- [ ] ✅ Documentation updated with live links

---

## 🚨 **Troubleshooting Common Issues**

### **Build Failures:**
- Check `requirements.txt` for incompatible versions
- Verify all imports work in `space_app.py`
- Ensure environment variables are set correctly

### **MCP Endpoints Not Working:**
- Verify FastAPI routes are properly configured
- Check if app.mount() is correctly set up
- Test endpoints locally first

### **Azure OpenAI Errors:**
- Confirm environment variables are set in Spaces settings
- Check Azure OpenAI quota and model availability
- Verify API key permissions

---

**Ready to deploy! Your agentic skill builder will be live for the world to see! 🌍✨**
