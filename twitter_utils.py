import os
import requests
import requests_oauthlib

def get_trends(woeid=1):
    """Fetch trending topics from Twitter (default: worldwide)."""
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_KEY_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    # Defensive: check for missing env vars
    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("Missing Twitter API credentials. Please check your .env file.")
        return []
    url = f"https://api.twitter.com/1.1/trends/place.json?id={woeid}"
    oauth = requests_oauthlib.OAuth1(api_key, api_secret, access_token, access_token_secret)
    resp = requests.get(url, auth=oauth)
    if resp.status_code == 200:
        return resp.json()[0]['trends']
    else:
        print(f"Error fetching trends: {resp.status_code} {resp.text}")
        return []

def search_tweets(query, count=10):
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_KEY_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    url = f"https://api.twitter.com/1.1/search/tweets.json?q={requests.utils.quote(query)}&count={count}&result_type=recent"
    oauth = requests_oauthlib.OAuth1(api_key, api_secret, access_token, access_token_secret)
    resp = requests.get(url, auth=oauth)
    if resp.status_code == 200:
        return resp.json()['statuses']
    else:
        print(f"Error searching tweets: {resp.status_code} {resp.text}")
        return []

def search_tweets_bearer(query, count=10):
    """Search recent tweets using Twitter API v2 and Bearer Token."""
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    if not bearer_token:
        print("Missing TWITTER_BEARER_TOKEN in .env file.")
        return []
    url = f"https://api.twitter.com/2/tweets/search/recent?query={requests.utils.quote(query)}&max_results={min(count,100)}&tweet.fields=text,public_metrics,created_at"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json().get('data', [])
    else:
        print(f"Error searching tweets (bearer): {resp.status_code} {resp.text}")
        return []

def post_tweet(text, media_ids=None):
    user_token = os.getenv('TWITTER_USER_ACCESS_TOKEN')
    url = "https://api.twitter.com/2/tweets"
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
    payload = {"text": text}
    if media_ids:
        payload["media"] = {"media_ids": media_ids}
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 201:
        return resp.json()
    else:
        print(f"Error posting tweet: {resp.status_code} {resp.text}")
        return None

def upload_media(image_paths):
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_KEY_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    upload_url = "https://upload.twitter.com/1.1/media/upload.json"
    oauth = requests_oauthlib.OAuth1(api_key, api_secret, access_token, access_token_secret)
    media_ids = []
    for image_path in image_paths:
        with open(image_path, 'rb') as img_file:
            files = {'media': img_file}
            resp = requests.post(upload_url, files=files, auth=oauth)
            if resp.status_code == 200:
                media_id = resp.json().get('media_id_string')
                if media_id:
                    media_ids.append(media_id)
            else:
                print(f"Error uploading {image_path}: {resp.status_code} {resp.text}")
    return media_ids

def get_tweet_metrics(tweet_id):
    user_token = os.getenv('TWITTER_USER_ACCESS_TOKEN')
    url = f"https://api.twitter.com/2/tweets/{tweet_id}?tweet.fields=public_metrics"
    headers = {"Authorization": f"Bearer {user_token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json().get('data', {}).get('public_metrics', {})
    else:
        print(f"Error fetching tweet metrics: {resp.status_code} {resp.text}")
        return {}
