"""Output handlers for collected form data."""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class OutputHandler:
    """Base class for output handlers."""
    
    def save(self, data: Dict[str, Any], metadata: Optional[Dict] = None) -> str:
        """Save collected data. Returns path/identifier of saved data."""
        raise NotImplementedError


class JSONOutputHandler(OutputHandler):
    """Save data as JSON file."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def save(self, data: Dict[str, Any], metadata: Optional[Dict] = None) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"form_submission_{timestamp}.json"
        filepath = self.output_dir / filename
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "metadata": metadata or {}
        }
        
        with open(filepath, "w") as f:
            json.dump(output, f, indent=2, default=str)
        
        return str(filepath)


class CSVOutputHandler(OutputHandler):
    """Append data to CSV file."""
    
    def __init__(self, output_file: str = "output/submissions.csv"):
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(exist_ok=True)
    
    def save(self, data: Dict[str, Any], metadata: Optional[Dict] = None) -> str:
        # Flatten the data
        flat_data = {}
        for field_id, field_data in data.items():
            flat_data[field_id] = field_data.get("value", "")
            if field_data.get("notes"):
                flat_data[f"{field_id}_notes"] = "; ".join(field_data["notes"])
        
        flat_data["timestamp"] = datetime.now().isoformat()
        
        # Check if file exists to determine if we need headers
        file_exists = self.output_file.exists()
        
        with open(self.output_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=flat_data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(flat_data)
        
        return str(self.output_file)


class WebhookOutputHandler(OutputHandler):
    """Send data to a webhook URL."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def save(self, data: Dict[str, Any], metadata: Optional[Dict] = None) -> str:
        import requests
        
        payload = {
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "metadata": metadata or {}
        }
        
        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        return f"Sent to {self.webhook_url} (Status: {response.status_code})"


class DatabaseOutputHandler(OutputHandler):
    """Save data to a database (example with SQLite)."""
    
    def __init__(self, db_path: str = "output/submissions.db"):
        import sqlite3
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                data TEXT NOT NULL,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def save(self, data: Dict[str, Any], metadata: Optional[Dict] = None) -> str:
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO submissions (timestamp, data, metadata) VALUES (?, ?, ?)",
            (
                datetime.now().isoformat(),
                json.dumps(data, default=str),
                json.dumps(metadata or {}, default=str)
            )
        )
        
        submission_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return f"Saved to database with ID: {submission_id}"
