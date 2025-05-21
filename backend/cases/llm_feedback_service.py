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
        return "No content provided for this report."
    
    report_text = []
    try:
        # Sort by section_order if available, to ensure consistent input to LLM
        # Ensure section_order is treated as a number for sorting, defaulting if not present
        sorted_sections = sorted(
            structured_content_list, 
            key=lambda x: x.get('section_order', float('inf')) if isinstance(x.get('section_order'), (int, float)) else float('inf')
        )
    except TypeError:
        print("Warning: Could not sort report sections by order (possibly due to mixed types or missing 'section_order'). Using original order.")
        sorted_sections = structured_content_list

    for section in sorted_sections:
        section_name = section.get('section_name', 'Unnamed Section')
        content = section.get('content', '').strip()
        if not content: 
            content = "N/A" # Represent empty sections clearly
        report_text.append(f"Section: {section_name}\nContent: {content}\n")
    
    return "\n".join(report_text) if report_text else "No content available after formatting."

def format_pre_analysis_for_llm(pre_analysis_summary):
    """
    Formats the programmatic pre-analysis summary into a readable string for the LLM.
    """
    if not pre_analysis_summary:
        return "No pre-analysis performed or summary available."

    lines = []
    
    # Overall Diagnosis Comparison
    diag_comp = pre_analysis_summary.get('overall_diagnosis_comparison', {})
    lines.append("Overall Diagnosis Comparison with Expert:")
    lines.append(f"- Status: {diag_comp.get('status', 'Not Assessed')}")
    if diag_comp.get('detail'):
        lines.append(f"- Detail: {diag_comp.get('detail')}")
    lines.append("-" * 3)

    # Section-by-Section Comparisons
    lines.append("Section-by-Section Pre-analysis:")
    section_comparisons = pre_analysis_summary.get('section_comparisons', [])
    if not section_comparisons:
        lines.append("  No specific section comparisons available.")
    else:
        for sc in section_comparisons:
            lines.append(f"- Section: {sc.get('section_name', 'Unknown Section')}")
            lines.append(f"  - Text vs. Expert Template: {sc.get('text_comparison_status', 'Unknown')}")
            key_concepts_status = sc.get('key_concepts_status', 'Not Applicable')
            lines.append(f"  - Case-Specific Key Concepts (for this section): {key_concepts_status}")
            if sc.get('missing_key_concepts'):
                lines.append(f"    - Potentially Missing Concepts: {', '.join(sc.get('missing_key_concepts'))}")
            lines.append("-" * 2) # Shorter separator for sections
    
    return "\n".join(lines)

