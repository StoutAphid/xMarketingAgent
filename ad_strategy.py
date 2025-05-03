from twitter_utils import get_tweet_metrics

class AdPerformanceTracker:
    def __init__(self):
        self.tweet_history = []  # List of dicts: {tweet_id, text, images, metrics}

    def record_tweet(self, tweet_id, text, images):
        self.tweet_history.append({
            'tweet_id': tweet_id,
            'text': text,
            'images': images,
            'metrics': None
        })

    def update_metrics(self):
        for tweet in self.tweet_history:
            if tweet['metrics'] is None:
                metrics = get_tweet_metrics(tweet['tweet_id'])
                tweet['metrics'] = metrics

    def best_performing(self):
        self.update_metrics()
        if not self.tweet_history:
            return None
        return max(self.tweet_history, key=lambda t: (t['metrics'] or {}).get('like_count', 0))

    def needs_improvement(self, threshold=5):
        self.update_metrics()
        return [t for t in self.tweet_history if (t['metrics'] or {}).get('like_count', 0) < threshold]
