import streamlit as st
from datetime import datetime
import calendar
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.keys import Keys

def scrape_complaints(start_date, end_date, headless=True):
    """
    Scrape complaints from the ASCI Complaint Outcomes page within a date range.
    Verifies that each complaint's date falls within the selected range.
    """
    url = "https://www.ascionline.in/complaint-outcomes/"
    options = Options()
    if headless:
        options.add_argument("--headless")  # Run in headless mode by default
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        
        # Handle cookie consent modal
        try:
            close_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
            ))
            close_button.click()
            time.sleep(2)
        except Exception:
            pass
        
        # Format dates in YYYY-MM-DD format
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Find date inputs and set values using JavaScript
        script = """
            const fromInput = document.getElementById('DATE_FROM');
            const toInput = document.getElementById('DATE_TO');
            
            fromInput.value = arguments[0];
            toInput.value = arguments[1];
            
            // Trigger change events
            fromInput.dispatchEvent(new Event('change', { bubbles: true }));
            toInput.dispatchEvent(new Event('change', { bubbles: true }));
            
            // Trigger input events
            fromInput.dispatchEvent(new Event('input', { bubbles: true }));
            toInput.dispatchEvent(new Event('input', { bubbles: true }));
        """
        
        driver.execute_script(script, start_date_str, end_date_str)
        
        # Wait for the results to load
        time.sleep(5)
        
        # Wait for complaints to load
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#comOutcome ul.searchBarCon_ul_comOutcome li")
        ))
        time.sleep(3)
        
        # Load all complaints by clicking "Show More"
        while True:
            try:
                show_more_button = driver.find_element(By.CLASS_NAME, "showMoreCom")
                if show_more_button.is_displayed() and show_more_button.is_enabled():
                    driver.execute_script("arguments[0].click();", show_more_button)
                    time.sleep(5)
                else:
                    break
            except:
                break
        
        # Extract and filter complaints
        complaint_list = driver.find_elements(
            By.CSS_SELECTOR, "#comOutcome ul.searchBarCon_ul_comOutcome li"
        )
        complaints = []
        for complaint in complaint_list:
            try:
                # Extract complaint details
                title_elem = complaint.find_element(By.CLASS_NAME, "comOutcomeTitle")
                link_elem = title_elem.find_element(By.TAG_NAME, "a")
                link = link_elem.get_attribute("href")
                title = link_elem.text.strip()
                
                spanline = complaint.find_element(By.CLASS_NAME, "spanline")
                spans = spanline.find_elements(By.TAG_NAME, "span")
                if len(spans) >= 3:
                    outcome = spans[0].text.strip()
                    source = spans[1].text.strip()
                    date_str = spans[2].text.strip()
                else:
                    continue
                
                description_elems = complaint.find_elements(By.TAG_NAME, "p")
                description = description_elems[2].text.strip() if len(description_elems) >= 3 else "No description"
                
                complaints.append({
                    "title": title,
                    "link": link,
                    "outcome": outcome,
                    "source": source,
                    "date": date_str,
                    "description": description
                })
            except Exception:
                continue
        
        return complaints
    
    except Exception as e:
        st.error(f"Scraping failed: {str(e)}")
        return []
    
    finally:
        driver.quit()

def main():
    """Run the Streamlit app for scraping complaints."""
    st.title("ASCI Complaint Outcomes Scraper")
    st.write("Select a date range to scrape complaints with precision.")
    
    mode = st.radio("Select Mode", ["Simple Mode", "Advanced Mode"])
    dev_mode = st.checkbox("Enable Development Mode (Non-Headless)", value=False)
    
    # Date range selection
    if mode == "Simple Mode":
        today = datetime.today()
        year, month, day = today.year, today.month, today.day
        if day <= 15:
            start_date = datetime(year, month, 1)
            end_date = datetime(year, month, 15)
        else:
            last_day = calendar.monthrange(year, month)[1]
            start_date = datetime(year, month, 16)
            end_date = datetime(year, month, last_day)
        st.write(f"**Date Range**: {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}")
    else:
        start_date = st.date_input("Start Date", value=datetime.today())
        end_date = st.date_input("End Date", value=datetime.today())
        if start_date > end_date:
            st.error("End Date must be on or after Start Date.")
            return
    
    if st.button("Scrape Data"):
        with st.spinner("Scraping data..."):
            complaints = scrape_complaints(start_date, end_date, headless=not dev_mode)
            if complaints:
                df = pd.DataFrame(complaints)
                st.success(f"Scraped {len(df)} complaints within the date range!")
                st.write("### Sample Data (First 5 Entries)")
                st.dataframe(df.head(5))
                json_data = df.to_json(orient="records", indent=4)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name="complaint_outcomes.json",
                    mime="application/json"
                )
            else:
                st.warning("No complaints found within the selected date range.")

if __name__ == "__main__":
    main()