---
title: Pre-Built Form Schemas (V2.0)
overview: Draft schemas for employment, housing, tax, and healthcare intake forms for the Dynamic Intake Form Agent.
---

## Overview

This document defines **pre-built form schemas** for V2.0 that can be loaded server‑side and passed into the existing intake graph via the `form_schema` field in the `FormState`.

Each schema follows the current structure:

```json
{
  "fields": [
    {
      "id": "unique_field_id",
      "field_type": "text | email | phone | date | number | boolean | select | address",
      "label": "User‑visible label",
      "description": "Short helper text",
      "required": true,
      "options": ["for", "select", "fields"],
      "validation": {
        "min": 0,
        "max": 100,
        "min_length": 0,
        "max_length": 255
      }
    }
  ]
}
```

The existing `modes.py` and `validation.py` already understand these field types and validation keys.

---

## 1. Employment / Onboarding Bundle

This bundle groups three logical forms:

- Form I‑9 (eligibility)
- Form W‑4 (tax withholding)
- Direct Deposit Authorization

In practice this can be a **single schema** with grouped sections or three separate schemas; below we model it as **one combined schema** with `id` prefixes.

### 1.1 Form I‑9 (Employment Eligibility Verification)

Key goals:

- Capture **citizenship status**
- Capture **document identifiers** (passport, driver’s license, SSN)
- Capture relevant **expiration dates**

Example schema fragment:

```json
{
  "fields": [
    {
      "id": "i9_citizenship_status",
      "field_type": "select",
      "label": "Citizenship status",
      "description": "Select the option that best describes your current immigration status.",
      "required": true,
      "options": [
        "U.S. citizen",
        "Noncitizen national of the U.S.",
        "Lawful permanent resident",
        "Alien authorized to work"
      ]
    },
    {
      "id": "i9_document_type",
      "field_type": "select",
      "label": "Identity document type",
      "description": "Which document are you providing for I‑9 verification?",
      "required": true,
      "options": [
        "U.S. passport",
        "Driver’s license and Social Security card",
        "Permanent Resident Card (Green Card)",
        "Other DHS‑authorized document"
      ]
    },
    {
      "id": "i9_passport_number",
      "field_type": "text",
      "label": "Passport number",
      "description": "Enter your passport number, if you are using a passport as your I‑9 document.",
      "required": false,
      "validation": {
        "max_length": 20
      }
    },
    {
      "id": "i9_driver_license_number",
      "field_type": "text",
      "label": "Driver’s license number",
      "description": "Enter your driver’s license number if applicable.",
      "required": false,
      "validation": {
        "max_length": 25
      }
    },
    {
      "id": "i9_ssn",
      "field_type": "text",
      "label": "Social Security Number",
      "description": "Enter your 9‑digit SSN (no dashes needed).",
      "required": false,
      "validation": {
        "min_length": 9,
        "max_length": 11
      }
    },
    {
      "id": "i9_document_expiration",
      "field_type": "date",
      "label": "Document expiration date",
      "description": "Expiration date for the document you are using for I‑9 verification.",
      "required": false
    }
  ]
}
```

### 1.2 Form W‑4 (Employee’s Withholding Certificate)

Key goals:

- Filing status
- Dependents
- Any extra withholding

Example schema fragment (can be appended to the same `fields` list):

```json
[
  {
    "id": "w4_filing_status",
    "field_type": "select",
    "label": "Filing status",
    "description": "Your expected filing status on your federal tax return.",
    "required": true,
    "options": [
      "Single or Married filing separately",
      "Married filing jointly",
      "Head of household"
    ]
  },
  {
    "id": "w4_dependents_under_17",
    "field_type": "number",
    "label": "Number of qualifying children under age 17",
    "description": "Enter how many children under age 17 you can claim.",
    "required": false,
    "validation": {
      "min": 0,
      "max": 20
    }
  },
  {
    "id": "w4_other_dependents",
    "field_type": "number",
    "label": "Number of other dependents",
    "description": "Other dependents who are not qualifying children under 17.",
    "required": false,
    "validation": {
      "min": 0,
      "max": 20
    }
  },
  {
    "id": "w4_extra_withholding",
    "field_type": "number",
    "label": "Extra amount to withhold each paycheck",
    "description": "Optional additional dollar amount to withhold from each paycheck.",
    "required": false,
    "validation": {
      "min": 0
    }
  }
]
```

