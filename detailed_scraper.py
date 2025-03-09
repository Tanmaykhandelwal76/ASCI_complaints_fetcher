import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_detailed_complaints(complaints_data, headless=True):
    """Fetch detailed descriptions for each complaint by visiting their links."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    detailed_complaints = []
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 10)
        
        for complaint in complaints_data:
            try:
                driver.get(complaint['link'])
                logger.info(f"Fetching details from: {complaint['link']}")
                
                # Wait for and extract detailed content
                detail_selector = "div#comOutcomes p:nth-child(3)"  # Updated selector
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, detail_selector)))
                time.sleep(2)  # Give time for content to load
                
                # Get the detailed description
                detailed_content = driver.find_element(
                    By.CSS_SELECTOR, 
                    detail_selector
                ).get_attribute('textContent').strip()
                
                # Add detailed content to complaint data
                detailed_complaint = complaint.copy()
                detailed_complaint['detailed_description'] = detailed_content
                detailed_complaints.append(detailed_complaint)
                
                logger.info(f"Successfully fetched details for: {complaint['title'][:50]}...")
                
            except Exception as e:
                logger.error(f"Error fetching details for {complaint['link']}: {str(e)}")
                # Add original complaint without details
                detailed_complaints.append(complaint)
                
            # Add a small delay between requests
            time.sleep(2)
                
    except Exception as e:
        logger.error(f"Detailed scraping failed: {str(e)}")
    finally:
        driver.quit()
    
    return detailed_complaints
