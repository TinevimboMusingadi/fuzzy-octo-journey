"""Tests for mode-specific implementations."""

import pytest
from src.modes import (
    ask_speed,
    process_speed,
    extract_email,
    extract_phone,
    extract_boolean,
    extract_select,
    annotate_speed,
    clarify_speed,
)
from src.config import AgentConfig


class TestAskSpeed:
    def test_text_field(self):
        field = {"field_type": "text", "label": "Name"}
        question = ask_speed(field, {})
        assert "Name" in question
    
    def test_email_field(self):
        field = {"field_type": "email", "label": "Email"}
        question = ask_speed(field, {})
        assert "Email" in question
        assert "example.com" in question
    
    def test_select_field(self):
        field = {
            "field_type": "select",
            "label": "Country",
            "options": ["USA", "Canada", "Mexico"]
        }
        question = ask_speed(field, {})
        assert "Country" in question
        assert "USA" in question or "Canada" in question


class TestExtractEmail:
    def test_extract_email_simple(self):
        result = extract_email("My email is test@example.com", {})
        assert result == "test@example.com"
    
    def test_extract_email_no_match(self):
        result = extract_email("No email here", {})
        assert result == "No email here"


class TestExtractPhone:
    def test_extract_phone_10_digits(self):
        result = extract_phone("Call me at 1234567890", {})
        assert "123" in result
        assert "456" in result
        assert "7890" in result
    
    def test_extract_phone_formatted(self):
        result = extract_phone("(555) 123-4567", {})
        assert "555" in result


class TestExtractBoolean:
    def test_extract_boolean_yes(self):
        assert extract_boolean("yes", {}) is True
        assert extract_boolean("Y", {}) is True
        assert extract_boolean("yeah", {}) is True
    
    def test_extract_boolean_no(self):
        assert extract_boolean("no", {}) is False
        assert extract_boolean("N", {}) is False
        assert extract_boolean("nope", {}) is False
    
    def test_extract_boolean_ambiguous(self):
        assert extract_boolean("maybe", {}) is None


class TestExtractSelect:
    def test_extract_select_exact_match(self):
        field = {"options": ["Option A", "Option B"]}
        result = extract_select("Option A", field)
        assert result == "Option A"
    
    def test_extract_select_fuzzy_match(self):
        field = {"options": ["United States", "Canada"]}
        result = extract_select("usa", field)
        assert "United States" in result or result == "usa"


class TestProcessSpeed:
    def test_process_text(self):
        field = {"field_type": "text"}
        result = process_speed("  Hello World  ", field)
        assert result["value"] == "Hello World"
        assert result["extraction_method"] == "regex"
    
    def test_process_email(self):
        field = {"field_type": "email"}
        result = process_speed("Contact me at user@example.com", field)
        assert result["value"] == "user@example.com"
        assert result["confidence"] == 1.0
    
    def test_process_boolean(self):
        field = {"field_type": "boolean"}
        result = process_speed("yes", field)
        assert result["value"] is True


class TestAnnotateSpeed:
    def test_annotate_uncertainty(self):
        notes = annotate_speed("I think it's around 100")
        assert any("uncertainty" in note.lower() for note in notes)
    
    def test_annotate_conditional(self):
        notes = annotate_speed("If it's available, I'll take it")
        assert any("conditional" in note.lower() for note in notes)
    
    def test_annotate_time_sensitive(self):
        notes = annotate_speed("Currently I'm working there")
        assert any("time-sensitive" in note.lower() for note in notes)
    
    def test_annotate_external_reference(self):
        notes = annotate_speed("See attached document")
        assert any("external" in note.lower() or "document" in note.lower() for note in notes)


class TestClarifySpeed:
    def test_clarify_email_error(self):
        field = {"field_type": "email", "label": "Email"}
        errors = ["Please provide a valid email address"]
        message = clarify_speed(field, errors, 1)
        assert "email" in message.lower()
    
    def test_clarify_required_error(self):
        field = {"field_type": "text", "label": "Name"}
        errors = ["This field is required"]
        message = clarify_speed(field, errors, 1)
        assert "required" in message.lower()
        assert "Name" in message

