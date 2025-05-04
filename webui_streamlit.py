import os
from dotenv import load_dotenv
import streamlit as st
from gemini_utils import generate_ad_content
from ad_strategy import AdPerformanceTracker
import requests
import re
import subprocess
import sys

load_dotenv()
ad_tracker = AdPerformanceTracker()

# --- Utility Functions ---
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

# --- Streamlit State Setup ---
if 'step' not in st.session_state:
    st.session_state['step'] = 0
if 'product' not in st.session_state:
    st.session_state['product'] = ''
if 'questions' not in st.session_state:
    st.session_state['questions'] = []
if 'answers' not in st.session_state:
    st.session_state['answers'] = {}
if 'user_images' not in st.session_state:
    st.session_state['user_images'] = []
if 'reference_image_path' not in st.session_state:
    st.session_state['reference_image_path'] = None
if 'options' not in st.session_state:
    st.session_state['options'] = []
if 'ad_generated' not in st.session_state:
    st.session_state['ad_generated'] = False

st.set_page_config(page_title="AI Marketing Agent", page_icon="🚀", layout="centered")
st.title("🚀 AI Marketing Agent for X (Twitter)")
st.markdown("""
This agent helps you generate and post engaging ad content for X (Twitter) using AI. Just enter your product or service, answer a few questions, and let the agent do the rest!
""")

# --- Step 1: Product Input ---
if st.session_state['step'] == 0:
    product = st.text_input("What is your product/app/service?", st.session_state['product'])
    if st.button("Next") and product.strip():
        st.session_state['product'] = product.strip()
        st.session_state['questions'] = ask_questions_with_gemini(product.strip())
        st.session_state['step'] = 1
        st.rerun()
        st.stop()

# --- Step 2: Questions & Answers ---
if st.session_state['step'] == 1:
    st.header("Answer a few questions to help create the best ad:")
    for idx, q in enumerate(st.session_state['questions']):
        st.session_state['answers'][q] = st.text_input(f"Q{idx+1}: {q}", st.session_state['answers'].get(q, ''), key=f"q_{idx}")
    img_input = st.text_input("Do you have any images to include? (enter file paths separated by commas, or leave blank):", ", ".join(st.session_state['user_images']))
    st.session_state['user_images'] = [img.strip() for img in img_input.split(',') if img.strip()]
    if st.button("Generate Ad Options"):
        # Generate image if needed
        if not st.session_state['user_images']:
            image_prompt = get_gemini_image_prompt(st.session_state['product'], st.session_state['answers'])
            st.session_state['reference_image_path'] = generate_image_from_prompt(image_prompt)
        else:
            st.session_state['reference_image_path'] = None
        # Generate ad options
        context = f"Product: {st.session_state['product']}\n"
        for q, a in st.session_state['answers'].items():
            context += f"{q} {a}\n"
        if st.session_state['user_images']:
            context += f"User images: {', '.join(st.session_state['user_images'])}\n"
        elif st.session_state['reference_image_path']:
            context += f"Reference image: {st.session_state['reference_image_path']}\n"
        context += "Use real-world examples and best practices from the web."
        content_prompt = f"Using the following context, create 3 different engaging, human-like X (Twitter) ad post options for this product. Number them as option 1, option 2, option 3 (lowercase, no colon needed). Each option should include a headline and supporting data.\n{context}"
        ad_text = generate_ad_content(content_prompt)
        st.session_state['options'] = extract_options_gex(ad_text)
        st.session_state['ad_generated'] = True
        st.session_state['step'] = 2
        st.rerun()
        st.stop()

# --- Step 3: Show Ad Options and Post ---
if st.session_state['step'] == 2:
    st.header("Generated Ad Options:")
    for idx, opt in enumerate(st.session_state['options'], 1):
        st.markdown(f"**Option {idx}:**\n> {opt}")
    selected_idx = st.radio("Which option do you want to post?", options=[f"Option {i+1}" for i in range(len(st.session_state['options']))], index=0)
    selected_ad = clean_tweet_text(st.session_state['options'][int(selected_idx.split()[1])-1])
    if st.button("Post to X (Twitter)"):
        st.info("Posting to X (Twitter)...")
        media_args = st.session_state['user_images'] if st.session_state['user_images'] else ([st.session_state['reference_image_path']] if st.session_state['reference_image_path'] else [])
        tweet_cmd = f'post tweet: {selected_ad}'
        if media_args:
            tweet_cmd += ' :: ' + ', '.join(media_args)
        env = os.environ.copy()
        result = subprocess.run([
            sys.executable, 'cli_marketing_agent.py', tweet_cmd
        ], check=False, env=env, capture_output=True, text=True)
        st.code(result.stdout, language="text")
        if result.returncode == 0:
            st.success("Tweet posted successfully!")
            # --- Show Plan, Suggestions, and Tweet Link ---
            st.markdown("---")
            st.header("🎯 Your Campaign Plan & Suggestions")
            st.markdown(f"**Product/Service:** {st.session_state['product']}")
            st.markdown("**Q&A for Campaign:**")
            for q, a in st.session_state['answers'].items():
                st.markdown(f"- **{q}**  \\ {a}")
            st.markdown("**Ad Option Posted:**")
            st.markdown(f"> {selected_ad}")
            # Suggestion (optional):
            st.info("Tip: Monitor engagement for 24-48 hours and consider A/B testing with alternative options.")
            # Try to extract tweet URL from stdout or build from username (if available)
            import re
            tweet_url = None
            match = re.search(r'https://twitter.com/[^\s]+/status/\d+', result.stdout)
            if match:
                tweet_url = match.group(0)
            if tweet_url:
                st.markdown(f"[View your post on X (Twitter)]({tweet_url})")
            else:
                st.info("Tweet link will appear here if available.")
        else:
            st.error(f"Failed to post tweet. Error: {result.stderr}")
    if st.button("Start Over"):
        for k in ['step', 'product', 'questions', 'answers', 'user_images', 'reference_image_path', 'options', 'ad_generated']:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()
        st.stop()
