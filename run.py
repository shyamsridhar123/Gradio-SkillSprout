"""
Launcher script for SkillSprout
Runs both the Gradio interface and MCP server
"""

import asyncio
import subprocess
import sys
import time
import threading
from pathlib import Path

def run_gradio_app():
    """Run the main Gradio application"""
    print("🚀 Starting Gradio App...")
    subprocess.run([sys.executable, "app.py"])

def run_mcp_server():
    """Run the MCP server"""
    print("🔗 Starting MCP Server...")
    subprocess.run([sys.executable, "mcp_server.py"])

def main():
    """Main launcher function"""
    print("=" * 60)
    print("🌱 SKILLSPROUT")
    print("   AI-Powered Microlearning Platform")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        print("❌ Error: app.py not found. Please run this script from the project directory.")
        return
    
    print("Choose how to run the application:")
    print("1. Gradio App only (recommended for demo)")
    print("2. MCP Server only")
    print("3. Both Gradio App and MCP Server")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\n🎯 Starting Gradio App...")
        print("📱 Interface will be available at: http://localhost:7860")
        run_gradio_app()
    
    elif choice == "2":
        print("\n🔗 Starting MCP Server...")
        print("🌐 API will be available at: http://localhost:8000")
        print("📚 API docs at: http://localhost:8000/docs")
        run_mcp_server()
    
    elif choice == "3":
        print("\n🚀 Starting both services...")
        print("📱 Gradio App: http://localhost:7860")
        print("🌐 MCP Server: http://localhost:8000")
        print("📚 API docs: http://localhost:8000/docs")
        print()
        
        # Start MCP server in a separate thread
        mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
        mcp_thread.start()
        
        # Give MCP server time to start
        time.sleep(2)
        
        # Start Gradio app (this will block)
        run_gradio_app()
    
    else:
        print("❌ Invalid choice. Please run the script again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Thanks for using SkillSprout!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check your configuration and try again.")