### 1.3 Direct Deposit Authorization

Key goals:

- Bank name
- Account type
- Routing and account numbers

Example schema fragment:

```json
[
  {
    "id": "dd_bank_name",
    "field_type": "text",
    "label": "Bank name",
    "description": "Name of your bank (e.g., Chase, Bank of America).",
    "required": true,
    "validation": {
      "min_length": 2,
      "max_length": 80
    }
  },
  {
    "id": "dd_account_type",
    "field_type": "select",
    "label": "Account type",
    "description": "Type of bank account for direct deposit.",
    "required": true,
    "options": [
      "Checking",
      "Savings"
    ]
  },
  {
    "id": "dd_routing_number",
    "field_type": "text",
    "label": "Routing number",
    "description": "9‑digit routing number from the bottom of your check.",
    "required": true,
    "validation": {
      "min_length": 9,
      "max_length": 9
    }
  },
  {
    "id": "dd_account_number",
    "field_type": "text",
    "label": "Account number",
    "description": "Your bank account number.",
    "required": true,
    "validation": {
      "min_length": 4,
      "max_length": 20
    }
  }
]
```

---

## 2. Housing – Rental Application

Key goals:

- Residential history
- Employment verification
- References

### Example schema

```json
{
  "fields": [
    {
      "id": "rent_current_address",
      "field_type": "address",
      "label": "Current address",
      "description": "Your current residential address.",
      "required": true
    },
    {
      "id": "rent_current_landlord_name",
      "field_type": "text",
      "label": "Current landlord name",
      "description": "Full name of your current landlord or property manager.",
      "required": false,
      "validation": {
        "max_length": 120
      }
    },
    {
      "id": "rent_current_landlord_phone",
      "field_type": "phone",
      "label": "Current landlord phone",
      "description": "Phone number for your current landlord or property manager.",
      "required": false
    },
    {
      "id": "rent_previous_address",
      "field_type": "address",
      "label": "Previous address",
      "description": "Your previous residential address (if within the last 3–5 years).",
      "required": false
    },
    {
      "id": "rent_previous_landlord_name",
      "field_type": "text",
      "label": "Previous landlord name",
      "description": "Full name of your previous landlord.",
      "required": false
    },
    {
      "id": "rent_previous_landlord_phone",
      "field_type": "phone",
      "label": "Previous landlord phone",
      "description": "Phone number for your previous landlord.",
      "required": false
    },
    {
      "id": "rent_employer_name",
      "field_type": "text",
      "label": "Current employer",
      "description": "Name of your current employer.",
      "required": true
    },
    {
      "id": "rent_job_title",
      "field_type": "text",
      "label": "Job title",
      "description": "Your job title with your current employer.",
      "required": true
    },
    {
      "id": "rent_hr_contact_phone",
      "field_type": "phone",
      "label": "HR or supervisor phone",
      "description": "Contact number for HR or your supervisor to verify employment.",
      "required": false
    },
    {
      "id": "rent_gross_monthly_income",
      "field_type": "number",
      "label": "Gross monthly income",
      "description": "Your approximate gross monthly income (before taxes).",
      "required": true,
      "validation": {
        "min": 0
      }
    },
    {
      "id": "rent_reference_1_name",
      "field_type": "text",
      "label": "Reference 1 name",
      "description": "Name of a personal reference (non‑relative).",
      "required": false
    },
    {
      "id": "rent_reference_1_phone",
      "field_type": "phone",
      "label": "Reference 1 phone",
      "description": "Phone number for your personal reference.",
      "required": false
    },
    {
      "id": "rent_reference_1_email",
      "field_type": "email",
      "label": "Reference 1 email",
      "description": "Email address for your personal reference.",
      "required": false
    }
  ]
}
```

