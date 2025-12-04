"""Registry of pre-built V2.0 form schemas.

These schemas are Python representations of the forms described in
`docs/v2/forms.md`. They are intentionally minimal for now and can be
expanded over time.
"""

from typing import Dict, Any, Optional


Schema = Dict[str, Any]


EMPLOYMENT_ONBOARDING_SCHEMA: Schema = {
    "id": "employment_onboarding",
    "fields": [
        # I-9 core fields (simplified)
        {
            "id": "i9_citizenship_status",
            "field_type": "select",
            "label": "Citizenship status",
            "description": "Select the option that best describes your current immigration status.",
            "required": True,
            "options": [
                "U.S. citizen",
                "Noncitizen national of the U.S.",
                "Lawful permanent resident",
                "Alien authorized to work",
            ],
        },
        {
            "id": "i9_document_type",
            "field_type": "select",
            "label": "Identity document type",
            "description": "Which document are you providing for I-9 verification?",
            "required": True,
            "options": [
                "U.S. passport",
                "Driver’s license and Social Security card",
                "Permanent Resident Card (Green Card)",
                "Other DHS-authorized document",
            ],
        },
        {
            "id": "i9_ssn",
            "field_type": "text",
            "label": "Social Security Number",
            "description": "Enter your 9-digit SSN (no dashes needed).",
            "required": False,
            "validation": {
                "min_length": 9,
                "max_length": 11,
            },
        },
        # W-4 core fields (simplified)
        {
            "id": "w4_filing_status",
            "field_type": "select",
            "label": "Filing status",
            "description": "Your expected filing status on your federal tax return.",
            "required": True,
            "options": [
                "Single or Married filing separately",
                "Married filing jointly",
                "Head of household",
            ],
        },
        {
            "id": "w4_dependents_under_17",
            "field_type": "number",
            "label": "Number of qualifying children under age 17",
            "description": "Enter how many children under age 17 you can claim.",
            "required": False,
            "validation": {
                "min": 0,
                "max": 20,
            },
        },
        {
            "id": "w4_other_dependents",
            "field_type": "number",
            "label": "Number of other dependents",
            "description": "Other dependents who are not qualifying children under 17.",
            "required": False,
            "validation": {
                "min": 0,
                "max": 20,
            },
        },
        # Direct deposit core fields
        {
            "id": "dd_bank_name",
            "field_type": "text",
            "label": "Bank name",
            "description": "Name of your bank (e.g., Chase, Bank of America).",
            "required": True,
            "validation": {
                "min_length": 2,
                "max_length": 80,
            },
        },
        {
            "id": "dd_account_type",
            "field_type": "select",
            "label": "Account type",
            "description": "Type of bank account for direct deposit.",
            "required": True,
            "options": [
                "Checking",
                "Savings",
            ],
        },
        {
            "id": "dd_routing_number",
            "field_type": "text",
            "label": "Routing number",
            "description": "9-digit routing number from the bottom of your check.",
            "required": True,
            "validation": {
                "min_length": 9,
                "max_length": 9,
            },
        },
        {
            "id": "dd_account_number",
            "field_type": "text",
            "label": "Account number",
            "description": "Your bank account number.",
            "required": True,
            "validation": {
                "min_length": 4,
                "max_length": 20,
            },
        },
    ],
}


RENTAL_APPLICATION_SCHEMA: Schema = {
    "id": "rental_application",
    "fields": [
        {
            "id": "rent_current_address",
            "field_type": "address",
            "label": "Current address",
            "description": "Your current residential address.",
            "required": True,
        },
        {
            "id": "rent_employer_name",
            "field_type": "text",
            "label": "Current employer",
            "description": "Name of your current employer.",
            "required": True,
        },
        {
            "id": "rent_job_title",
            "field_type": "text",
            "label": "Job title",
            "description": "Your job title with your current employer.",
            "required": True,
        },
        {
            "id": "rent_gross_monthly_income",
            "field_type": "number",
            "label": "Gross monthly income",
            "description": "Your approximate gross monthly income (before taxes).",
            "required": True,
            "validation": {
                "min": 0,
            },
        },
    ],
}


