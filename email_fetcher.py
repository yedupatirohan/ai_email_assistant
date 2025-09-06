import imaplib
import email
from email.header import decode_header
import pandas as pd

# -------------------------
# Gmail/Outlook Email Fetcher (Stub)
# -------------------------

def fetch_emails_from_imap(username, password, imap_server="imap.gmail.com", folder="INBOX", limit=20):
    """
    Fetch latest emails via IMAP.
    Returns: DataFrame with sender, subject, body, sent_date
    """
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(username, password)
        mail.select(folder)

        # Search all emails
        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        email_ids = email_ids[-limit:]  # fetch only latest N

        data = []
        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            sender = msg.get("From")
            date = msg.get("Date")

            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            data.append({
                "sender": sender,
                "subject": subject,
                "body": body,
                "sent_date": date
            })

        mail.logout()
        return pd.DataFrame(data)

    except Exception as e:
        print("❌ Error fetching emails:", e)
        return pd.DataFrame(columns=["sender", "subject", "body", "sent_date"])
