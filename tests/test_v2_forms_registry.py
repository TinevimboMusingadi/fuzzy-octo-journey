from src.v2.forms_registry import (
    get_form_schema,
    EMPLOYMENT_ONBOARDING_SCHEMA,
    RENTAL_APPLICATION_SCHEMA,
    TAX_1040_MVP_SCHEMA,
    HEALTHCARE_INTAKE_SCHEMA,
)


def test_get_form_schema_known_ids():
    assert get_form_schema("employment_onboarding") == EMPLOYMENT_ONBOARDING_SCHEMA
    assert get_form_schema("rental_application") == RENTAL_APPLICATION_SCHEMA
    assert get_form_schema("tax_1040_mvp") == TAX_1040_MVP_SCHEMA
    assert get_form_schema("healthcare_intake") == HEALTHCARE_INTAKE_SCHEMA


def test_get_form_schema_unknown_id():
    assert get_form_schema("unknown_form_id") is None


def test_schemas_have_fields_and_ids():
    for schema in [
        EMPLOYMENT_ONBOARDING_SCHEMA,
        RENTAL_APPLICATION_SCHEMA,
        TAX_1040_MVP_SCHEMA,
        HEALTHCARE_INTAKE_SCHEMA,
    ]:
        fields = schema.get("fields")
        assert isinstance(fields, list) and fields, "schema must have non-empty fields"
        for field in fields:
            assert "id" in field
            assert "field_type" in field
            assert "label" in field


