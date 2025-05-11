import matplotlib.pyplot as plt
import uuid
from typing import List, Dict
from io import BytesIO
from app.analyzers.util import upload_to_supabase_storage

class FeedbackAnalyzer:
    def __init__(self, feedback_list: List[Dict]):
        """
        Initialize with a list of feedback dictionaries.
        """
        self.feedback_list = feedback_list
        self.analysis_results = {}
        self.generated_image_urls = []

    def analyze(self) -> Dict:
        """
        Perform analysis and return JSON-serializable results.
        """
        # Basic stats
        ratings = [f['rating'] for f in self.feedback_list]
        sentiments = [f['sentiment'] for f in self.feedback_list]
        word_counts = [f['word_count'] for f in self.feedback_list]
        
        # Convert numpy types to native Python types
        self.analysis_results = {
            'total_feedbacks': len(self.feedback_list),
            'average_rating': float(sum(ratings)) / len(ratings),
            'average_sentiment': float(sum(sentiments)) / len(sentiments),
            'average_word_count': float(sum(word_counts)) / len(word_counts),
            
            # Rating distribution
            'rating_distribution': {
                '1': ratings.count(1),
                '2': ratings.count(2),
                '3': ratings.count(3),
                '4': ratings.count(4),
                '5': ratings.count(5)
            },
            
            # Sentiment distribution
            'sentiment_distribution': {
                'positive': sum(1 for f in self.feedback_list 
                               if f['sentiment_label'] == 'positive'),
                'neutral': sum(1 for f in self.feedback_list 
                              if f['sentiment_label'] == 'neutral'),
                'negative': sum(1 for f in self.feedback_list 
                               if f['sentiment_label'] == 'negative')
            },
            
            # Adjective analysis
            'top_adjectives': self._get_top_adjectives(5),

        }
        
        # Generate visualizations and get mock URLs
        self._generate_charts()
        self.analysis_results['chart_urls'] = self.generated_image_urls
        
        return self.analysis_results
    
    def _get_top_adjectives(self, n: int) -> Dict:
        """Get top n most frequent adjectives."""
        adjectives = []
        for feedback in self.feedback_list:
            adjectives.extend(feedback['adjectives'])
        
        # Count frequencies
        freq = {}
        for adj in adjectives:
            freq[adj] = freq.get(adj, 0) + 1
        
        # Get top n
        top_n = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:n]
        return {adj: count for adj, count in top_n}
    
    def _generate_charts(self):
        """Generate simple charts and save to temp files."""
        # Rating distribution
        plt.figure(figsize=(6, 4))
        ratings = [f['rating'] for f in self.feedback_list]
        plt.hist(ratings, bins=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5], edgecolor='black')
        plt.title('Rating Distribution')
        plt.xlabel('Rating (1-5)')
        plt.ylabel('Count')
        image_bytes = BytesIO()
        plt.savefig(image_bytes, format='png')
        plt.close()
        image_bytes.seek(0)
        image_url = upload_to_supabase_storage(image_bytes.read(), f"daily_trend_{uuid.uuid4()}.png")
        self.generated_image_urls.append(image_url)
        
        # Sentiment distribution
        plt.figure(figsize=(6, 4))
        sentiments = [f['sentiment_label'] for f in self.feedback_list]
        plt.hist(sentiments)
        plt.title('Sentiment Distribution')
        image_bytes = BytesIO()
        plt.savefig(image_bytes, format='png')
        plt.close()
        image_bytes.seek(0)
        image_url = upload_to_supabase_storage(image_bytes.read(), f"daily_trend_{uuid.uuid4()}.png")
        self.generated_image_urls.append(image_url)

class CommentFeedbackAnalyzer:
    def __init__(self, feedback_list: List[Dict]):
        """
        Initialize with a list of feedback dictionaries.
        """
        self.feedback_list = feedback_list
        self.analysis_results = {}
        self.generated_image_urls = []

    def analyze(self) -> Dict:
        """
        Perform analysis and return JSON-serializable results.
        """
        # Basic stats
        sentiments = [f['sentiment'] for f in self.feedback_list]
        word_counts = [f['word_count'] for f in self.feedback_list]
        
        # Convert numpy types to native Python types
        self.analysis_results = {
            'total_feedbacks': len(self.feedback_list),
            'average_sentiment': float(sum(sentiments)) / len(sentiments),
            'average_word_count': float(sum(word_counts)) / len(word_counts),
            
            # Sentiment distribution
            'sentiment_distribution': {
                'positive': sum(1 for f in self.feedback_list 
                               if f['sentiment_label'] == 'positive'),
                'neutral': sum(1 for f in self.feedback_list 
                              if f['sentiment_label'] == 'neutral'),
                'negative': sum(1 for f in self.feedback_list 
                               if f['sentiment_label'] == 'negative')
            },
            
            # Adjective analysis
            'top_adjectives': self._get_top_adjectives(5),

        }
        
        # Generate visualizations and get mock URLs
        self._generate_charts()
        self.analysis_results['chart_urls'] = self.generated_image_urls
        
        return self.analysis_results
    
    def _get_top_adjectives(self, n: int) -> Dict:
        """Get top n most frequent adjectives."""
        adjectives = []
        for feedback in self.feedback_list:
            adjectives.extend(feedback['adjectives'])
        
        # Count frequencies
        freq = {}
        for adj in adjectives:
            freq[adj] = freq.get(adj, 0) + 1
        
        # Get top n
        top_n = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:n]
        return {adj: count for adj, count in top_n}
    
    def _generate_charts(self):
        """Generate simple charts and save to temp files."""

        # Sentiment distribution
        plt.figure(figsize=(6, 4))
        sentiments = [f['sentiment_label'] for f in self.feedback_list]
        plt.hist(sentiments)
        plt.title('Sentiment Distribution')
        image_bytes = BytesIO()
        plt.savefig(image_bytes, format='png')
        plt.close()
        image_bytes.seek(0)
        image_url = upload_to_supabase_storage(image_bytes.read(), f"daily_trend_{uuid.uuid4()}.png")
        self.generated_image_urls.append(image_url)