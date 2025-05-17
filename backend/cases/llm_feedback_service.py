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
You are an expert pediatric radiology educator providing detailed, constructive feedback on a trainee's diagnostic report. Your goal is to help the trainee learn and improve.

RELEVANT CASE INFORMATION:
Case Identifier: "{case_identifier_for_llm}"
Patient Age: "{case_patient_age}"
Patient Sex: "{case_patient_sex}"
Clinical History Provided with Case:
---
{case_clinical_history}
---
Case Difficulty Level: "{case_difficulty}"

EXPERT'S SUMMARY FOR THIS SPECIFIC CASE (Ground Truth):
This information represents the definitive expert interpretation and key teaching points for this case.
Expert Key Findings for This Case:
---
{case_expert_key_findings}
---
Expert Final Diagnosis for This Case:
---
{case_expert_diagnosis}
---
Expert Discussion Summary for This Case:
---
{case_expert_discussion}
---

AUTOMATED PRE-ANALYSIS OF REPORT DIFFERENCES:
(This is a preliminary programmatic check. Use your expert judgment to verify, elaborate on these points, and identify any other significant discrepancies. Pay close attention to sections flagged as "Content Differs" or where key concepts appear to be missing, and the overall diagnosis comparison.)
---
{pre_analysis_str}
---

TRAINEE'S REPORT:
---
{user_report_str}
---

EXPERT'S REPORT (Full text for detailed comparison):
---
{expert_report_str}
---

**Your Task: Provide a structured critique of the TRAINEE'S REPORT.**

**Feedback Format and Instructions:**

**I. Overall Impression Alignment (Crucial):**
   - Start by commenting on how well the trainee's overall Impression/Conclusion aligns with the "Expert Final Diagnosis for This Case" provided above.
   - If there's a misalignment, this is a critical area. Explain the potential reasons for the difference based on the trainee's findings.

**II. Section-by-Section Discrepancy Analysis:**
   - Go through each section present in the TRAINEE'S REPORT (e.g., Findings, Technique, Comparison, Impression).
   - For each section:
     1. If the trainee's section is generally consistent with the EXPERT'S REPORT for that section and addresses any relevant "Case-Specific Key Concepts" (highlighted in the pre-analysis), you can state: "[Section Name]: Generally consistent with expert report and addresses key points." or omit detailed comment if no significant issues.
     2. **If there's a significant discrepancy, omission, or error in a trainee's section compared to the expert's content for that section OR if it fails to address relevant "Case-Specific Key Concepts" (see pre-analysis):**
        a. State the section name (e.g., "Findings:").
        b. Clearly describe the main discrepancy, error, or missed key concept.
        c. **Assign a severity level using an explicit prefix: "Severity: Critical - " OR "Severity: Moderate - ".**
           - **Critical Discrepancy:** An error or omission that would likely lead to a misdiagnosis, incorrect patient management, or has significant clinical safety implications.
           - **Moderate Discrepancy:** An error or omission that affects completeness, clarity, or accuracy, potentially leading to minor misinterpretation or requiring clarification, but less likely to directly cause immediate harm.
        d. Provide a brief (1-2 sentences) justification for the assigned severity and explain the clinical significance or reasoning why this difference matters. Focus on *why* it's an issue.
     3. **Do NOT report merely stylistic differences or use of exact synonyms as discrepancies if the core clinical meaning is preserved and accurate.** Focus on substantive differences.

**III. Key Learning Points & Actionable Advice (Concise - 2-3 points maximum):**
   - Based *only* on the significant discrepancies (Critical or Moderate) you identified above:
     1. List the most important learning points for the trainee.
     2. For each learning point, provide a brief, actionable suggestion for improvement or a specific area/topic they should review further. (e.g., "Learning Point: Missed subtle pneumothorax. Advice: Review techniques for optimal pneumothorax detection on supine radiographs. Topics for Further Study: pediatric pneumothorax imaging, supine chest X-ray interpretation.")

**General Instructions for Your Output:**
- Focus on what is different, incorrect, or omitted in the trainee's report compared to the expert standard and the provided case context.
- Be direct, professional, constructive, and educational.
- Provide *only* the feedback text, starting with "I. Overall Impression Alignment:". Do not include any conversational preamble or sign-off.
- Ensure your feedback is well-organized and easy to read using the specified section headers (I, II, III).
- Give feedback as if you were talking to the trainee directly, do not reference "the trainee", instead reference you.
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

