def generate_reply(email):
    body = email['body']
    sentiment = email['sentiment']
    if sentiment == "Negative":
        tone = "We’re sorry to hear about your issue. We’ll work on resolving this immediately."
    elif sentiment == "Positive":
        tone = "Thank you for reaching out with your feedback."
    else:
        tone = "Thank you for contacting us."
    reply = f"Hello {email['sender']},\n\n{tone}\n\nRegarding your query: {email['subject']}\nWe’ll get back with more details soon.\n\nBest regards,\nSupport Team"
    return reply
