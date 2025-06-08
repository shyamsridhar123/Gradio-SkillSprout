"""
Quick test to verify environment variables are loaded correctly
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_env_vars():
    """Test if required environment variables are available"""
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY", 
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_LLM_DEPLOYMENT",
        "AZURE_OPENAI_LLM_MODEL"
    ]
    
    print("🔍 Environment Variables Check")
    print("=" * 40)
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value and value.strip():
            print(f"✅ {var}: Present")
        else:
            print(f"❌ {var}: Missing or empty")
            all_present = False
    
    print("=" * 40)
    if all_present:
        print("🎉 All environment variables are properly configured!")
        print("✅ Your app should work in Hugging Face Spaces")
    else:
        print("⚠️  Some environment variables are missing")
        print("🔧 Set them in Hugging Face Spaces Repository Secrets")
    
    return all_present

if __name__ == "__main__":
    test_env_vars()
