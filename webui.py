from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
from gemini_utils import generate_ad_content
from ad_strategy import AdPerformanceTracker
import requests
import re
import subprocess

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')
load_dotenv()
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

def generate_image_from_prompt(prompt, output_path="static/pollinations_image.png"):
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        return output_path
    else:
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product = request.form['product'].strip()
        if not product:
            flash('Product name is required.', 'danger')
            return redirect(url_for('index'))
        questions = ask_questions_with_gemini(product)
        answers = {}
        for i, q in enumerate(questions):
            ans = request.form.get(f'answer_{i}', '').strip()
            answers[q] = ans
        user_images = request.form.get('user_images', '').strip()
        image_paths = [img.strip() for img in user_images.split(',') if img.strip()] if user_images else []
        reference_image_path = None
        if not image_paths:
            image_prompt = get_gemini_image_prompt(product, answers)
            reference_image_path = generate_image_from_prompt(image_prompt)
        else:
            reference_image_path = None
        context = f"Product: {product}\n"
        for q, a in answers.items():
            context += f"{q} {a}\n"
        if image_paths:
            context += f"User images: {', '.join(image_paths)}\n"
        elif reference_image_path:
            context += f"Reference image: {reference_image_path}\n"
        context += "Use real-world examples and best practices from the web."
        content_prompt = f"Using the following context, create 3 different engaging, human-like X (Twitter) ad post options for this product. Number them as option 1, option 2, option 3 (lowercase, no colon needed). Each option should include a headline and supporting data.\n{context}"
        ad_text = generate_ad_content(content_prompt)
        options = extract_options_gex(ad_text)
        return render_template('options.html', product=product, questions=questions, answers=answers, options=list(enumerate(options)), image_paths=image_paths, reference_image_path=reference_image_path)
    return render_template('index.html')

@app.route('/post', methods=['POST'])
def post_option():
    product = request.form['product']
    option_idx = int(request.form['option_idx'])
    image_paths = request.form.getlist('image_paths')
    reference_image_path = request.form.get('reference_image_path')
    options = request.form.getlist('options')
    selected_ad = clean_tweet_text(options[option_idx])
    media_args = []
    if image_paths:
        media_args = image_paths
    elif reference_image_path:
        media_args = [reference_image_path]
    tweet_cmd = f'post tweet: {selected_ad}'
    if media_args:
        tweet_cmd += f' :: {", ".join(media_args)}'
    env = os.environ.copy()
    result = subprocess.run([
        sys.executable, 'cli_marketing_agent.py', tweet_cmd
    ], check=False, env=env, capture_output=True, text=True)
    if result.returncode == 0:
        flash('Tweet posted successfully!', 'success')
    else:
        flash(f'Tweet failed to post. Error: {result.stderr}', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)
