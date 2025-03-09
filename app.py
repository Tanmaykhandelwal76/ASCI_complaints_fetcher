import streamlit as st
from datetime import datetime, date
import calendar
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.keys import Keys
from detailed_scraper import get_detailed_complaints
from newsletter_generator import generate_newsletter

def parse_date(date_str):
    """Convert date string to datetime object."""
    try:
        date_obj = datetime.strptime(date_str.strip(), "%d %b %Y")
        return datetime.combine(date_obj.date(), datetime.min.time())
    except Exception as e:
        st.error(f"Failed to parse date: {date_str} - {str(e)}")
        return None

def scrape_complaints(start_date, end_date, headless=True):
    """
    Scrape complaints from the ASCI Complaint Outcomes page within a date range.
    """
    url = "https://www.ascionline.in/complaint-outcomes/"
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        wait = WebDriverWait(driver, 20)

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
        st.write(f"Setting date range: {start_date_str} to {end_date_str}")
        
        # Enhanced JavaScript to handle date inputs and trigger search
        script = """
            const fromInput = document.getElementById('DATE_FROM');
            const toInput = document.getElementById('DATE_TO');
            
            if (fromInput && toInput) {
                // Set values
                fromInput.value = arguments[0];
                toInput.value = arguments[1];
                
                // Create and dispatch events
                const events = ['change', 'input', 'blur'];
                events.forEach(eventType => {
                    fromInput.dispatchEvent(new Event(eventType, { bubbles: true }));
                    toInput.dispatchEvent(new Event(eventType, { bubbles: true }));
                });

                // Try to find and trigger search functionality
                const form = fromInput.closest('form');
                if (form) {
                    form.dispatchEvent(new Event('submit', { bubbles: true }));
                }
                
                return {
                    from: fromInput.value, 
                    to: toInput.value,
                    formFound: !!form
                };
            }
            return null;
        """
        
        # Execute script and get actual values
        result = driver.execute_script(script, start_date_str, end_date_str)
        if result:
            st.write(f"Date inputs found and set. Values: From={result['from']}, To={result['to']}")
        else:
            st.error("Could not find date input fields")
            return []
        
        # Wait for the results to load
        time.sleep(5)
        
        try:
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
            
            # Get all complaints and filter by date
            complaints = []
            all_complaints = driver.find_elements(
                By.CSS_SELECTOR, "#comOutcome ul.searchBarCon_ul_comOutcome li"
            )
            
            for complaint in all_complaints:
                try:
                    date_str = complaint.find_element(
                        By.CSS_SELECTOR, "p.spanline > span:nth-child(3)"
                    ).get_attribute("textContent").strip()
                    
                    complaint_date = parse_date(date_str)
                    if not complaint_date or not (start_date <= complaint_date <= end_date):
                        continue
                    
                    # Extract other complaint details
                    # Debug the complaint HTML
                    st.write("Complaint HTML:", complaint.get_attribute('innerHTML')[:200])
                    
                    # Extract title and link with better error handling
                    title_elem = complaint.find_element(By.CSS_SELECTOR, ".comOutcomeTitle a")
                    link = title_elem.get_attribute("href") or ""
                    title = title_elem.get_attribute("textContent").strip()
                    
                    # Extract spans with explicit waiting
                    spanline = wait.until(EC.presence_of_element_located(
                        (By.CLASS_NAME, "spanline")
                    ))
                    spans = spanline.find_elements(By.TAG_NAME, "span")
                    
                    # Extract data with validation
                    if len(spans) >= 3:
                        outcome = spans[0].get_attribute("textContent").strip()
                        source = spans[1].get_attribute("textContent").strip()
                        date_str = spans[2].get_attribute("textContent").strip()
                    else:
                        st.warning(f"Insufficient spans found for complaint: {title}")
                        continue
                    
                    # Extract description with correct selector
                    description = ""
                    try:
                        description_elem = complaint.find_element(
                            By.CSS_SELECTOR, 
                            "li > p:nth-child(3)"  # Using the exact selector that works
                        )
                        description = description_elem.get_attribute("textContent").strip()
                    except Exception as e:
                        st.write(f"Error extracting description: {str(e)}")
                        description = "No description available"
                    
                    # Validate data before adding
                    if not all([title, link, outcome, source, date_str]):
                        st.warning(f"Missing required data for complaint: {link}")
                        continue
                    
                    complaints.append({
                        "title": title,
                        "link": link,
                        "outcome": outcome,
                        "source": source,
                        "date": date_str,
                        "description": description or "No description available"
                    })
                    
                    # Debug output for successful extraction
                    st.write(f"Successfully extracted complaint: {title[:50]}...")
                    
                except Exception as e:
                    st.error(f"Error extracting complaint: {str(e)}")
                    continue
            
            return complaints
        
        except Exception as e:
            st.error(f"No initial results found: {str(e)}")
            return []
        
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
            end_date = datetime(year, month, 15, 23, 59, 59)
        else:
            last_day = calendar.monthrange(year, month)[1]
            start_date = datetime(year, month, 16)
            end_date = datetime(year, month, last_day, 23, 59, 59)
        st.write(f"**Date Range**: {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}")
    else:
        # Convert date input to datetime
        start_date = datetime.combine(
            st.date_input("Start Date", value=datetime.today()), 
            datetime.min.time()
        )
        end_date = datetime.combine(
            st.date_input("End Date", value=datetime.today()), 
            datetime.max.time()
        )
        if start_date > end_date:
            st.error("End Date must be on or after Start Date.")
            return

    if st.button("Scrape Data"):
        with st.spinner("Scraping data..."):
            complaints = scrape_complaints(start_date, end_date, headless=not dev_mode)
            if complaints:
                # Store complaints in session state
                st.session_state['complaints'] = complaints
                df = pd.DataFrame(complaints)
                st.success(f"Scraped {len(df)} complaints within the date range!")
                st.write("### Sample Data (First 5 Entries)")
                st.dataframe(df.head(5))
                
                # Download JSON button
                json_data = df.to_json(orient="records", indent=4)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name="complaint_outcomes.json",
                    mime="application/json"
                )
            else:
                st.warning("No complaints found within the selected date range.")
    
    # Only show these buttons if we have complaints data
    if 'complaints' in st.session_state:
        if st.button("Fetch Detailed Descriptions"):
            with st.spinner("Fetching detailed descriptions..."):
                detailed_complaints = get_detailed_complaints(
                    st.session_state['complaints'],
                    headless=not dev_mode
                )
                st.session_state['detailed_complaints'] = detailed_complaints
                st.success("Fetched detailed descriptions!")
                
                # Show preview of detailed descriptions
                st.write("### Detailed Descriptions Preview")
                for complaint in detailed_complaints:
                    with st.expander(f"{complaint['title']} ({complaint['date']})"):
                        st.write("**Original Description:**")
                        st.write(complaint['description'])
                        st.write("**Detailed Description:**")
                        st.write(complaint.get('detailed_description', 'No detailed description available'))
                        st.write("---")
                        st.write(f"Source: {complaint['source']}")
                        st.write(f"Outcome: {complaint['outcome']}")
                        st.markdown(f"[View Original]({complaint['link']})")
        
        if st.button("Generate Newsletter"):
            with st.spinner("Generating newsletter..."):
                complaints_data = st.session_state.get(
                    'detailed_complaints',
                    st.session_state['complaints']
                )
                newsletter = generate_newsletter(complaints_data)
                if newsletter:
                    st.success("Newsletter generated!")
                    st.markdown(newsletter)
                    st.download_button(
                        label="Download Newsletter",
                        data=newsletter,
                        file_name="asci_newsletter.md",
                        mime="text/markdown"
                    )
                else:
                    st.error("Failed to generate newsletter. Check if GEMINI_API_KEY is set in .env file")

if __name__ == "__main__":
    main()