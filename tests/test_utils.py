"""Tests for utility functions."""

import pytest
from src.utils import (
    get_field,
    get_ordered_fields,
    get_field_index,
    get_last_user_message,
    should_show_field,
)


class TestGetField:
    def test_get_field_by_id(self):
        schema = {
            "fields": [
                {"id": "field1", "label": "Field 1"},
                {"id": "field2", "label": "Field 2"}
            ]
        }
        field = get_field("field1", schema)
        assert field is not None
        assert field["id"] == "field1"
    
    def test_get_field_not_found(self):
        schema = {"fields": [{"id": "field1"}]}
        field = get_field("nonexistent", schema)
        assert field is None
    
    def test_get_field_none_id(self):
        schema = {"fields": [{"id": "field1"}]}
        field = get_field(None, schema)
        assert field is None


class TestGetOrderedFields:
    def test_get_fields(self):
        schema = {
            "fields": [
                {"id": "field1"},
                {"id": "field2"}
            ]
        }
        fields = get_ordered_fields(schema)
        assert len(fields) == 2
        assert fields[0]["id"] == "field1"
    
    def test_get_fields_empty_schema(self):
        schema = {}
        fields = get_ordered_fields(schema)
        assert fields == []


class TestGetFieldIndex:
    def test_get_index_exists(self):
        fields = [
            {"id": "field1"},
            {"id": "field2"},
            {"id": "field3"}
        ]
        assert get_field_index("field2", fields) == 1
    
    def test_get_index_not_found(self):
        fields = [{"id": "field1"}]
        assert get_field_index("nonexistent", fields) == -1


class TestGetLastUserMessage:
    def test_get_message_from_dict(self):
        state = {
            "messages": [
                {"type": "ai", "content": "Hello"},
                {"type": "human", "content": "Hi there"}
            ]
        }
        message = get_last_user_message(state)
        assert message == "Hi there"
    
    def test_get_message_no_user_message(self):
        state = {
            "messages": [
                {"type": "ai", "content": "Hello"}
            ]
        }
        message = get_last_user_message(state)
        assert message == ""


class TestShouldShowField:
    def test_show_field_no_conditional(self):
        field = {"id": "field1", "label": "Field 1"}
        collected = {}
        assert should_show_field(field, collected) is True
    
    def test_show_field_conditional_equals(self):
        field = {
            "id": "field2",
            "conditional": {
                "depends_on": "field1",
                "condition": "equals",
                "value": "yes"
            }
        }
        collected = {
            "field1": {"value": "yes"}
        }
        assert should_show_field(field, collected) is True
    
    def test_show_field_conditional_not_met(self):
        field = {
            "id": "field2",
            "conditional": {
                "depends_on": "field1",
                "condition": "equals",
                "value": "yes"
            }
        }
        collected = {
            "field1": {"value": "no"}
        }
        assert should_show_field(field, collected) is False
    
    def test_show_field_conditional_missing_dependency(self):
        field = {
            "id": "field2",
            "conditional": {
                "depends_on": "field1",
                "condition": "equals",
                "value": "yes"
            }
        }
        collected = {}
        assert should_show_field(field, collected) is False

