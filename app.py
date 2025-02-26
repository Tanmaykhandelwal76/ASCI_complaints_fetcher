import streamlit as st
from datetime import datetime
from scraper import scrape_complaints  # Import the scraper function

def main():
    st.title("ASCI Complaint Outcomes Scraper")
    st.write("Select a date range to scrape complaint outcomes from ASCI.")

    # Date range selection
    range_option = st.selectbox(
        "Choose Date Range",
        ["1st to 15th of February 2025", "16th to 28th of February 2025"]
    )

    if st.button("Scrape Data"):
        if range_option == "1st to 15th of February 2025":
            start_date = datetime(2025, 2, 1)
            end_date = datetime(2025, 2, 15)
        else:
            start_date = datetime(2025, 2, 16)
            end_date = datetime(2025, 2, 28)
        
        with st.spinner("Scraping data... This may take a few moments."):
            complaints = scrape_complaints(start_date, end_date)
        
        if complaints:
            st.success(f"Scraped {len(complaints)} complaints! Data saved to 'complaint_outcomes.json'.")
            st.write("Sample of scraped data:")
            st.json(complaints[:5])  # Show first 5 entries
        else:
            st.error("No complaints scraped. Check the logs for details.")

if __name__ == "__main__":
    main()  