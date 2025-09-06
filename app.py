import streamlit as st
import imaplib
import email
from email.header import decode_header
import openai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ----------------- CONFIG -----------------
KEYWORDS = ["Support", "Query", "Request", "Help"]
SENT_LOG_FILE = "sent_emails_log.txt"

# ----------------- FUNCTIONS -----------------
def get_secret(key, default=""):
    """Get secret from Streamlit secrets, fallback to default"""
    try:
        return st.secrets[key]
    except Exception:
        return default

openai.api_key = get_secret("OPENAI_API_KEY")

def connect_email(email_address, password, imap_server):
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        mail.select("inbox")
        return mail
    except imaplib.IMAP4.error:
        st.error("❌ Email login failed. Check your credentials or App Password.")
        st.stop()

def fetch_emails(mail):
    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    filtered_emails = []

    for eid in reversed(email_ids):
        res, msg = mail.fetch(eid, "(RFC822)")
        for response in msg:
            if isinstance(response, tuple):
                msg_obj = email.message_from_bytes(response[1])
                subject, encoding = decode_header(msg_obj["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                from_ = msg_obj.get("From")
                date_ = msg_obj.get("Date")

                body = ""
                if msg_obj.is_multipart():
                    for part in msg_obj.walk():
                        ctype = part.get_content_type()
                        cdispo = str(part.get("Content-Disposition"))
                        if ctype == "text/plain" and "attachment" not in cdispo:
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg_obj.get_payload(decode=True).decode()

                if any(keyword.lower() in subject.lower() for keyword in KEYWORDS):
                    filtered_emails.append({
                        "from": from_,
                        "subject": subject,
                        "date": date_,
                        "body": body
                    })
    return filtered_emails

def prioritize_email(email_body):
    urgent_keywords = ["urgent", "immediately", "asap", "critical"]
    if any(word in email_body.lower() for word in urgent_keywords):
        return "High"
    return "Normal"

def generate_response(email_body):
    prompt = f"Draft a professional, polite response to the following email:\n\n{email_body}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {e}"

def send_email(sender_email, password, to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        smtp_server = "smtp.gmail.com" if "gmail" in sender_email else "smtp.office365.com"
        smtp_port = 587

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()

        with open(SENT_LOG_FILE, "a") as f:
            f.write(f"{datetime.now()} | To: {to_email} | Subject: {subject}\n")
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False

# ----------------- STREAMLIT UI -----------------
st.title("📧 AI-Powered Email Communication Assistant")

st.header("Email Login Settings")
email_address = st.text_input("Email Address", value=get_secret("EMAIL_ADDRESS"))
password = st.text_input("App Password", type="password", value=get_secret("EMAIL_PASSWORD"))
imap_server = st.text_input("IMAP Server", value="imap.gmail.com")

if st.button("Connect & Fetch Emails"):
    if not email_address or not password:
        st.warning("Please enter both email and password.")
        st.stop()

    st.info("Fetching emails...")
    mail = connect_email(email_address, password, imap_server)
    emails = fetch_emails(mail)

    if emails:
        for em in emails:
            em['priority'] = prioritize_email(em['body'])
        emails = sorted(emails, key=lambda x: 0 if x['priority']=="High" else 1)

        for idx, em in enumerate(emails):
            if em['priority'] == "High":
                st.markdown(f"<p style='color:red;font-weight:bold'>{idx+1}. {em['subject']} (High Priority)</p>", unsafe_allow_html=True)
            else:
                st.subheader(f"{idx+1}. {em['subject']}")

            st.write(f"**From:** {em['from']}")
            st.write(f"**Date:** {em['date']}")
            st.write(f"**Body:** {em['body'][:300]}...")

            response = generate_response(em["body"])
            user_response = st.text_area(f"AI Response for {idx+1}", response, height=150)

            if st.button(f"Send Response to {em['from']}", key=idx):
                success = send_email(email_address, password, em['from'], f"Re: {em['subject']}", user_response)
                if success:
                    st.success(f"✅ Response sent to {em['from']}")

            st.markdown("---")
    else:
        st.warning("No emails matched the filter keywords.")
