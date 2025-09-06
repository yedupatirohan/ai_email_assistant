import re

def preprocess_emails(emails):
    processed = []
    for email in emails:
        email['body'] = re.sub(r'\s+', ' ', email['body']).strip()
        processed.append(email)
    return processed
