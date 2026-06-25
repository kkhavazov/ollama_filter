import imaplib
import email
from datetime import datetime, timedelta
from email.header import decode_header

def fetch_latest_emails(address, password, days):
    # Connect to Strato IMAP
    mail_conn = imaplib.IMAP4_SSL("imap.strato.de", 993)
    mail_conn.login(address, password)
    mail_conn.select("inbox")
    

    yesterday = datetime.now() - timedelta(days=days)
    imap_date_format = yesterday.strftime("%d-%b-%Y")
    
    status, messages = mail_conn.search(None, f'(SINCE "{imap_date_format}")')

    email_ids = messages[0].split()
    print(f"Found {len(email_ids)} emails since {imap_date_format}.")
    
    fetched_emails = []

    for e_id in email_ids:
        status, msg_data = mail_conn.fetch(e_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode(errors="ignore")
                
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")
                
                fetched_emails.append({"id": e_id,"subject": subject, "body": body})
                
    mail_conn.logout()
    return fetched_emails

def move_email_to_folder(mail, email_id, target_folder="Customers"):
    mail.create(target_folder)
    result = mail.copy(email_id, target_folder)
    if result[0] == 'OK':
        mail.store(email_id, '+FLAGS', '\\Deleted')