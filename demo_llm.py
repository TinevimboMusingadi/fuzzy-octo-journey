"""Demo script to show LLM usage in the agent."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.modes import ask_speed, ask_quality, process_speed, process_quality
from src.config import AgentConfig

load_dotenv()

def demo_question_generation():
    """Show difference between Speed and Quality mode questions."""
    print("=" * 70)
    print("DEMO 1: Question Generation")
    print("=" * 70)
    
    field = {
        "field_type": "email",
        "label": "Email Address",
        "description": "We'll use this to contact you"
    }
    
    context = {
        "name": {"value": "John Doe"}
    }
    
    # Speed Mode
    print("\n🏃 SPEED MODE (Template-based, no LLM):")
    speed_question = ask_speed(field, context)
    print(f"   {speed_question}")
    
    # Quality Mode
    print("\n🧠 QUALITY MODE (LLM-generated, contextual):")
    config = AgentConfig(default_mode="quality")
    try:
        quality_question = ask_quality(field, context, config)
        print(f"   {quality_question}")
    except Exception as e:
        import traceback
        print(f"   ❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")
        print("\n   Full traceback:")
        traceback.print_exc()
        print("   (This means your API key might be invalid or you have no internet)")

def demo_value_extraction():
    """Show difference in extracting values from natural language."""
    print("\n" + "=" * 70)
    print("DEMO 2: Value Extraction from Natural Language")
    print("=" * 70)
    
    field = {"field_type": "number", "label": "Age"}
    user_input = "I'm thirty years old"
    
    # Speed Mode
    print(f"\n📝 User said: '{user_input}'")
    print("\n🏃 SPEED MODE (Regex extraction):")
    speed_result = process_speed(user_input, field)
    print(f"   Extracted: {speed_result.get('value')}")
    print(f"   Confidence: {speed_result.get('confidence')}")
    print(f"   Method: {speed_result.get('extraction_method')}")
    
    # Quality Mode
    print("\n🧠 QUALITY MODE (LLM extraction):")
    config = AgentConfig(default_mode="quality")
    try:
        quality_result = process_quality(user_input, field, config)
        print(f"   Extracted: {quality_result.get('value')}")
        print(f"   Confidence: {quality_result.get('confidence')}")
        print(f"   Method: {quality_result.get('extraction_method')}")
        if quality_result.get('notes'):
            print(f"   Notes: {quality_result.get('notes')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def demo_hybrid_mode():
    """Show how hybrid mode works."""
    print("\n" + "=" * 70)
    print("DEMO 3: Hybrid Mode (Best of Both Worlds)")
    print("=" * 70)
    
    print("\n💡 Hybrid mode uses:")
    print("   - Speed Mode for simple fields (name, simple email)")
    print("   - Quality Mode for complex fields (addresses, unclear input)")
    print("   - Quality Mode for clarifications")
    print("\n   This saves money while maintaining quality!")

if __name__ == "__main__":
    print("\n🤖 Dynamic Intake Form Agent - LLM Usage Demo")
    print("=" * 70)
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("\n⚠️  WARNING: No GOOGLE_API_KEY found in .env file!")
        print("   Quality Mode demos will fail.")
        print("   Get a free key: https://makersuite.google.com/app/apikey")
    else:
        print(f"\n✅ API Key found: {api_key[:20]}...")
    
    demo_question_generation()
    demo_value_extraction()
    demo_hybrid_mode()
    
    print("\n" + "=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    print("\nTo see the LLM in action in the full agent:")
    print("  python src/main.py --mode quality")
    print("\nOr use hybrid mode (recommended):")
    print("  python src/main.py --mode hybrid")
