"""Mode-specific implementations (Speed vs Quality)."""

import re
import json
from typing import Dict, Any, Optional, Union
from dateutil import parser as date_parser

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from src.utils import summarize_context
from src.config import AgentConfig


# Initialize LLM (lazy loading)
_llm: Optional[BaseChatModel] = None


def get_llm(config: AgentConfig) -> BaseChatModel:
    """Get or create LLM instance."""
    global _llm
    if _llm is None:
        if config.llm_provider == "google":
            _llm = ChatGoogleGenerativeAI(
                model=config.llm_model,
                temperature=config.llm_temperature,
                google_api_key=config.google_api_key
            )
        else:
            _llm = ChatOpenAI(
                model=config.llm_model,
                temperature=config.llm_temperature
            )
    return _llm


# ==================== ASK NODE ====================

QUESTION_TEMPLATES = {
    "text": "What is your {label}?",
    "email": "What is your {label}? (e.g., name@example.com)",
    "phone": "What is your {label}? Please include area code.",
    "date": "What is your {label}? (e.g., MM/DD/YYYY)",
    "select": "What is your {label}?\n{options}",
    "boolean": "{label}? (Yes/No)",
    "number": "What is your {label}?",
    "address": "What is your {label}? Please include full address."
}


def format_options(options: list) -> str:
    """Format options for select fields."""
    if not options:
        return ""
    return "\n".join(f"- {opt}" for opt in options)


