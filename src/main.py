from email_client import fetch_latest_emails
from ollama_client import filter_email_with_llm
from dotenv import load_dotenv
import os
import sqlite3


def main():
    if not os.path.exists("data/emails.db"):
        conn = sqlite3.connect("data/emails.db")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE emails (
                id INTEGER PRIMARY KEY,
                subject TEXT,
                body TEXT,
                is_customer_request BOOLEAN,
                customer_name TEXT,
                urgency TEXT,
                summary TEXT
            )
        ''')
        conn.commit()
        conn.close()
    load_dotenv()
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    strato_emails = fetch_latest_emails(email_address, email_password, days =100)
    conn = sqlite3.connect("data/emails.db")
    cursor = conn.cursor()
    for mail in strato_emails:
        result = filter_email_with_llm(mail)
        if result.is_customer_request:
            cursor.execute('''
                INSERT OR IGNORE INTO emails (id, subject, body, is_customer_request, customer_name, urgency, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (int(mail['id']), mail['subject'], mail['body'], result.is_customer_request, result.customer_name, result.urgency, result.summary))
            
            print(f"Save to DB: {result.model_dump_json(indent=2)}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()