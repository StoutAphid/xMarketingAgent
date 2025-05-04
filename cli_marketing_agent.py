from dotenv import load_dotenv
load_dotenv()

import os
import sys
import requests
import json
import base64
import hashlib
import secrets
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from requests_oauthlib import OAuth1

# Placeholder for ASI1 LLM API integration
def converse_with_ai(prompt, asi1_api_key):
    # Replace with actual API call
    return f"[AI Response to]: {prompt}"

# Helper to guide user through Twitter API credential setup
def guide_twitter_setup():
    print("\nTo connect your Twitter (X) account, follow these steps:")
    print("1. Go to https://developer.twitter.com/en/portal/dashboard and create a Project and an App.\n")
    print("2. Navigate to your App's Keys and Tokens section.")
    print("3. Generate and copy your API Key and API Key Secret.\n")
    print("4. Generate and copy your Access Token and Access Token Secret.\n")
    print("5. Add your API Key to the .env file as TWITTER_API_KEY, API Key Secret as TWITTER_API_KEY_SECRET, Access Token as TWITTER_ACCESS_TOKEN, and Access Token Secret as TWITTER_ACCESS_TOKEN_SECRET.\n")
    print("If you need more help, type 'help twitter'.")

# Helper to generate PKCE code verifier and challenge
def generate_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode('utf-8')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).rstrip(b'=').decode('utf-8')
    return code_verifier, code_challenge

# Helper HTTP handler to catch the OAuth redirect
class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)
        if 'code' in params:
            OAuthCallbackHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Authorization complete. You can close this window.</h1>')
        else:
            self.send_response(400)
            self.end_headers()

# Function to start a local HTTP server for redirect URI
def start_local_http_server(port=8080):
    server = HTTPServer(('localhost', port), OAuthCallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    return server, thread

# Function to perform OAuth 2.0 Authorization Code Flow with PKCE
def oauth2_pkce_flow():
    client_id = os.getenv('TWITTER_CLIENT_ID')
    client_secret = os.getenv('TWITTER_CLIENT_SECRET')
    redirect_uri = os.getenv('TWITTER_REDIRECT_URI')
    scope = 'tweet.write tweet.read users.read offline.access'
    code_verifier, code_challenge = generate_pkce_pair()
    auth_url = (
        f"https://twitter.com/i/oauth2/authorize?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
        f"&scope={urllib.parse.quote(scope)}"
        f"&state=state123"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    print("\nGo to this URL in your browser and authorize the app:")
    print(auth_url)
    print("\nWaiting for authorization...")
    server, thread = start_local_http_server(port=8080)
    thread.join()
    auth_code = OAuthCallbackHandler.auth_code
    if not auth_code:
        print("Authorization code not received.")
        return None
    print("Received authorization code. Exchanging for access token...")
    token_url = "https://api.twitter.com/2/oauth2/token"
    data = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier
    }
    import base64
    basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic_auth}"
    }
    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code == 200:
        tokens = response.json()
        print("Access token:", tokens.get("access_token"))
        print("Refresh token:", tokens.get("refresh_token"))
        # Optionally, update the .env file or print instructions for user to do so
        return tokens
    else:
        print("Error exchanging code for token:", response.status_code, response.text)
        return None

