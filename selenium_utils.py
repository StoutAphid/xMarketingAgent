from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Use Firefox (geckodriver) by default, which is often available or auto-installed with selenium

def search_and_scrape_images(query, num_images=1):
    """Scrape image URLs from DuckDuckGo image search using Firefox (headless)."""
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)
    driver.get(f'https://duckduckgo.com/?q={query}&iax=images&ia=images')
    time.sleep(2)
    # Click Images tab if not already there
    try:
        images_tab = driver.find_element(By.XPATH, '//a[contains(@data-zci-link, "images")]')
        images_tab.click()
        time.sleep(2)
    except Exception:
        pass
    image_urls = []
    thumbnails = driver.find_elements(By.CSS_SELECTOR, 'img.tile--img__img')
    for thumb in thumbnails[:num_images]:
        src = thumb.get_attribute('src')
        if src and src.startswith('http'):
            image_urls.append(src)
    driver.quit()
    return image_urls