# UPDATED FUNCTION SIGNATURE
def get_feedback_from_llm(
    user_report_sections, # List of dicts
    expert_report_sections, # List of dicts (from CaseTemplateSectionContent)
    programmatic_pre_analysis_summary, # Dict from generate_report_comparison_summary
    case_identifier_for_llm="", 
    case_patient_age="", 
    case_patient_sex="", 
    case_clinical_history="", 
    case_expert_key_findings="", # From Case.key_findings
    case_expert_diagnosis="",    # From Case.diagnosis
    case_expert_discussion="",   # From Case.discussion
    case_difficulty=""
    ):
    global IS_GEMINI_CONFIGURED

    if not IS_GEMINI_CONFIGURED:
        print("Gemini API was not configured successfully. API key might be missing or invalid.")
        return "AI feedback service is not configured correctly (API key issue or configuration error)."

    user_report_str = format_report_for_llm(user_report_sections)
    expert_report_str = format_report_for_llm(expert_report_sections)
    pre_analysis_str = format_pre_analysis_for_llm(programmatic_pre_analysis_summary)
    
    # Ensure all context strings have a fallback if None or empty
    case_identifier_for_llm = case_identifier_for_llm or "Not specified"
    case_patient_age = case_patient_age or "Not specified"
    case_patient_sex = case_patient_sex or "Not specified"
    case_clinical_history = case_clinical_history.strip() or "Not specified"
    case_expert_key_findings = case_expert_key_findings.strip() or "Not specified by case expert."
    case_expert_diagnosis = case_expert_diagnosis.strip() or "Not specified by case expert."
    case_expert_discussion = case_expert_discussion.strip() or "Not specified by case expert."
    case_difficulty = case_difficulty or "Not specified"

    prompt = f"""
You are an expert pediatric radiology educator providing direct, concise feedback to a trainee on their diagnostic report. Address the trainee directly using "you" and "your".

RELEVANT CASE INFORMATION:
Case Identifier: "{case_identifier_for_llm}"
Patient Age: "{case_patient_age}"
Patient Sex: "{case_patient_sex}"
Clinical History: "{case_clinical_history}"

EXPERT'S KEY FINDINGS, DIAGNOSIS AND DISCUSSION:
Key Findings: {case_expert_key_findings}
Final Diagnosis: {case_expert_diagnosis}
Discussion: {case_expert_discussion}

TRAINEE'S REPORT:
{user_report_str}

EXPERT'S REPORT:
{expert_report_str}

AUTOMATED PRE-ANALYSIS SUMMARY:
{pre_analysis_str}

FEEDBACK INSTRUCTIONS:

Provide a structured list of ONLY the issues and discrepancies in this exact format:

1. CRITICAL DISCREPANCIES:
   List only findings that would affect patient care or represent a significant diagnostic error. For each:
   - State exactly what was missed, incorrectly identified, or inappropriately emphasized
   - Begin each point with "You..." to address the trainee directly
   - Provide ONE brief sentence (15 words max) explaining why this is clinically important
   - Include any conceptual errors (e.g., misidentifying organ/structure or misclassifying pathology)

2. NON-CRITICAL DISCREPANCIES:
   List findings that differ but would not significantly impact immediate patient care. For each:
   - State the difference concisely, starting with "You..."
   - No explanation needed unless absolutely necessary for clarity

Rules:
- Do NOT include any introduction, conclusion, tips, or suggestions for improvement
- Do NOT comment on style differences, only substantive content differences
- Keep explanations extremely brief and focused on clinical significance
- If a category has no discrepancies, simply write "None identified."
- If the trainee completely missed the diagnosis, this is always a CRITICAL discrepancy
- Maximum 3-5 bullet points per category, prioritize the most important discrepancies
- Pay special attention to contradictions within the trainee's report itself
- Identify any misattributions (incorrect organ/structure identification) or misclassifications (wrong pathology type)

BEFORE SUBMITTING YOUR FEEDBACK:
1. Review each point for redundancy, - eliminate any repeated information and make sure critical and non-critical are not redundant (if they are, then keep only the critical)
2. Verify that each critical discrepancy includes a brief explanation of clinical importance
3. Check that all discrepancies are properly categorized as critical or non-critical based on patient care impact
4. Ensure you're addressing the trainee directly using "you" in each point
5. Remove any teaching advice or improvement suggestions
6. Confirm you've prioritized the most significant discrepancies if there are many
"""

    print(f"---- PROMPT FOR GEMINI LLM (Case ID: '{case_identifier_for_llm}') ----")
    # print(prompt) # Uncomment for full prompt debugging if needed
    print("---- END PROMPT ----")

    try:
        # Updated model name based on common availability, adjust if you have access to specific versions
        model = genai.GenerativeModel('gemini-1.5-flash-latest') 
        
        response = model.generate_content(prompt)
        
        feedback_text = ""
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'text') and part.text:
                    feedback_text += part.text
        elif hasattr(response, 'text') and response.text: # Fallback for simpler response structures
            feedback_text = response.text
        
        # Check for blocked content or other non-STOP finish reasons
        if not feedback_text and hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason != 'STOP':
                print(f"LLM content generation potentially problematic. Reason: {candidate.finish_reason}")
                if hasattr(candidate, 'safety_ratings'): print(f"Safety Ratings: {candidate.safety_ratings}")
                
                if candidate.finish_reason == 'SAFETY':
                    feedback_text = "AI feedback could not be generated for this content due to safety filters. Please review the reports for any sensitive or inappropriate material."
                elif candidate.finish_reason == 'MAX_TOKENS':
                    feedback_text = "AI feedback generation was stopped because the maximum output length was reached. The feedback might be incomplete."
                elif candidate.finish_reason in ['RECITATION', 'OTHER']:
                    feedback_text = "AI feedback could not be generated due to content quality or other filters."
                else:
                    feedback_text = f"AI feedback generation stopped for an unspecified reason: {candidate.finish_reason}."
            elif not feedback_text: # If finish_reason was STOP but still no text
                 feedback_text = "No feedback was generated by the AI (empty response received despite successful completion)."
        elif not feedback_text: # If no parts and no text attribute
            feedback_text = "No feedback was generated by the AI (empty or unexpected response structure)."

        print("---- RAW LLM RESPONSE (Full Object) ----")
        try:
            print(response) # Print the full response object for debugging
        except Exception as print_e:
            print(f"Could not print full LLM response object: {print_e}")
        print("---- EXTRACTED FEEDBACK TEXT ----")
        print(feedback_text.strip())
        print("---- END LLM ----")
            
        return feedback_text.strip()

    except GoogleAPIError as e:
        print(f"Google API Error calling Gemini API: {e}")
        return f"Sorry, an error occurred with the AI service (GoogleAPIError): {e.message if hasattr(e, 'message') else e}"
    except Exception as e:
        print(f"Unexpected error calling Gemini API: {e}")
        traceback.print_exc()
        return "Sorry, an unexpected error occurred while generating AI feedback."

