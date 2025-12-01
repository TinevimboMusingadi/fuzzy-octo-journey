"""Tests for validation logic."""

import pytest
from src.validation import (
    validate_value,
    validate_email,
    validate_phone,
    validate_number,
    validate_select,
    validate_text,
)


class TestEmailValidation:
    def test_valid_email(self):
        is_valid, errors = validate_email("test@example.com", {})
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_email(self):
        is_valid, errors = validate_email("not-an-email", {})
        assert not is_valid
        assert len(errors) > 0
    
    def test_email_with_subdomain(self):
        is_valid, errors = validate_email("user@mail.example.com", {})
        assert is_valid


class TestPhoneValidation:
    def test_valid_phone_10_digits(self):
        is_valid, errors = validate_phone("1234567890", {})
        assert is_valid
    
    def test_valid_phone_formatted(self):
        is_valid, errors = validate_phone("(123) 456-7890", {})
        assert is_valid
    
    def test_invalid_phone_short(self):
        is_valid, errors = validate_phone("123", {})
        assert not is_valid


class TestNumberValidation:
    def test_valid_number(self):
        is_valid, errors = validate_number(42, {})
        assert is_valid
    
    def test_number_with_min(self):
        validation = {"min": 10}
        is_valid, errors = validate_number(5, validation)
        assert not is_valid
        assert any("at least" in e for e in errors)
    
    def test_number_with_max(self):
        validation = {"max": 100}
        is_valid, errors = validate_number(150, validation)
        assert not is_valid
        assert any("at most" in e for e in errors)


class TestSelectValidation:
    def test_valid_select(self):
        options = ["option1", "option2", "option3"]
        is_valid, errors = validate_select("option1", options)
        assert is_valid
    
    def test_invalid_select(self):
        options = ["option1", "option2"]
        is_valid, errors = validate_select("option99", options)
        assert not is_valid


class TestTextValidation:
    def test_valid_text(self):
        is_valid, errors = validate_text("Hello world", {})
        assert is_valid
    
    def test_text_min_length(self):
        validation = {"min_length": 10}
        is_valid, errors = validate_text("short", validation)
        assert not is_valid
    
    def test_text_max_length(self):
        validation = {"max_length": 5}
        is_valid, errors = validate_text("too long text", validation)
        assert not is_valid


class TestValidateValue:
    def test_required_field_empty(self):
        field = {
            "field_type": "text",
            "required": True
        }
        result = validate_value("", field)
        assert not result["valid"]
        assert "required" in result["errors"][0].lower()
    
    def test_optional_field_empty(self):
        field = {
            "field_type": "text",
            "required": False
        }
        result = validate_value("", field)
        assert result["valid"]
    
    def test_valid_email_field(self):
        field = {
            "field_type": "email",
            "required": True
        }
        result = validate_value("test@example.com", field)
        assert result["valid"]

