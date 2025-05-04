import os
from dotenv import load_dotenv
load_dotenv()
from gemini_utils import generate_ad_content
from ad_strategy import AdPerformanceTracker
import sys
import subprocess
import re
import requests

ad_tracker = AdPerformanceTracker()

def clean_tweet_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'option\s*\d+[:\-\.]?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(headline|title)[:\-\.]?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    if len(text) > 280:
        cutoff = text[:280].rfind('.')
        if cutoff == -1:
            cutoff = text[:280].rfind(' ')
        if cutoff == -1:
            cutoff = 277
        text = text[:cutoff].strip()
        if not text.endswith('.'):
            text += '...'
    return text

def generate_image_from_prompt(prompt, output_path="pollinations_image.png"):
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"[DEBUG] Image generated and saved as {output_path}")
        return output_path
    else:
        print(f"[ERROR] Pollinations API error: {response.status_code}")
        return None

def ask_questions_with_gemini(product):
    prompt = f"You are a marketing expert. Given the product or service '{product}', what are the 5 most important questions you would ask a client to create a highly effective and engaging X (Twitter) ad campaign? Please list the questions only."
    questions_text = generate_ad_content(prompt)
    questions = []
    for line in questions_text.split('\n'):
        line = line.strip('- ').strip()
        if line and (line.endswith('?') or line.lower().startswith('what') or line.lower().startswith('how')):
            questions.append(line)
        if len(questions) >= 5:
            break
    return questions[:5] if questions else [questions_text.strip()]

def extract_options_gex(text):
    pattern = re.compile(r'(option\s*\d+)(.*?)(?=(option\s*\d+)|$)', re.IGNORECASE | re.DOTALL)
    matches = pattern.findall(text)
    options = []
    for match in matches:
        headline = match[0].strip()
        body = match[1].strip()
        full_option = f"{headline}{body}".strip()
        if full_option:
            options.append(full_option)
    if not options:
        options = [text.strip()]
    return options

def get_gemini_image_prompt(product, answers):
    context = f"Product: {product}\n"
    for q, a in answers.items():
        context += f"{q} {a}\n"
    prompt = f"Given the following context, write a short, vivid, and creative prompt for an AI image generator to create a beautiful and engaging image that would help market this product on social media. Do not include any explanations or extra text, just the image prompt.\n{context}"
    image_prompt = generate_ad_content(prompt)
    image_prompt = image_prompt.strip().split('\n')[0].strip('"')
    return image_prompt

def main():
    print("[DEBUG] ENV: TWITTER_USER_ACCESS_TOKEN:", os.environ.get("TWITTER_USER_ACCESS_TOKEN"))
    product = input("What is your product/app/service? ").strip()
    if not product:
        print("Product name is required.")
        return
    questions = ask_questions_with_gemini(product)
    answers = {}
    print("\nPlease answer the following questions to help the agent create the best content:")
    for q in questions:
        ans = input(q + " ").strip()
        answers[q] = ans
    user_images = []
    img_input = input("Do you have any images to include? (enter file paths separated by commas, or leave blank): ").strip()
    if img_input:
        user_images = [img.strip() for img in img_input.split(',') if img.strip()]
    reference_image_path = None
    if not user_images:
        print("\nNo user images provided. Generating a custom AI image...")
        image_prompt = get_gemini_image_prompt(product, answers)
        print(f"[DEBUG] Gemini-generated image prompt: {image_prompt}")
        reference_image_path = generate_image_from_prompt(image_prompt)
    context = f"Product: {product}\n"
    for q, a in answers.items():
        context += f"{q} {a}\n"
    if user_images:
        context += f"User images: {', '.join(user_images)}\n"
    elif reference_image_path:
        context += f"Reference image: {reference_image_path}\n"
    context += "Use real-world examples and best practices from the web."
    content_prompt = f"Using the following context, create 3 different engaging, human-like X (Twitter) ad post options for this product. Number them as option 1, option 2, option 3 (lowercase, no colon needed). Each option should include a headline and supporting data.\n{context}"
    ad_text = generate_ad_content(content_prompt)
    print("\nGenerated ad options:\n")
    options = extract_options_gex(ad_text)
    for idx, opt in enumerate(options, 1):
        print(f"[{idx}]\n{opt}\n")
    while True:
        try:
            choice = int(input(f"Which option do you want to post? (1-{len(options)}): ").strip())
            if 1 <= choice <= len(options):
                break
            else:
                print("Invalid choice. Please enter a number from the options above.")
        except ValueError:
            print("Please enter a valid number.")
    selected_ad = clean_tweet_text(options[choice-1])
    confirm = input("Do you want to post this to X (Twitter)? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Tweet not posted.")
        sys.exit(0)
    media_args = []
    if user_images:
        media_args = user_images
    elif reference_image_path:
        media_args = [reference_image_path]
    tweet_cmd = f'post tweet: {selected_ad}'
    if media_args:
        tweet_cmd += f' :: {", ".join(media_args)}'
    env = os.environ.copy()
    print(f"[DEBUG] About to call cli_marketing_agent.py with env: TWITTER_USER_ACCESS_TOKEN={env.get('TWITTER_USER_ACCESS_TOKEN')}")
    print(f"Posting selected option using cli_marketing_agent.py...\n")
    result = subprocess.run([
        sys.executable, 'cli_marketing_agent.py', tweet_cmd
    ], check=False, env=env, capture_output=True, text=True)
    print("[DEBUG] CLI STDOUT:\n", result.stdout)
    print("[DEBUG] CLI STDERR:\n", result.stderr)
    if result.returncode != 0:
        print(f"[ERROR] cli_marketing_agent.py exited with code {result.returncode}")
    plan_prompt = f"Given the product '{product}' and these answers: {answers}, suggest an optimal social media posting plan (what, when, and where to post) to maximize marketing impact."
    plan = generate_ad_content(plan_prompt)
    print("\nSuggested Posting Plan:\n", plan)

if __name__ == "__main__":
    main()