---

## 3. Government & Taxes – Form 1040 (Simplified)

Key goals (for an MVP helper, not full tax prep):

- Total income
- Standard vs. itemized deduction choice
- Refund method (esp. routing/account for direct deposit)

### Example schema (simplified)

```json
{
  "fields": [
    {
      "id": "f1040_total_wage_income",
      "field_type": "number",
      "label": "Total wage income",
      "description": "Approximate total wages, salaries, and tips for the year.",
      "required": true,
      "validation": {
        "min": 0
      }
    },
    {
      "id": "f1040_other_income",
      "field_type": "number",
      "label": "Other taxable income",
      "description": "Approximate amount of other taxable income (interest, dividends, etc.).",
      "required": false,
      "validation": {
        "min": 0
      }
    },
    {
      "id": "f1040_deduction_type",
      "field_type": "select",
      "label": "Deduction type",
      "description": "Whether you expect to claim the standard deduction or itemize.",
      "required": true,
      "options": [
        "Standard deduction",
        "Itemized deductions"
      ]
    },
    {
      "id": "f1040_refund_method",
      "field_type": "select",
      "label": "Refund method",
      "description": "How you want to receive any refund.",
      "required": true,
      "options": [
        "Direct deposit",
        "Paper check"
      ]
    },
    {
      "id": "f1040_refund_routing",
      "field_type": "text",
      "label": "Refund routing number",
      "description": "Routing number for refund direct deposit (if applicable).",
      "required": false,
      "validation": {
        "min_length": 9,
        "max_length": 9
      }
    },
    {
      "id": "f1040_refund_account",
      "field_type": "text",
      "label": "Refund account number",
      "description": "Account number for refund direct deposit (if applicable).",
      "required": false,
      "validation": {
        "min_length": 4,
        "max_length": 20
      }
    }
  ]
}
```

---

## 4. Healthcare – Patient Intake

Focus: **HIPAA release** and **insurance card** information.

### Example schema

```json
{
  "fields": [
    {
      "id": "hipaa_release_consent",
      "field_type": "boolean",
      "label": "HIPAA release consent",
      "description": "Do you authorize this provider to share your medical information with the people you specify?",
      "required": true
    },
    {
      "id": "hipaa_authorized_contacts",
      "field_type": "text",
      "label": "Authorized contacts",
      "description": "List the names and relationships of people you authorize to receive your medical information (e.g., spouse, parent).",
      "required": false,
      "validation": {
        "max_length": 500
      }
    },
    {
      "id": "hipaa_signature",
      "field_type": "text",
      "label": "Electronic signature",
      "description": "Type your full legal name as your electronic signature.",
      "required": true
    },
    {
      "id": "hipaa_signature_date",
      "field_type": "date",
      "label": "Signature date",
      "description": "Date you are signing this HIPAA release.",
      "required": true
    },
    {
      "id": "insurance_member_id",
      "field_type": "text",
      "label": "Insurance member ID",
      "description": "Member ID from your insurance card.",
      "required": true,
      "validation": {
        "max_length": 40
      }
    },
    {
      "id": "insurance_group_number",
      "field_type": "text",
      "label": "Insurance group number",
      "description": "Group number from your insurance card, if applicable.",
      "required": false,
      "validation": {
        "max_length": 40
      }
    },
    {
      "id": "insurance_provider_phone",
      "field_type": "phone",
      "label": "Insurance provider phone",
      "description": "Customer service or provider phone number on the back of your card.",
      "required": false
    },
    {
      "id": "insurance_policy_holder_name",
      "field_type": "text",
      "label": "Policy holder name",
      "description": "Name of the policy holder, if different from the patient.",
      "required": false
    }
  ]
}
```

---

## Next Steps

- Decide whether each of the above should be:
  - Separate form schemas (`employment_onboarding.json`, `rental_application.json`, etc.), or
  - A single schema with **section IDs** and conditional display logic.
- Implement loader utilities (e.g., `load_form_schema(form_id)`) and wire them into the server‑side selection flow described in the API design document.


