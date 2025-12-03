import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import InvalidArgument, Unauthenticated

# Load environment variables from .env file
load_dotenv()

# 1. SETUP: Get API key from environment or use test key
TEST_KEY = os.getenv("GOOGLE_API_KEY") or "YOUR_PASTED_API_KEY_HERE"

def run_vibe_check():
    print(f"--- 📡 Initiating Gemini API Vibe Check ---")
    
    # Check if API key is set
    if TEST_KEY == "YOUR_PASTED_API_KEY_HERE" or not TEST_KEY:
        print("❌ ERROR: GOOGLE_API_KEY not found!")
        print("   Please set it in one of these ways:")
        print("   1. Create a .env file with: GOOGLE_API_KEY=your_key_here")
        print("   2. Set environment variable: $env:GOOGLE_API_KEY='your_key_here' (PowerShell)")
        print("   3. Edit apitest.py and replace TEST_KEY with your actual key")
        return
    
    print(f"✓ API Key found: {TEST_KEY[:10]}...{TEST_KEY[-4:] if len(TEST_KEY) > 14 else '****'}")
    
    # 2. INITIALIZE: Try different models to find one that works
    models_to_try = [
        "gemini-1.5-flash",  # Fastest, cheapest
        "gemini-1.5-pro",    # More capable
        "gemini-2.5-pro",    # Latest stable
        "gemini-3-pro-preview"  # Latest preview
    ]
    
    llm = None
    working_model = None
    
    for model_name in models_to_try:
        try:
            print(f"\n🔄 Trying model: {model_name}...")
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=TEST_KEY,
                temperature=0.0,
                max_retries=1  # Fail fast
            )
            # Quick test invocation
            test_response = llm.invoke("Hi")
            working_model = model_name
            print(f"✅ Model {model_name} works!")
            break
        except InvalidArgument as e:
            print(f"   ⚠️  Model {model_name} not available: {str(e)[:100]}")
            continue
        except Exception as e:
            print(f"   ⚠️  Model {model_name} failed: {type(e).__name__}")
            continue
    
    if not llm:
        print("\n❌ ERROR: Could not initialize any model!")
        print("   Check your API key and available models.")
        return
    
    print(f"\n✓ Using model: {working_model}")

    # 3. THE PROMPT: Simple, low-token verification
    test_prompt = "System Check: Reply with the exact string '200 OK' if you receive this message."
    
    print(f"sending payload: '{test_prompt}'...")

    # 4. EXECUTE
    try:
        response = llm.invoke(test_prompt)
        
        # 5. VERIFY
        clean_response = response.content.strip()
        if "200 OK" in clean_response:
            print(f"✅ SUCCESS: API Key is valid. Model responded: '{clean_response}'")
        else:
            print(f"⚠️  WARNING: Connected, but unexpected response: '{clean_response}'")
            
    except Unauthenticated:
        print("❌ ERROR: 401 Unauthenticated. Your API Key is invalid or expired.")
    except InvalidArgument:
        print("❌ ERROR: 400 Invalid Argument. Check if the model name is correct.")
    except Exception as e:
        print(f"❌ ERROR: Connection failed. Details:\n{e}")

if __name__ == "__main__":
    run_vibe_check()