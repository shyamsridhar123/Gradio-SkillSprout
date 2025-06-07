"""
Hackathon Validation Script
Tests the MCP server functionality for submission requirements
"""

import asyncio
import requests
import time
import subprocess
import threading
from datetime import datetime

def test_mcp_server_endpoints():
    """Test MCP server endpoints to ensure hackathon compliance"""
    print("🧪 HACKATHON VALIDATION - MCP SERVER TESTING")
    print("=" * 60)
    
    base_url = "http://localhost:8001"  # MCP server port
    
    tests = [
        ("Root endpoint", "GET", "/"),
        ("Skills list", "GET", "/mcp/skills"),
        ("Progress endpoint", "GET", "/mcp/progress/test_user"),
    ]
    
    print(f"🌐 Testing MCP server at {base_url}")
    print(f"📋 Running {len(tests)} endpoint tests...\n")
    
    results = []
    
    for test_name, method, endpoint in tests:
        try:
            url = f"{base_url}{endpoint}"
            print(f"🔄 Testing {test_name}: {method} {endpoint}")
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json={}, timeout=5)
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS: {response.status_code}")
                try:
                    data = response.json()
                    if "mcp" in str(data).lower() or "agentic" in str(data).lower():
                        print(f"  🎯 MCP-compliant response detected")
                except:
                    pass
                results.append((test_name, True, response.status_code))
            else:
                print(f"  ❌ FAILED: {response.status_code}")
                results.append((test_name, False, response.status_code))
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ CONNECTION ERROR: {e}")
            results.append((test_name, False, "Connection Error"))
        
        print()
    
    # Summary
    print("📊 TEST SUMMARY")
    print("-" * 40)
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL MCP ENDPOINT TESTS PASSED!")
    else:
        print("⚠️  Some tests failed. Check the MCP server.")
    
    return results

def test_post_endpoints():
    """Test POST endpoints with sample data"""
    print("\n🧪 TESTING POST ENDPOINTS")
    print("=" * 40)
    
    base_url = "http://localhost:8001"
    
    # Test lesson generation
    try:
        print("🔄 Testing lesson generation...")
        lesson_data = {
            "skill": "Python Programming",
            "user_id": "test_user",
            "difficulty": "beginner"
        }
        response = requests.post(f"{base_url}/mcp/lesson/generate", json=lesson_data, timeout=10)
        if response.status_code == 200:
            print("  ✅ Lesson generation successful")
            data = response.json()
            if "lesson" in data:
                print("  🎯 Lesson data structure valid")
        else:
            print(f"  ❌ Lesson generation failed: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Lesson generation error: {e}")

    # Test quiz submission
    try:
        print("🔄 Testing quiz submission...")
        quiz_data = {
            "user_id": "test_user",
            "skill": "Python Programming",
            "lesson_title": "Variables and Data Types",
            "answers": ["correct", "incorrect", "correct"]
        }
        response = requests.post(f"{base_url}/mcp/quiz/submit", json=quiz_data, timeout=10)
        if response.status_code == 200:
            print("  ✅ Quiz submission successful")
        else:
            print(f"  ❌ Quiz submission failed: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Quiz submission error: {e}")

def validate_hackathon_requirements():
    """Validate all hackathon submission requirements"""
    print("\n🏆 HACKATHON SUBMISSION VALIDATION")
    print("=" * 50)
    
    requirements = []
    
    # Check README.md for required tag
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
            if "mcp-server-track" in readme_content:
                print("✅ README.md contains 'mcp-server-track' tag")
                requirements.append(("README tag", True))
            else:
                print("❌ README.md missing 'mcp-server-track' tag")
                requirements.append(("README tag", False))
    except FileNotFoundError:
        print("❌ README.md not found")
        requirements.append(("README file", False))
    
    # Check for demo video link
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
            if "demo-video-link.com" in readme_content or "your-demo-video-link.com" in readme_content:
                print("⚠️  Demo video link is placeholder - needs actual video")
                requirements.append(("Demo video", False))
            elif any(video_keyword in readme_content.lower() for video_keyword in ["youtube.com", "vimeo.com", "loom.com", "demo video"]):
                print("✅ Demo video link appears to be present")
                requirements.append(("Demo video", True))
            else:
                print("❌ Demo video link not found")
                requirements.append(("Demo video", False))
    except:
        requirements.append(("Demo video check", False))
    
    # Check space_app.py exists and has MCP endpoints
    try:
        with open("space_app.py", "r", encoding="utf-8") as f:
            app_content = f.read()
            if "FastAPI" in app_content and "@mcp_app" in app_content:
                print("✅ space_app.py has MCP server integration")
                requirements.append(("MCP integration", True))
            else:
                print("❌ space_app.py missing MCP server integration")
                requirements.append(("MCP integration", False))
    except FileNotFoundError:
        print("❌ space_app.py not found")
        requirements.append(("Main app file", False))
    
    # Check requirements.txt
    try:
        with open("requirements.txt", "r") as f:
            reqs = f.read()
            if "gradio" in reqs and "fastapi" in reqs:
                print("✅ requirements.txt has necessary dependencies")
                requirements.append(("Dependencies", True))
            else:
                print("❌ requirements.txt missing key dependencies")
                requirements.append(("Dependencies", False))
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        requirements.append(("Requirements file", False))
    
    print("\n📋 SUBMISSION CHECKLIST")
    print("-" * 30)
    passed = sum(1 for _, success in requirements if success)
    total = len(requirements)
    
    for req_name, success in requirements:
        status = "✅" if success else "❌"
        print(f"{status} {req_name}")
    
    print(f"\n📊 Overall Score: {passed}/{total}")
    
    if passed == total:
        print("🎉 READY FOR HACKATHON SUBMISSION!")
    else:
        print("⚠️  Please address the failed requirements above.")
    
    return requirements

def main():
    """Main validation function"""
    print("🚀 AGENTIC SKILL BUILDER - HACKATHON VALIDATION")
    print("=" * 60)
    print(f"⏰ Validation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # First validate file-based requirements
    validate_hackathon_requirements()
    
    # Ask user if they want to test the running server
    print("\n" + "="*60)
    print("🌐 MCP SERVER TESTING")
    print("To test MCP endpoints, the server should be running on localhost:8001")
    print("You can start it with: python space_app.py")
    
    try:
        # Try to test if server is running
        response = requests.get("http://localhost:8001", timeout=2)
        print("✅ Server detected running!")
        test_mcp_server_endpoints()
        test_post_endpoints()
    except:
        print("⚠️  Server not detected. Start the server to test MCP endpoints.")
        print("   Command: python space_app.py")
    
    print("\n" + "="*60)
    print("🎯 NEXT STEPS FOR HACKATHON SUBMISSION:")
    print("1. 📹 Record demo video showing MCP server in action")
    print("2. 🔗 Update README.md with actual demo video link")
    print("3. 🚀 Upload to Hugging Face Spaces under Agents-MCP-Hackathon org")
    print("4. ✅ Ensure all MCP endpoints work in the deployed Space")
    print("=" * 60)

if __name__ == "__main__":
    main()
