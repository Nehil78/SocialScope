from pathlib import Path

class KeywordAlert:
    def __init__(self, config):
        self.red_flags = config.get('red_flags', {})
        self.keywords = [k.lower() for k in self.red_flags.get('keywords', [])]
        self.phrases  = [p.lower() for p in self.red_flags.get('phrases', [])]

    def analyze_message(self, text):
        if not text:
            return {"status": "Normal", "flags": [], "is_suspicious": False}

        text_lower = text.lower()
        found_flags = []

        # Keyword check
        for kw in self.keywords:
            if kw in text_lower:
                found_flags.append(kw)

        # Phrase check
        for ph in self.phrases:
            if ph in text_lower:
                found_flags.append(ph)

        # Simple Sentiment
        aggressive_words = ["kill", "maar", "khatam", "bomb", "blast", "goli"]
        if any(word in text_lower for word in aggressive_words) or len(found_flags) >= 2:
            sentiment = "Aggressive"
            is_suspicious = True
        elif found_flags:
            sentiment = "Suspicious"
            is_suspicious = True
        else:
            sentiment = "Normal"
            is_suspicious = False

        return {
            "status": sentiment,
            "flags": found_flags,
            "is_suspicious": is_suspicious
        }