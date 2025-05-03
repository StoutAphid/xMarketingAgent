import os
from dotenv import load_dotenv
load_dotenv()
from twitter_utils import post_tweet, upload_media
from gemini_utils import generate_ad_content
from ad_strategy import AdPerformanceTracker
from selenium_utils import search_and_scrape_images

ad_tracker = AdPerformanceTracker()

def main():
    product = input("What is your product/app/service? ").strip()
    if not product:
        print("Product name is required.")
        return
    image_path = input("Do you have an image to use? (enter file path or leave blank): ").strip()
    if image_path:
        prompt = f"This is an image for the product: {product}. Generate an engaging X (Twitter) post using this image as context."
        ad_text = generate_ad_content(prompt)
        print(f"\nGenerated ad:\n{ad_text}\n")
        confirm = input("Do you want to post this to X (Twitter)? (y/n): ").strip().lower()
        if confirm == 'y':
            media_ids = upload_media([image_path])
            result = post_tweet(ad_text, media_ids=media_ids)
            if result and 'data' in result:
                tweet_id = result['data']['id']
                ad_tracker.record_tweet(tweet_id, ad_text, images=[image_path])
                print(f"Posted tweet ID {tweet_id}")
            else:
                print("Failed to post tweet.")
        else:
            print("Tweet not posted.")
    else:
        print("No image provided. Searching the web for a reference image...")
        images = search_and_scrape_images(product, num_images=1)
        if images:
            img_url = images[0]
            prompt = f"This is a reference image found for the product: {product} ({img_url}). Generate an engaging X (Twitter) post using this image as context."
        else:
            prompt = f"Generate an engaging X (Twitter) post for the product: {product}."
        ad_text = generate_ad_content(prompt)
        print(f"\nGenerated ad:\n{ad_text}\n")
        confirm = input("Do you want to post this to X (Twitter)? (y/n): ").strip().lower()
        media_ids = []
        if confirm == 'y':
            if images:
                import requests
                img_data = requests.get(img_url).content
                temp_path = "reference_image.jpg"
                with open(temp_path, 'wb') as f:
                    f.write(img_data)
                media_ids = upload_media([temp_path])
            result = post_tweet(ad_text, media_ids=media_ids)
            if result and 'data' in result:
                tweet_id = result['data']['id']
                ad_tracker.record_tweet(tweet_id, ad_text, images=[img_url] if images else None)
                print(f"Posted tweet ID {tweet_id}")
            else:
                print("Failed to post tweet.")
        else:
            print("Tweet not posted.")

    # Suggest a posting plan
    plan_prompt = f"Given the product '{product}', suggest an optimal social media posting plan (what, when, and where to post) to maximize marketing impact."
    plan = generate_ad_content(plan_prompt)
    print("\nSuggested Posting Plan:\n", plan)

if __name__ == "__main__":
    main()
