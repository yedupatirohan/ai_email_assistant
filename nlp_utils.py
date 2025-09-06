from textblob import TextBlob

PRIORITY_KEYWORDS = ["urgent", "immediate", "critical", "cannot access", "blocked", "failure"]

def analyze_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0.2:
        return "Positive"
    elif analysis.sentiment.polarity < -0.2:
        return "Negative"
    else:
        return "Neutral"

def assign_priority(text):
    text_lower = text.lower()
    for kw in PRIORITY_KEYWORDS:
        if kw in text_lower:
            return "Urgent"
    return "Not urgent"