# Example Usage (for testing this service directly if needed):
# (Keep this section for your own testing if desired, but ensure IS_GEMINI_CONFIGURED is handled)
if __name__ == '__main__':
    print("Testing LLM feedback service directly...")
    
    # Simplified test without re-loading .env here, assuming it's loaded if run via manage.py or configured externally
    if IS_GEMINI_CONFIGURED:
        sample_user_report_sections = [
            {"section_name": "Findings", "content": "Lungs are clear. Heart size appears normal.", "section_order": 1, "master_template_section_id": 1},
            {"section_name": "Impression", "content": "Normal chest x-ray.", "section_order": 2, "master_template_section_id": 2}
        ]
        sample_expert_section_contents = [ # Simulating CaseTemplateSectionContent objects
            {'master_section_id': 1, 'content': "The lungs are well aerated. No focal consolidation, pleural effusion, or pneumothorax detected.", 'key_concepts_text': "clear lungs;no effusion;no pneumothorax", 'section_name': "Lungs and Pleura", 'section_order': 1},
            {'master_section_id': 2, 'content': "Normal chest radiographic study.", 'key_concepts_text': "normal study", 'section_name': "Impression", 'section_order': 4}, # Order might differ
        ]
        
        sample_pre_analysis = {
            'overall_diagnosis_comparison': {'status': 'Aligns with Expert Diagnosis', 'detail': "User's impression mentions 'Normal chest x-ray', expert is 'Normal chest radiographic study'."},
            'section_comparisons': [
                {
                    'section_name': 'Findings', 'master_template_section_id': 1, 
                    'text_comparison_status': 'Content Differs', 
                    'key_concepts_status': 'Some Missing', 'missing_key_concepts': ['no effusion', 'no pneumothorax'],
                    'user_content_preview': 'Lungs are clear. Heart size appears normal.', 
                    'expert_content_preview': 'The lungs are well aerated. No focal consolidation, pleural effusion, or pneumothorax detected.'
                },
                {
                    'section_name': 'Impression', 'master_template_section_id': 2, 
                    'text_comparison_status': 'Content Differs', # Even if similar, for testing
                    'key_concepts_status': 'All Addressed', 'missing_key_concepts': [],
                    'user_content_preview': 'Normal chest x-ray.', 
                    'expert_content_preview': 'Normal chest radiographic study.'
                }
            ]
        }

        feedback = get_feedback_from_llm(
            user_report_sections=sample_user_report_sections, 
            expert_report_sections=sample_expert_section_contents, # Pass the list of dicts
            programmatic_pre_analysis_summary=sample_pre_analysis,
            case_identifier_for_llm="PEDS-XR-2025-001",
            case_patient_age="5 years",
            case_patient_sex="Male",
            case_clinical_history="Routine check-up.",
            case_expert_key_findings="Lungs clear, no acute osseous abnormalities.",
            case_expert_diagnosis="Normal chest.",
            case_expert_discussion="This is a standard normal pediatric chest X-ray.",
            case_difficulty="Beginner"
        )
        print("\n--- Generated Feedback (Standalone Test) ---")
        print(feedback)
    else:
        print("Skipping standalone LLM test as Gemini API is not configured.")