TAX_1040_MVP_SCHEMA: Schema = {
    "id": "tax_1040_mvp",
    "fields": [
        {
            "id": "f1040_total_wage_income",
            "field_type": "number",
            "label": "Total wage income",
            "description": "Approximate total wages, salaries, and tips for the year.",
            "required": True,
            "validation": {
                "min": 0,
            },
        },
        {
            "id": "f1040_other_income",
            "field_type": "number",
            "label": "Other taxable income",
            "description": "Approximate amount of other taxable income (interest, dividends, etc.).",
            "required": False,
            "validation": {
                "min": 0,
            },
        },
        {
            "id": "f1040_deduction_type",
            "field_type": "select",
            "label": "Deduction type",
            "description": "Whether you expect to claim the standard deduction or itemize.",
            "required": True,
            "options": [
                "Standard deduction",
                "Itemized deductions",
            ],
        },
        {
            "id": "f1040_refund_method",
            "field_type": "select",
            "label": "Refund method",
            "description": "How you want to receive any refund.",
            "required": True,
            "options": [
                "Direct deposit",
                "Paper check",
            ],
        },
        {
            "id": "f1040_refund_routing",
            "field_type": "text",
            "label": "Refund routing number",
            "description": "Routing number for refund direct deposit (if applicable).",
            "required": False,
            "validation": {
                "min_length": 9,
                "max_length": 9,
            },
        },
        {
            "id": "f1040_refund_account",
            "field_type": "text",
            "label": "Refund account number",
            "description": "Account number for refund direct deposit (if applicable).",
            "required": False,
            "validation": {
                "min_length": 4,
                "max_length": 20,
            },
        },
    ],
}


HEALTHCARE_INTAKE_SCHEMA: Schema = {
    "id": "healthcare_intake",
    "fields": [
        {
            "id": "hipaa_release_consent",
            "field_type": "boolean",
            "label": "HIPAA release consent",
            "description": "Do you authorize this provider to share your medical information with the people you specify?",
            "required": True,
        },
        {
            "id": "hipaa_authorized_contacts",
            "field_type": "text",
            "label": "Authorized contacts",
            "description": "List the names and relationships of people you authorize to receive your medical information (e.g., spouse, parent).",
            "required": False,
            "validation": {
                "max_length": 500,
            },
        },
        {
            "id": "hipaa_signature",
            "field_type": "text",
            "label": "Electronic signature",
            "description": "Type your full legal name as your electronic signature.",
            "required": True,
        },
        {
            "id": "hipaa_signature_date",
            "field_type": "date",
            "label": "Signature date",
            "description": "Date you are signing this HIPAA release.",
            "required": True,
        },
        {
            "id": "insurance_member_id",
            "field_type": "text",
            "label": "Insurance member ID",
            "description": "Member ID from your insurance card.",
            "required": True,
            "validation": {
                "max_length": 40,
            },
        },
        {
            "id": "insurance_group_number",
            "field_type": "text",
            "label": "Insurance group number",
            "description": "Group number from your insurance card, if applicable.",
            "required": False,
            "validation": {
                "max_length": 40,
            },
        },
        {
            "id": "insurance_provider_phone",
            "field_type": "phone",
            "label": "Insurance provider phone",
            "description": "Customer service or provider phone number on the back of your card.",
            "required": False,
        },
        {
            "id": "insurance_policy_holder_name",
            "field_type": "text",
            "label": "Policy holder name",
            "description": "Name of the policy holder, if different from the patient.",
            "required": False,
        },
    ],
}


FORM_REGISTRY: Dict[str, Schema] = {
    EMPLOYMENT_ONBOARDING_SCHEMA["id"]: EMPLOYMENT_ONBOARDING_SCHEMA,
    RENTAL_APPLICATION_SCHEMA["id"]: RENTAL_APPLICATION_SCHEMA,
    TAX_1040_MVP_SCHEMA["id"]: TAX_1040_MVP_SCHEMA,
    HEALTHCARE_INTAKE_SCHEMA["id"]: HEALTHCARE_INTAKE_SCHEMA,
}


def get_form_schema(form_id: str) -> Optional[Schema]:
    """Return a pre-built form schema by ID, or None if not found."""
    return FORM_REGISTRY.get(form_id)
