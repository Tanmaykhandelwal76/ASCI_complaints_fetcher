import google.generativeai as genai
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def generate_newsletter(complaints_data):
    """Generate a newsletter from complaints data using Gemini."""
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("Gemini API key not found in environment variables")
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare content for Gemini
        complaints_text = "\n\n".join([
            f"Title: {c['title']}\n"
            f"Date: {c['date']}\n"
            f"Outcome: {c['outcome']}\n"
            f"Source: {c['source']}\n"
            f"Description: {c.get('detailed_description', c['description'])}\n"
            for c in complaints_data
        ])
        
        prompt = f"""
        Create a professional newsletter summarizing the following ASCI complaints:
        
        {complaints_text}
        
        Format the newsletter with:
        1. A compelling headline
        2. Brief introduction about ASCI's recent activities
        3. Summary of all the complaints one by one and outcomes
        4. Trends and insights
        5. Conclusion
        
        Keep the tone professional and informative.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        logger.error(f"Newsletter generation failed: {str(e)}")
        return None
