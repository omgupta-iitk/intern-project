from textblob import TextBlob
from app.models.feedback import FeedbackCreate

class FeedbackAnalyzer:
    def __init__(self, feedback: FeedbackCreate):
        """Initialize with a single FeedbackCreate object"""
        if not isinstance(feedback, FeedbackCreate):
            raise ValueError("Input must be a FeedbackCreate object")
        # Convert to dictionary and validate
        self.data = self._validate_and_clean(feedback.model_dump())

    def _validate_and_clean(self, data: dict) -> dict:
        """Ensure 'feedback' field exists and is a string"""
        data['feedback'] = str(data.get('feedback', '') or '')
        return data

    def _extract_adjectives(self, text: str):
        return [word for (word, tag) in TextBlob(text).tags if tag == 'JJ']

    def _analyze_sentiment(self, text: str):
        return TextBlob(text).sentiment.polarity

    def _label_sentiment(self, polarity: float):
        if polarity > 0.1:
            return "positive"
        elif polarity < -0.1:
            return "negative"
        return "neutral"

    def _enrich(self):
        """Add enrichment fields to the feedback item"""
        text = self.data['feedback']
        self.data['word_count'] = len(text.split())
        self.data['adjectives'] = self._extract_adjectives(text)
        polarity = self._analyze_sentiment(text)
        self.data['sentiment'] = polarity
        self.data['sentiment_label'] = self._label_sentiment(polarity)

    def get_data(self) -> dict:
        """Return enriched feedback as a dictionary"""
        self._enrich()
        return self.data
