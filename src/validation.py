"""Validation logic for form fields."""

import re
from typing import Dict, Any, Tuple


def validate_value(value: Any, field: Dict[str, Any]) -> Dict[str, Any]:
    """Validate extracted value against field requirements."""
    errors = []
    field_type = field.get("field_type", "text")
    required = field.get("required", True)
    validation = field.get("validation", {})
    
    # Required check
    if required and not value:
        return {"valid": False, "errors": ["This field is required"]}
    
    if not required and not value:
        return {"valid": True, "errors": []}
    
    # Type-specific validation
    validators = {
        "email": validate_email,
        "phone": validate_phone,
        "date": validate_date,
        "number": lambda v, f: validate_number(v, validation),
        "select": lambda v, f: validate_select(v, f.get("options", [])),
        "boolean": lambda v, f: (True, []) if isinstance(v, bool) else (False, ["Must be yes or no"]),
        "text": lambda v, f: validate_text(v, validation),
        "address": lambda v, f: validate_text(v, {"min_length": 10}),
    }
    
    is_valid, type_errors = validators.get(field_type, lambda v, f: (True, []))(value, field)
    errors.extend(type_errors)
    
    return {"valid": len(errors) == 0, "errors": errors}


def validate_email(value: Any, field: Dict[str, Any]) -> Tuple[bool, list]:
    """Validate email format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    if re.match(pattern, str(value)):
        return True, []
    return False, ["Please provide a valid email address"]


def validate_phone(value: Any, field: Dict[str, Any]) -> Tuple[bool, list]:
    """Validate phone number format."""
    digits = re.sub(r'\D', '', str(value))
    if len(digits) >= 10:
        return True, []
    return False, ["Please provide a 10-digit phone number"]


def validate_date(value: Any, field: Dict[str, Any]) -> Tuple[bool, list]:
    """Validate date format."""
    # Basic check - can be enhanced with dateutil
    if isinstance(value, str) and len(value) > 0:
        return True, []
    return False, ["Please provide a valid date"]


def validate_number(value: Any, validation: Dict[str, Any]) -> Tuple[bool, list]:
    """Validate number with optional min/max constraints."""
    try:
        num = float(value)
        errors = []
        
        if "min" in validation and num < validation["min"]:
            errors.append(f"Value must be at least {validation['min']}")
        
        if "max" in validation and num > validation["max"]:
            errors.append(f"Value must be at most {validation['max']}")
        
        return len(errors) == 0, errors
    except (ValueError, TypeError):
        return False, ["Please provide a numeric value"]


def validate_select(value: Any, options: list) -> Tuple[bool, list]:
    """Validate select option."""
    if value in options:
        return True, []
    return False, [f"Please choose from: {', '.join(options)}"]


def validate_text(value: Any, validation: Dict[str, Any]) -> Tuple[bool, list]:
    """Validate text with optional length constraints."""
    if not isinstance(value, str):
        return False, ["Please provide text"]
    
    errors = []
    
    if "min_length" in validation and len(value) < validation["min_length"]:
        errors.append(f"Text must be at least {validation['min_length']} characters")
    
    if "max_length" in validation and len(value) > validation["max_length"]:
        errors.append(f"Text must be at most {validation['max_length']} characters")
    
    return len(errors) == 0, errors

