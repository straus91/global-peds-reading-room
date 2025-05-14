# backend/cases/llm_feedback_service.py
import os
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError # For more specific error handling
import traceback # For more detailed error logging

# Configure the Gemini API key from environment variable
GEMINI_API_KEY = None
try:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("WARNING: llm_feedback_service.py - GEMINI_API_KEY environment variable not found at module load.")
    else:
        genai.configure(api_key=GEMINI_API_KEY)
        print("llm_feedback_service.py - Gemini API configured successfully at module load.")
except Exception as e:
    print(f"Error configuring Gemini API in llm_feedback_service.py at module load: {e}")


def format_report_for_llm(structured_content_list):
    """Helper to format structured report content into a readable string for the LLM."""
    if not structured_content_list:
        return "No content provided by the user for this report."
    
    report_text = []
    try:
        # Sort by section_order if available, to ensure consistent input to LLM
        sorted_sections = sorted(structured_content_list, key=lambda x: x.get('section_order', float('inf')))
    except TypeError:
        print("Warning: Could not sort report sections by order. Using original order.")
        sorted_sections = structured_content_list

    for section in sorted_sections:
        section_name = section.get('section_name', 'Unnamed Section')
        content = section.get('content', '').strip()
        if not content:
            content = "N/A"
        report_text.append(f"Section: {section_name}\nContent: {content}\n")
    
    return "\n".join(report_text) if report_text else "No content available after formatting."


def get_feedback_from_llm(user_report_sections, expert_report_sections, case_title=""):
    """
    Generates feedback by comparing a user's report to an expert's report using Gemini.
    """
    global GEMINI_API_KEY # Access the module-level variable
    if not GEMINI_API_KEY:
        # Attempt to re-load/re-configure if not set during initial module load
        # This can happen if env vars are set after initial Django startup in some dev server cases
        print("Retrying Gemini API key configuration in get_feedback_from_llm...")
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                print("Gemini API re-configured successfully within get_feedback_from_llm.")
            except Exception as e:
                print(f"Error re-configuring Gemini API in get_feedback_from_llm: {e}")
                return "AI feedback service is not configured (API key error during re-check)."
        else:
            print("GEMINI_API_KEY still not found during re-check.")
            return "AI feedback service is not configured (API key missing)."

    user_report_str = format_report_for_llm(user_report_sections)
    expert_report_str = format_report_for_llm(expert_report_sections)

    prompt = f"""
    You are an expert pediatric radiology educator reviewing a trainee's diagnostic report.
    The case is titled: "{case_title if case_title else 'Not specified'}".

    TRAINEE'S SUBMITTED REPORT:
    ---
    {user_report_str}
    ---

    EXPERT'S GOLD STANDARD REPORT (for comparison):
    ---
    {expert_report_str}
    ---

    Please provide constructive feedback for the trainee. Your feedback should:
    1. Start with a brief overall positive comment if appropriate.
    2. Clearly compare the trainee's findings and impression (if present) to the expert's report.
    3. Identify any significant discrepancies, missed findings, or overcalls in the trainee's report. Be specific.
    4. Acknowledge any key accurate observations made by the trainee.
    5. Offer specific suggestions for improvement in their reporting technique, interpretation, or areas to focus on for this type of case.
    6. Maintain an encouraging, supportive, and professional tone.
    7. Structure the feedback into logical paragraphs or bullet points for readability. For example:
       - Overall Impression:
       - Accurate Observations:
       - Areas for Improvement/Discrepancies:
       - Key Learning Points:

    Provide only the feedback text. Do not include any preamble like "Here's the feedback:".
    """

    print("---- PROMPT FOR GEMINI LLM ----")
    # print(prompt) # Uncomment for debugging the full prompt if needed, can be very long
    print(f"Prompt for case '{case_title}' sent to LLM.")
    print("---- END PROMPT ----")

    try:
        model = genai.GenerativeModel('gemini-1.0-pro') # Or 'gemini-1.5-flash' for a faster/cheaper option
        
        response = model.generate_content(prompt)
        
        feedback_text = ""
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'text'):
                    feedback_text += part.text
        elif hasattr(response, 'text'):
            feedback_text = response.text
        else:
            feedback_text = "Could not extract feedback text from LLM response."
            print(f"Unexpected LLM response structure: {response}")
            # If response.candidates is available and has safety ratings, it might indicate a block
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'finish_reason') and candidate.finish_reason != 'STOP':
                        print(f"LLM content generation stopped due to: {candidate.finish_reason}")
                        if hasattr(candidate, 'safety_ratings'):
                            print(f"Safety Ratings: {candidate.safety_ratings}")
                        # Provide a more user-friendly message if blocked
                        if candidate.finish_reason == 'SAFETY':
                             feedback_text = "The AI could not generate feedback for this content due to safety filters."
                        elif candidate.finish_reason in ['RECITATION', 'OTHER']:
                             feedback_text = "The AI could not generate feedback for this content due to quality filters."


        print("---- RAW LLM RESPONSE (parts) ----")
        if hasattr(response, 'parts'): print(response.parts)
        print("---- EXTRACTED FEEDBACK ----")
        print(feedback_text.strip())
        print("---- END LLM ----")
            
        return feedback_text.strip() if feedback_text else "No feedback was generated by the AI."

    except GoogleAPIError as e:
        print(f"Google API Error calling Gemini API: {e}")
        return f"Sorry, an error occurred with the AI service: {e}"
    except Exception as e:
        print(f"Unexpected error calling Gemini API: {e}")
        traceback.print_exc()
        return "Sorry, an unexpected error occurred while generating AI feedback."

