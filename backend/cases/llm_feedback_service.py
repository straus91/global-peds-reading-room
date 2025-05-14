# backend/cases/llm_feedback_service.py
import os
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
import traceback

# --- Module-level configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
IS_GEMINI_CONFIGURED = False

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        IS_GEMINI_CONFIGURED = True
        print("llm_feedback_service.py - Gemini API configured successfully at module load.")
    except Exception as e:
        print(f"Error configuring Gemini API in llm_feedback_service.py at module load: {e}")
        IS_GEMINI_CONFIGURED = False
else:
    print("WARNING: llm_feedback_service.py - GEMINI_API_KEY environment variable not found at module load.")
# --- End Module-level configuration ---

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
        if not content: # If content is empty or only whitespace
            content = "N/A"
        report_text.append(f"Section: {section_name}\nContent: {content}\n")
    
    return "\n".join(report_text) if report_text else "No content available after formatting."

def get_feedback_from_llm(user_report_sections, expert_report_sections, case_title="", case_expert_key_findings=""):
    global IS_GEMINI_CONFIGURED

    if not IS_GEMINI_CONFIGURED:
        print("Gemini API was not configured successfully at module load. API key might be missing or invalid.")
        return "AI feedback service is not configured correctly (API key issue or configuration error)."

    user_report_str = format_report_for_llm(user_report_sections)
    expert_report_str = format_report_for_llm(expert_report_sections)
    
    # This line defines expert_key_findings_str before it's used in the prompt
    expert_key_findings_str = case_expert_key_findings if case_expert_key_findings and case_expert_key_findings.strip() else "Not specified by the case creator."

    # Using "Option 1: More Concise MVP Prompt"
    prompt = f"""
    You are an expert pediatric radiology educator providing concise and targeted feedback on a trainee's diagnostic report.
    Case Title: "{case_title if case_title else 'Not specified'}".

    TRAINEE'S REPORT:
    ---
    {user_report_str}
    ---

    EXPERT'S REPORT (for comparison):
    ---
    {expert_report_str}
    ---

    **Your Task: Provide a concise critique focusing on significant differences and errors.**

    **Feedback Format:**

    **I. Section-by-Section Discrepancy Analysis:**
    Go through each section present in the TRAINEE'S REPORT.
    * If a trainee's section is generally consistent with the EXPERT'S REPORT (even if wording differs), state: "[Section Name]: Consistent with expert report." or simply omit comment for that section to save space.
    * **If there's a significant discrepancy, omission, or error in a trainee's section compared to the expert's:**
        1.  State the section name (e.g., "Findings:", "Impression:").
        2.  Clearly describe the main discrepancy or error.
        3.  Explain the clinical significance or reasoning why this difference matters.
    * **For the TRAINEE'S IMPRESSION section:** This is the most critical.
        * If it deviates significantly from the EXPERT'S IMPRESSION, analyze *why*. Did the trainee misinterpret a finding? Did they miss a key imaging pattern detailed in the expert's findings that would lead to a different impression? Be specific about the reasoning error if possible.
        * If the trainee's Impression is significantly different, this section of your feedback should be the most detailed.

    **II. Key Learning Points & Actionable Advice (Concise):**
    * Based *only* on the significant discrepancies you identified above, list 1-3 critical learning points for the trainee.
    * For each learning point, provide a brief, actionable suggestion for improvement.

    **General Instructions for Your Output:**
    -   Focus *only* on what is different or incorrect in the trainee's report compared to the expert standard. Do not comment on parts that are correct or similar, unless it's a brief "Consistent with expert." for a section.
    -   Be direct and use clear, professional language.
    -   Maintain a constructive and educational tone.
    -   Provide *only* the feedback text, starting with "I. Section-by-Section Discrepancy Analysis:". Do not include any conversational preamble.
    -   Aim for brevity while ensuring critical points are covered.
    """

    print(f"---- PROMPT FOR GEMINI LLM (Case: '{case_title}') ----")
    # print(prompt) # Uncomment for debugging the full prompt if needed
    print("---- END PROMPT ----")

    try:
        model = genai.GenerativeModel('gemini-2.0-flash') # Using a generally available and efficient model
        
        response = model.generate_content(prompt)
        
        feedback_text = ""
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'text') and part.text:
                    feedback_text += part.text
        elif hasattr(response, 'text') and response.text:
            feedback_text = response.text
        
        if not feedback_text and hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason != 'STOP':
                print(f"LLM content generation potentially stopped or blocked. Reason: {candidate.finish_reason}")
                if hasattr(candidate, 'safety_ratings'): print(f"Safety Ratings: {candidate.safety_ratings}")
                if candidate.finish_reason == 'SAFETY': feedback_text = "The AI could not generate feedback for this content due to safety filters."
                elif candidate.finish_reason in ['RECITATION', 'OTHER']: feedback_text = "The AI could not generate feedback due to quality or other filters."
                else: feedback_text = "The AI did not return content due to an unspecified reason."
            else:
                feedback_text = "No feedback was generated by the AI (empty response received)."
        elif not feedback_text:
            feedback_text = "No feedback was generated by the AI (empty or unexpected response)."

        print("---- RAW LLM RESPONSE (Full) ----")
        try:
            print(response)
        except Exception as print_e:
            print(f"Could not print full LLM response object: {print_e}")
        print("---- EXTRACTED FEEDBACK ----")
        print(feedback_text.strip())
        print("---- END LLM ----")
            
        return feedback_text.strip()

    except GoogleAPIError as e:
        print(f"Google API Error calling Gemini API: {e}")
        return f"Sorry, an error occurred with the AI service (GoogleAPIError): {e}"
    except Exception as e:
        print(f"Unexpected error calling Gemini API: {e}")
        traceback.print_exc()
        return "Sorry, an unexpected error occurred while generating AI feedback."

# Example Usage (for testing this service directly if needed):
if __name__ == '__main__':
    print("Testing LLM feedback service directly...")
    
    if not IS_GEMINI_CONFIGURED:
        print("Attempting to load .env for standalone test as Gemini was not configured at module load.")
        from dotenv import load_dotenv
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
            GEMINI_API_KEY_TEST = os.environ.get("GEMINI_API_KEY")
            if GEMINI_API_KEY_TEST:
                try:
                    genai.configure(api_key=GEMINI_API_KEY_TEST)
                    IS_GEMINI_CONFIGURED = True 
                    print("GEMINI_API_KEY loaded and configured for standalone test.")
                except Exception as e:
                    print(f"Error configuring Gemini API during standalone test: {e}")
            else:
                print("GEMINI_API_KEY not found in .env for standalone test.")
        else:
            print(f".env file not found at {dotenv_path} for standalone test.")

    if IS_GEMINI_CONFIGURED:
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
        sample_case_key_findings_data = "The lungs are clear and there are no acute osseous abnormalities." # Example
        
        feedback = get_feedback_from_llm(
            user_report_sections=sample_user_report_sections, 
            expert_report_sections=sample_expert_report_sections, 
            case_title="Test Case: Pediatric Chest X-Ray",
            case_expert_key_findings=sample_case_key_findings_data # Pass the key findings
        )
        print("\n--- Generated Feedback (Standalone Test) ---")
        print(feedback)
    else:
        print("Skipping standalone LLM test as Gemini API is not configured.")