# Function to fetch Twitter profile info using OAuth 2.0 User Access Token
def get_twitter_profile():
    user_token = os.getenv('TWITTER_USER_ACCESS_TOKEN')
    if not user_token:
        print("No Twitter User Access Token found. Please add it to your .env file as TWITTER_USER_ACCESS_TOKEN.")
        return
    url = "https://api.twitter.com/2/users/me"
    headers = {"Authorization": f"Bearer {user_token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("Profile info:", response.json())
        else:
            print("Error fetching profile:", response.status_code, response.text)
    except Exception as e:
        print(f"Exception occurred: {e}")

def upload_media_v1(image_paths, api_key, api_secret, access_token, access_token_secret):
    """Uploads one or more images to Twitter v1.1 and returns a list of media_ids."""
    import requests_oauthlib
    media_ids = []
    upload_url = "https://upload.twitter.com/1.1/media/upload.json"
    oauth = requests_oauthlib.OAuth1(api_key, api_secret, access_token, access_token_secret)
    for image_path in image_paths:
        with open(image_path, 'rb') as img_file:
            files = {'media': img_file}
            response = requests.post(upload_url, files=files, auth=oauth)
            if response.status_code == 200:
                media_id = response.json().get('media_id_string')
                if media_id:
                    media_ids.append(media_id)
            else:
                print(f"Error uploading {image_path}: {response.status_code} {response.text}")
    return media_ids

# Modified post_tweet to support multiple images
# Usage: post_tweet("text", ["img1.jpg", "img2.png"])
def post_tweet(tweet_text, image_paths=None):
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_KEY_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    user_token = os.getenv('TWITTER_USER_ACCESS_TOKEN')
    if image_paths:
        media_ids = upload_media_v1(image_paths, api_key, api_secret, access_token, access_token_secret)
    else:
        media_ids = []
    url = "https://api.twitter.com/2/tweets"
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
    payload = {"text": tweet_text}
    if media_ids:
        payload["media"] = {"media_ids": media_ids}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 201:
            print("Tweet posted successfully!", response.json())
        else:
            print("Error posting tweet:", response.status_code, response.text)
    except Exception as e:
        print(f"Exception occurred: {e}")

def print_command_sheet():
    print("""
==================== CLI COMMAND SHEET ====================
connect twitter           : Show Twitter API credential setup instructions
connect twitter oauth     : Start OAuth 2.0 PKCE flow to get user access token
help twitter              : Show detailed Twitter API setup help
exit / quit               : Exit the CLI

twitter profile           : Fetch and display your Twitter profile info
post tweet: TEXT          : Post a tweet with just text
post tweet: TEXT :: IMG   : Post a tweet with text and one or more images (comma-separated)
    Example: post tweet: Hello! :: img1.jpg,img2.png
===========================================================
""")

def handle_cli_command(user_input, asi1_api_key=None):
    if user_input.lower() in ['exit', 'quit']:
        print("Goodbye!")
        return
    elif user_input.lower() == 'connect twitter':
        guide_twitter_setup()
    elif user_input.lower() == 'connect twitter oauth':
        oauth2_pkce_flow()
    elif user_input.lower() == 'help twitter':
        print("\nDetailed Twitter API setup instructions:\n")
        print("- Twitter Developer Portal: https://developer.twitter.com/en/docs/twitter-api/getting-started/getting-access-to-the-twitter-api")
        print("- You need a Project, App, API Key, API Key Secret, Access Token, and Access Token Secret for posting tweets.\n")
        print("- Add your API Key to your .env file as TWITTER_API_KEY, API Key Secret as TWITTER_API_KEY_SECRET, Access Token as TWITTER_ACCESS_TOKEN, and Access Token Secret as TWITTER_ACCESS_TOKEN_SECRET.\n")
    elif user_input.lower() == 'twitter profile':
        get_twitter_profile()
    elif user_input.lower().startswith('post tweet:'):
        # Syntax: post tweet: text :: img1.jpg,img2.png
        if '::' in user_input:
            tweet_part, images_part = user_input[len('post tweet:'):].split('::', 1)
            tweet_text = tweet_part.strip()
            image_paths = [img.strip() for img in images_part.strip().split(',') if img.strip()]
            if tweet_text:
                post_tweet(tweet_text, image_paths)
            else:
                print("Please provide the tweet text before '::'.")
        else:
            tweet_text = user_input[len('post tweet:'):].strip()
            if tweet_text:
                post_tweet(tweet_text)
            else:
                print("Please provide the tweet text after 'post tweet:'")
    else:
        ai_response = converse_with_ai(user_input, asi1_api_key)
        print(f"Agent: {ai_response}")

def main():
    asi1_api_key = os.getenv('ASI1_API_KEY')
    # If a command is passed as a command-line argument, execute it directly
    if len(sys.argv) > 1:
        user_input = ' '.join(sys.argv[1:])
        handle_cli_command(user_input, asi1_api_key)
        return
    print_command_sheet()
    print("\nWelcome to the AI Marketing Agent CLI!")
    print("Type 'connect twitter' to set up Twitter (X) integration.")
    print("Type 'connect twitter oauth' to set up Twitter (X) OAuth 2.0 integration.")
    print("Type 'help' for more options. Type 'exit' or 'quit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        handle_cli_command(user_input, asi1_api_key)

if __name__ == '__main__':
    main()