def ask_speed(field: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Speed mode: Template-based question generation."""
    template = QUESTION_TEMPLATES.get(
        field.get("field_type", "text"),
        "What is your {label}?"
    )
    
    return template.format(
        label=field.get("label", ""),
        description=field.get("description", ""),
        options=format_options(field.get("options", []))
    )


def ask_quality(field: Dict[str, Any], context: Dict[str, Any], config: AgentConfig) -> str:
    """Quality mode: LLM-generated contextual question."""
    llm = get_llm(config)
    
    prompt = f"""Generate a natural, conversational question to collect:

Field: {field.get('label', '')}
Type: {field.get('field_type', 'text')}
Description: {field.get('description', 'N/A')}
Options: {field.get('options', 'N/A')}

Previous responses: {summarize_context(context)}

Requirements:
- Sound natural and friendly
- Include format hints if helpful
- Reference previous answers if relevant
- Keep it concise (1-2 sentences)

Question:"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


# ==================== PROCESS NODE ====================

def extract_email(text: str, field: Dict[str, Any]) -> str:
    """Extract email from text."""
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return match.group(0) if match else text.strip()


def extract_phone(text: str, field: Dict[str, Any]) -> str:
    """Extract and normalize phone number."""
    digits = re.sub(r'\D', '', text)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return digits if len(digits) >= 10 else text.strip()


def extract_date(text: str, field: Dict[str, Any]) -> str:
    """Extract date from text."""
    try:
        parsed = date_parser.parse(text)
        return parsed.strftime("%Y-%m-%d")
    except:
        return text.strip()


def extract_number(text: str, field: Dict[str, Any]) -> float:
    """Extract number from text."""
    match = re.search(r'-?\d+\.?\d*', text)
    if match:
        try:
            return float(match.group(0))
        except:
            pass
    raise ValueError("No number found")


def extract_boolean(text: str, field: Dict[str, Any]) -> Optional[bool]:
    """Extract boolean from text."""
    text_lower = text.lower().strip()
    if text_lower in ["yes", "y", "yeah", "yep", "true", "1", "correct"]:
        return True
    if text_lower in ["no", "n", "nope", "false", "0", "incorrect"]:
        return False
    return None


def extract_select(text: str, field: Dict[str, Any]) -> str:
    """Extract select option with fuzzy matching."""
    options = field.get("options", [])
    text_lower = text.lower().strip()
    
    # Exact match
    for opt in options:
        if opt.lower() == text_lower:
            return opt
    
    # Fuzzy match
    for opt in options:
        if text_lower in opt.lower() or opt.lower() in text_lower:
            return opt
    
    return text.strip()


def process_speed(user_input: str, field: Dict[str, Any]) -> Dict[str, Any]:
    """Speed mode: Regex-based extraction."""
    field_type = field.get("field_type", "text")
    
    extractors = {
        "email": extract_email,
        "phone": extract_phone,
        "date": extract_date,
        "number": extract_number,
        "boolean": extract_boolean,
        "select": extract_select,
        "text": lambda x, f: x.strip(),
        "address": lambda x, f: x.strip()
    }
    
    extractor = extractors.get(field_type, lambda x, f: x.strip())
    
    try:
        value = extractor(user_input, field)
        return {
            "value": value,
            "raw": user_input,
            "confidence": 1.0 if value else 0.5,
            "extraction_method": "regex"
        }
    except Exception as e:
        return {
            "value": None,
            "raw": user_input,
            "confidence": 0.3,
            "extraction_method": "regex",
            "error": str(e)
        }


def process_quality(user_input: str, field: Dict[str, Any], config: AgentConfig) -> Dict[str, Any]:
    """Quality mode: LLM-based extraction."""
    llm = get_llm(config)
    
    prompt = f"""Extract the {field.get('field_type', 'text')} value from this response.

Field: {field.get('label', '')}
Type: {field.get('field_type', 'text')}
Options: {field.get('options', 'N/A')}
User said: "{user_input}"

Return JSON:
{{
    "value": <extracted value in correct type>,
    "confidence": <0.0-1.0>,
    "notes": [<any observations about ambiguity, uncertainty>]
}}

JSON:"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        result = json.loads(response.content)
        result["raw"] = user_input
        result["extraction_method"] = "llm"
        return result
    except Exception as e:
        # Fallback to speed mode
        return process_speed(user_input, field)


# ==================== VALIDATE NODE ====================

def verify_quality(
    collected: Dict[str, Any],
    field: Dict[str, Any],
    rule_result: Dict[str, Any],
    config: AgentConfig
) -> Dict[str, Any]:
    """Quality mode: Additional LLM verification."""
    if collected.get("confidence", 1.0) > 0.9:
        return rule_result
    
    llm = get_llm(config)
    
    prompt = f"""Verify this extracted value makes sense.

Field: {field.get('label', '')} ({field.get('field_type', 'text')})
User said: "{collected.get('raw', '')}"
Extracted: {collected.get('value', '')}

Does the extracted value accurately represent what the user meant?
Is there any ambiguity that should be clarified?

Return JSON:
{{
    "valid": true/false,
    "needs_clarification": true/false,
    "reason": "explanation if invalid or ambiguous"
}}

JSON:"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        verification = json.loads(response.content)
        
        if not verification.get("valid", True) or verification.get("needs_clarification", False):
            return {
                "valid": False,
                "errors": [verification.get("reason", "Please clarify your response")]
            }
    except:
        pass  # Fallback to rule result
    
    return rule_result


# ==================== CLARIFY NODE ====================

def clarify_speed(field: Dict[str, Any], errors: list, attempt: int) -> str:
    """Speed mode: Template-based clarification."""
    error_templates = {
        "email": "Please provide a valid email address (e.g., name@example.com)",
        "phone": "Please provide your phone number with area code (e.g., 555-123-4567)",
        "date": "Please provide a valid date (e.g., 01/15/2024 or January 15, 2024)",
        "required": f"The {field.get('label', 'field')} is required. Please provide a response.",
        "select": f"Please choose from: {', '.join(field.get('options', []))}",
        "number": "Please provide a numeric value",
        "default": f"Please provide a valid {field.get('label', 'value')}"
    }
    
    # Match error to template
    for key, template in error_templates.items():
        if any(key in e.lower() for e in errors):
            return template
    
    return error_templates["default"]


def clarify_quality(
    field: Dict[str, Any],
    errors: list,
    collected: Dict[str, Any],
    attempt: int,
    config: AgentConfig
) -> str:
    """Quality mode: LLM-generated clarification."""
    llm = get_llm(config)
    
    prompt = f"""Generate a helpful clarification request.

Field: {field.get('label', '')}
Type: {field.get('field_type', 'text')}
User said: "{collected.get('raw', '')}"
Validation errors: {errors}
Attempt: {attempt} of 3

Requirements:
- Be friendly and helpful, not robotic
- Explain what's wrong clearly
- Give a specific example of correct format
- If attempt > 1, try a different explanation approach
- Keep it concise

Clarification:"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


# ==================== ANNOTATE NODE ====================

def annotate_speed(raw_response: str) -> list:
    """Speed mode: Pattern-based annotation."""
    notes = []
    text = raw_response.lower()
    
    # Uncertainty detection
    uncertainty_patterns = [
        (r'\bi think\b', "Response contains uncertainty"),
        (r'\bmaybe\b', "Response contains uncertainty"),
        (r'\bapprox', "Approximate value provided"),
        (r'\baround\b', "Approximate value provided"),
        (r'\bnot sure\b', "Respondent expressed uncertainty"),
    ]
    
    for pattern, note in uncertainty_patterns:
        if re.search(pattern, text):
            notes.append(note)
            break
    
    # Conditional language
    if re.search(r'\b(if|unless|depending|when)\b', text):
        notes.append("Response contains conditional language")
    
    # Time-sensitive
    if re.search(r'\b(currently|right now|at the moment|as of)\b', text):
        notes.append("Response may be time-sensitive")
    
    # External references
    if re.search(r'\b(attached|see |refer to|document)\b', text):
        notes.append("References external document")
    
    return notes


def annotate_quality(collected: Dict[str, Any], state: Dict[str, Any], config: AgentConfig) -> list:
    """Quality mode: LLM-based annotation."""
    llm = get_llm(config)
    
    prompt = f"""Analyze this response for any notable observations.

Field: {state.get('current_field_id', 'unknown')}
User said: "{collected.get('raw', '')}"
Extracted value: {collected.get('value', '')}

Flag any of the following if present:
- Uncertainty or hedging language
- Conditional statements
- Time-sensitive information
- References to external documents
- Potential inconsistencies with previous answers
- Anything that might need follow-up

Previous answers: {summarize_context(state.get('collected_fields', {}))}

Return JSON array of notes (empty if nothing notable):
["note 1", "note 2"]

Notes:"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return json.loads(response.content)
    except:
        return []

