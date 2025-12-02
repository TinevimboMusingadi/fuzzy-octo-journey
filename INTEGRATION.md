# Output Integration Guide

This guide explains how to integrate the collected form data with your systems.

## Built-in Output Handlers

The agent includes several output handlers in `src/output_handlers.py`:

### 1. JSON Output (Default)
Saves each submission as a separate JSON file with timestamp.

```python
from src.output_handlers import JSONOutputHandler

handler = JSONOutputHandler(output_dir="output")
path = handler.save(collected_fields, metadata={"form_id": "contact_form"})
```

**Output:** `output/form_submission_20231203_142530.json`

### 2. CSV Output
Appends submissions to a single CSV file for easy analysis.

```python
from src.output_handlers import CSVOutputHandler

handler = CSVOutputHandler(output_file="output/submissions.csv")
path = handler.save(collected_fields)
```

### 3. Webhook Integration
Send data to an external API endpoint.

```python
from src.output_handlers import WebhookOutputHandler

handler = WebhookOutputHandler(webhook_url="https://your-api.com/webhook")
result = handler.save(collected_fields, metadata={"source": "intake_form"})
```

**Example Payload:**
```json
{
  "timestamp": "2023-12-03T14:25:30.123456",
  "data": {
    "name": {"value": "John Doe", "raw": "John Doe", "notes": []},
    "email": {"value": "john@example.com", "raw": "john@example.com", "notes": []}
  },
  "metadata": {"source": "intake_form"}
}
```

### 4. Database Storage
Save to SQLite database (easily adaptable to PostgreSQL/MySQL).

```python
from src.output_handlers import DatabaseOutputHandler

handler = DatabaseOutputHandler(db_path="output/submissions.db")
result = handler.save(collected_fields)
```

## Custom Integration Examples

### Example 1: Send Email Notification

```python
import smtplib
from email.mime.text import MIMEText

def send_email_notification(collected_fields):
    msg = MIMEText(f"New form submission:\n\n{json.dumps(collected_fields, indent=2)}")
    msg['Subject'] = 'New Form Submission'
    msg['From'] = 'noreply@yourcompany.com'
    msg['To'] = 'admin@yourcompany.com'
    
    with smtplib.SMTP('localhost') as server:
        server.send_message(msg)
```

### Example 2: CRM Integration (Salesforce, HubSpot, etc.)

```python
from src.output_handlers import OutputHandler
import requests

class CRMOutputHandler(OutputHandler):
    def __init__(self, api_key: str, crm_url: str):
        self.api_key = api_key
        self.crm_url = crm_url
    
    def save(self, data, metadata=None):
        # Transform to CRM format
        crm_contact = {
            "firstName": data.get("name", {}).get("value", "").split()[0],
            "lastName": " ".join(data.get("name", {}).get("value", "").split()[1:]),
            "email": data.get("email", {}).get("value"),
            "phone": data.get("phone", {}).get("value"),
        }
        
        response = requests.post(
            f"{self.crm_url}/contacts",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=crm_contact
        )
        return f"Created contact ID: {response.json()['id']}"
```

### Example 3: Google Sheets Integration

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleSheetsHandler(OutputHandler):
    def __init__(self, spreadsheet_id: str, credentials_file: str):
        creds = service_account.Credentials.from_service_account_file(credentials_file)
        self.service = build('sheets', 'v4', credentials=creds)
        self.spreadsheet_id = spreadsheet_id
    
    def save(self, data, metadata=None):
        values = [[
            datetime.now().isoformat(),
            data.get("name", {}).get("value"),
            data.get("email", {}).get("value"),
            data.get("phone", {}).get("value"),
        ]]
        
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range='Sheet1!A:D',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        
        return f"Added to Google Sheet: {self.spreadsheet_id}"
```

## Using Multiple Handlers

You can use multiple handlers simultaneously:

```python
# In main.py, after form completion:
handlers = [
    JSONOutputHandler(),  # Local backup
    CSVOutputHandler(),   # Analytics
    WebhookOutputHandler("https://your-api.com/webhook"),  # Real-time processing
    DatabaseOutputHandler()  # Persistent storage
]

for handler in handlers:
    try:
        result = handler.save(collected_fields, metadata={"form_id": "contact"})
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ Error with {handler.__class__.__name__}: {e}")
```

## Environment Configuration

Add to your `.env` file:

```bash
# Output Configuration
OUTPUT_DIR=output
WEBHOOK_URL=https://your-api.com/webhook
DATABASE_PATH=output/submissions.db

# CRM Integration (optional)
CRM_API_KEY=your_api_key
CRM_URL=https://api.yourcrm.com

# Email Notifications (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFY_EMAIL=admin@yourcompany.com
```

## Next Steps

1. Choose your output handler(s) based on your needs
2. Update `src/main.py` to use your preferred handlers
3. Test with sample data
4. Deploy to production

For webhook integration, ensure your endpoint can handle the JSON payload format shown above.
