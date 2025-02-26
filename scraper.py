import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import logging
from selenium.common.exceptions import NoSuchElementException

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def parse_date(date_str):
    """Convert date string (e.g., '14 Feb 2025') to datetime object."""
    date_str = date_str.strip()
    if not date_str:
        logger.warning("Empty date string encountered")
        return None
    try:
        return datetime.strptime(date_str, "%d %b %Y")
    except ValueError as e:
        logger.error(f"Failed to parse date '{date_str}': {e}")
        return None

def scrape_complaints(start_date, end_date, output_file="complaint_outcomes.json"):
    """Scrape complaint outcomes within the specified date range."""
    url = "https://www.ascionline.in/complaint-outcomes/"  # Replace with your actual URL
    logger.info(f"Starting scrape for {url} from {start_date} to {end_date}")
    
    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        
        # Click "Show More" until no more button is present
        while True:
            try:
                show_more_button = driver.find_element(By.CLASS_NAME, "showMoreCom")  # Adjust class name if different
                if show_more_button.is_displayed() and show_more_button.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView();", show_more_button)
                    driver.execute_script("arguments[0].click();", show_more_button)
                    logger.info("Clicked 'Show More' button")
                    time.sleep(5)  # Wait for new content to load
                else:
                    break
            except NoSuchElementException:
                logger.info("No more 'Show More' button found")
                break
            except Exception as e:
                logger.info(f"Error clicking 'Show More': {e}")
                break
        
        # Extract all complaints
        complaint_list = driver.find_elements(By.CSS_SELECTOR, "#comOutcome ul.searchBarCon_ul_comOutcome li")  # Adjust selector if needed
        logger.info(f"Total complaints found: {len(complaint_list)}")
        
        complaints = []
        for i, complaint in enumerate(complaint_list):
            try:
                title_elem = complaint.find_element(By.CLASS_NAME, "comOutcomeTitle")
                link = title_elem.find_element(By.TAG_NAME, "a").get_attribute("href")
                title = title_elem.get_attribute('innerText').strip()
                
                spanline = complaint.find_element(By.CLASS_NAME, "spanline")
                spans = spanline.find_elements(By.TAG_NAME, "span")
                if len(spans) < 3:
                    logger.warning(f"Complaint {i}: Insufficient spans ({len(spans)}), skipping")
                    continue
                
                outcome = spans[0].get_attribute('innerText').strip()
                source = spans[1].get_attribute('innerText').strip()
                date_str = spans[2].get_attribute('innerText').strip()
                logger.info(f"Complaint {i}: Extracted date_str: '{date_str}'")
                
                date = parse_date(date_str)
                if date is None:
                    logger.warning(f"Complaint {i}: Failed to parse date '{date_str}'")
                    continue
                
                logger.info(f"Complaint {i}: Parsed date: {date}")
                
                description_elem = complaint.find_elements(By.TAG_NAME, "p")
                description = description_elem[1].get_attribute('innerText').strip() if len(description_elem) > 1 else "No description"
                
                if start_date <= date <= end_date:
                    complaints.append({
                        "title": title,
                        "link": link,
                        "outcome": outcome,
                        "source": source,
                        "date": date_str,
                        "description": description
                    })
                    logger.info(f"Added complaint {i}: {title} - {date_str}")
                else:
                    logger.info(f"Skipped complaint {i}: Date {date_str} outside range")
            
            except Exception as e:
                logger.error(f"Error parsing complaint {i}: {e}")
                continue
        
        # Save to JSON file
        with open(output_file, "w") as f:
            json.dump(complaints, f, indent=4)
        logger.info(f"Saved {len(complaints)} complaints to {output_file}")
        
        return complaints
    
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return []
    
    finally:
        driver.quit()
        logger.info("WebDriver closed")

if __name__ == "__main__":
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 2, 28)
    scrape_complaints(start_date, end_date)