# Example Usage (for testing this service directly if needed):
if __name__ == '__main__':
    print("Testing LLM feedback service directly...")
    
    if not GEMINI_API_KEY:
        print("Attempting to load .env for standalone test as GEMINI_API_KEY was not initially set.")
        from dotenv import load_dotenv
        # Assumes .env is in the 'backend' directory, one level up from 'cases'
        # Adjust path if your .env is elsewhere relative to this script for standalone testing
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
            GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
            if GEMINI_API_KEY:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    print("GEMINI_API_KEY loaded and configured for standalone test.")
                except Exception as e:
                    print(f"Error configuring Gemini API during standalone test: {e}")
                    GEMINI_API_KEY = None # Ensure it's None if config fails
            else:
                print("GEMINI_API_KEY not found in .env for standalone test.")
        else:
            print(f".env file not found at {dotenv_path} for standalone test.")

    if GEMINI_API_KEY:
        sample_user_report_sections = [
            {"section_name": "Findings", "content": "Lungs are clear. Heart size appears normal.", "section_order": 1},
            {"section_name": "Impression", "content": "Normal chest x-ray.", "section_order": 2}
        ]
        sample_expert_report_sections = [
            {"section_name": "Lungs and Pleura", "content": "The lungs are well aerated. No focal consolidation, pleural effusion, or pneumothorax detected.", "section_order": 1},
            {"section_name": "Mediastinum and Hila", "content": "The cardiomediastinal silhouette is within normal limits for the patient's age and inspiration. The hilar contours are normal.", "section_order": 2},
            {"section_name": "Bones and Soft Tissues", "content": "Visualized portions of the bony thorax and overlying soft tissues are unremarkable.", "section_order": 3},
            {"section_name": "Impression", "content": "Normal chest radiographic study.", "section_order": 4}
        ]
        feedback = get_feedback_from_llm(
            user_report_sections=sample_user_report_sections, 
            expert_report_sections=sample_expert_report_sections, 
            case_title="Test Case: Pediatric Chest X-Ray"
        )
        print("\n--- Generated Feedback (Standalone Test) ---")
        print(feedback)
    else:
        print("Skipping standalone LLM test as GEMINI_API_KEY is not available.")