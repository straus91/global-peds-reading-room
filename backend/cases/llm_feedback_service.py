# backend/cases/llm_feedback_service.py
import os
import re
import time
import logging
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
import traceback
from functools import lru_cache
from django.conf import settings

# Configure logger
logger = logging.getLogger(__name__)

# --- Module-level configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
IS_GEMINI_CONFIGURED = False

# Compile regex patterns once for reuse
PROMPT_INJECTION_PATTERN = re.compile(r'(ignore previous instructions|ignore above instructions|stop using template|exit role)', re.IGNORECASE)

# Rate limiting settings
MAX_CALLS_PER_MINUTE = getattr(settings, 'GEMINI_API_RATE_LIMIT', 10)
API_CALL_HISTORY = []

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        IS_GEMINI_CONFIGURED = True
        logger.info("Gemini API configured successfully at module load.")
    except Exception as e:
        logger.error(f"Error configuring Gemini API at module load: {e}")
        IS_GEMINI_CONFIGURED = False
else:
    logger.warning("GEMINI_API_KEY environment variable not found at module load.")
# --- End Module-level configuration ---

def sanitize_text(text):
    """
    Sanitize input text to prevent prompt injection and other issues.
    
    Args:
        text: The text to sanitize
    
    Returns:
        Sanitized text string
    """
    if not isinstance(text, str):
        return "" if text is None else str(text)
    
    # Remove potential prompt injection patterns
    sanitized = PROMPT_INJECTION_PATTERN.sub('', text)
    
    # Limit extremely long inputs
    if len(sanitized) > 10000:  # Reasonable limit for section content
        sanitized = sanitized[:10000] + "... [content truncated due to length]"
        
    return sanitized

def format_report_for_llm(structured_content_list, highlight_different_sections=False, identical_section_ids=None):
    """
    Helper to format structured report content into a readable string for the LLM.
    
    Args:
        structured_content_list: List of section content dictionaries
        highlight_different_sections: If True, will mark sections that differ from expert report
        identical_section_ids: Set of section IDs that are identical to expert report (used with highlight_different_sections)
    """
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
        logger.warning("Could not sort report sections by order (possibly due to mixed types or missing 'section_order'). Using original order.")
        sorted_sections = structured_content_list

    for section in sorted_sections:
        section_name = sanitize_text(section.get('section_name', 'Unnamed Section'))
        content = sanitize_text(section.get('content', '')).strip()
        section_id = section.get('master_template_section_id')
        
        if not content: 
            content = "N/A" # Represent empty sections clearly
            
        # Mark if this section is identical to expert report (for optimization)
        if highlight_different_sections and identical_section_ids and section_id in identical_section_ids:
            # If section is identical, mark it for the LLM
            report_text.append(f"Section: {section_name} [IDENTICAL TO EXPERT REPORT]\nContent: {content}\n")
        else:
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
    lines.append(f"- Status: {sanitize_text(diag_comp.get('status', 'Not Assessed'))}")
    if diag_comp.get('detail'):
        lines.append(f"- Detail: {sanitize_text(diag_comp.get('detail'))}")
    lines.append("-" * 3)

    # Section-by-Section Comparisons
    lines.append("Section-by-Section Pre-analysis:")
    section_comparisons = pre_analysis_summary.get('section_comparisons', [])
    if not section_comparisons:
        lines.append("  No specific section comparisons available.")
    else:
        for sc in section_comparisons:
            lines.append(f"- Section: {sanitize_text(sc.get('section_name', 'Unknown Section'))}")
            lines.append(f"  - Text vs. Expert Template: {sanitize_text(sc.get('text_comparison_status', 'Unknown'))}")
            key_concepts_status = sanitize_text(sc.get('key_concepts_status', 'Not Applicable'))
            lines.append(f"  - Case-Specific Key Concepts (for this section): {key_concepts_status}")
            if sc.get('missing_key_concepts'):
                missing_concepts = [sanitize_text(concept) for concept in sc.get('missing_key_concepts', [])]
                lines.append(f"    - Potentially Missing Concepts: {', '.join(missing_concepts)}")
            lines.append("-" * 2) # Shorter separator for sections
    
    return "\n".join(lines)

def check_rate_limit():
    """
    Check if we're within API rate limits.
    Returns True if we can proceed, False if we need to wait.
    """
    global API_CALL_HISTORY
    current_time = time.time()
    
    # Remove timestamps older than 60 seconds
    API_CALL_HISTORY = [t for t in API_CALL_HISTORY if current_time - t < 60]
    
    # If we have capacity, return True
    if len(API_CALL_HISTORY) < MAX_CALLS_PER_MINUTE:
        API_CALL_HISTORY.append(current_time)
        return True
    
    # Otherwise, we've hit the rate limit
    return False

@lru_cache(maxsize=1)
def get_gemini_model():
    """
    Returns a cached instance of the Gemini model to avoid recreation.
    """
    try:
        return genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        logger.error(f"Failed to create Gemini model instance: {e}")
        return None

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
    case_difficulty="",
    identical_section_ids=None   # NEW: Set of section IDs that are identical to expert report
    ):
    global IS_GEMINI_CONFIGURED

    if not IS_GEMINI_CONFIGURED:
        logger.error("Gemini API was not configured successfully. API key might be missing or invalid.")
        return "AI feedback service is not configured correctly (API key issue or configuration error)."

    # Check rate limiting
    if not check_rate_limit():
        logger.warning(f"API rate limit reached ({MAX_CALLS_PER_MINUTE} calls per minute). Request delayed.")
        # Add some jitter to prevent synchronized retries
        time.sleep(3 + (time.time() % 2))
        # Check again after delay
        if not check_rate_limit():
            logger.error("Rate limit still exceeded after delay. Aborting request.")
            return "AI feedback service is currently experiencing high demand. Please try again in a moment."

    # Format reports, highlighting identical sections to optimize LLM focus
    user_report_str = format_report_for_llm(
        user_report_sections, 
        highlight_different_sections=True, 
        identical_section_ids=identical_section_ids
    )
    expert_report_str = format_report_for_llm(expert_report_sections)
    pre_analysis_str = format_pre_analysis_for_llm(programmatic_pre_analysis_summary)
    
    # Ensure all context strings have a fallback if None or empty and sanitize inputs
    case_identifier_for_llm = sanitize_text(case_identifier_for_llm or "Not specified")
    case_patient_age = sanitize_text(case_patient_age or "Not specified")
    case_patient_sex = sanitize_text(case_patient_sex or "Not specified")
    case_clinical_history = sanitize_text(case_clinical_history.strip() or "Not specified")
    case_expert_key_findings = sanitize_text(case_expert_key_findings.strip() or "Not specified by case expert.")
    case_expert_diagnosis = sanitize_text(case_expert_diagnosis.strip() or "Not specified by case expert.")
    case_expert_discussion = sanitize_text(case_expert_discussion.strip() or "Not specified by case expert.")
    case_difficulty = sanitize_text(case_difficulty or "Not specified")

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

You will provide two separate feedback components:

PART 1 - DISCREPANCY LIST: 
Provide a very brief sentence (15 words max), if the trainee got the right diagnosis or not, and what it was.
Begin each point with "You..." to address the trainee directly
Provide a structured list of ONLY the issues and discrepancies in this exact format:

1. CRITICAL DISCREPANCIES:
   List only findings that would affect patient care or represent a significant diagnostic error. For each:
   - State exactly what was missed, incorrectly identified, or inappropriately emphasized
   - Begin each point with "You..." to address the trainee directly
   - Provide ONE brief sentence (15 words max) explaining why this is radiologically important
   - Include any conceptual errors (e.g., misidentifying organ/structure or misclassifying pathology)

2. NON-CRITICAL DISCREPANCIES:
   List findings that differ but would not significantly impact immediate patient care. For each:
   - State the difference concisely, starting with "You..."
   - No explanation needed unless absolutely necessary for clarity

Rules for Part 1:
- Do NOT include any introduction, conclusion, tips, or suggestions for improvement
- Do NOT comment on style differences, only substantive content differences
- Keep explanations extremely brief and focused on clinical significance
- If a category has no discrepancies, simply write "None identified."
- If the trainee completely missed the diagnosis, this is always a CRITICAL discrepancy
- Maximum 3-5 bullet points per category, prioritize the most important discrepancies
- Pay special attention to contradictions within the trainee's report itself
- Identify any misattributions (incorrect organ/structure identification) or misclassifications (wrong pathology type)

PART 2 - SECTION-BY-SECTION SEVERITY ASSESSMENT:
After the discrepancy list, add the heading "SECTION SEVERITY ASSESSMENT:" and create a structured JSON-like list that evaluates each section with exactly this format:

SECTION SEVERITY ASSESSMENT:
Section: [Section Name]
Severity: [Critical|Moderate|Consistent]
Reason: [1-2 sentence explanation]

Section: [Section Name]
Severity: [Critical|Moderate|Consistent]
Reason: [1-2 sentence explanation]

(and so on for each section)

Rules for Part 2:
- The severity levels must be EXACTLY one of: "Critical", "Moderate", or "Consistent" (no variations)
- "Critical" = Major discrepancy that could impact patient care
- "Moderate" = Notable difference but would not affect immediate care 
- "Consistent" = Section aligns well with expert assessment
- Always include EVERY section from the trainee's report
- For each section, explain why you assigned that severity in 1-2 sentences maximum
- Sections with missing critical findings should be marked as "Critical"
- Focus on radiological impact when assigning severity levels
- EFFICIENCY NOTE: Sections marked with [IDENTICAL TO EXPERT REPORT] should always be rated as "Consistent" without detailed analysis

BEFORE SUBMITTING YOUR FEEDBACK:
1. Review each point for redundancy - eliminate any repeated information
2. Verify that each critical discrepancy includes a brief explanation of clinical importance
3. Check that all discrepancies are properly categorized based on patient care impact
4. Ensure you've assigned a severity level for EVERY section in the trainee's report
5. Double-check that any section mentioning pneumothorax is marked as "Critical"
6. Format the section assessment exactly as specified above for proper parsing
"""

    logger.info(f"Preparing prompt for Gemini LLM (Case ID: '{case_identifier_for_llm}')")
    logger.debug(f"Prompt length: {len(prompt)} characters")
    # logger.debug(f"Full prompt: {prompt}") # Uncomment for full prompt debugging if needed

    start_time = time.time()
    try:
        # Get cached model instance
        model = get_gemini_model()
        if not model:
            return "AI feedback service encountered an error with the model configuration."
        
        # Set safety settings to allow medical content
        safety_settings = [
            {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
        ]
        
        # Generate content with safety settings
        response = model.generate_content(prompt, safety_settings=safety_settings)
        
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
                logger.warning(f"LLM content generation issue. Reason: {candidate.finish_reason}")
                if hasattr(candidate, 'safety_ratings'): 
                    logger.warning(f"Safety Ratings: {candidate.safety_ratings}")
                
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

        # Log performance metrics
        elapsed_time = time.time() - start_time
        logger.info(f"LLM response received in {elapsed_time:.2f} seconds (Case ID: '{case_identifier_for_llm}')")
        logger.debug(f"Response length: {len(feedback_text)} characters")
            
        return feedback_text.strip()

    except GoogleAPIError as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Google API Error calling Gemini API after {elapsed_time:.2f}s: {e}")
        error_type = type(e).__name__
        
        # Provide more specific error messages based on error type
        if "quota" in str(e).lower() or "rate" in str(e).lower():
            return "The AI service has reached its quota limit. Please try again later or contact support."
        elif "invalid" in str(e).lower() and "key" in str(e).lower():
            return "The AI service is misconfigured (API key issue). Please contact support."
        elif "timeout" in str(e).lower() or "deadline" in str(e).lower():
            return "The AI service took too long to respond. Please try again or contact support if this persists."
        else:
            # Generic error but don't expose internal details to end users
            logger.error(f"Detailed error: {traceback.format_exc()}")
            return f"Sorry, an error occurred with the AI service ({error_type}). Please try again later."
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Unexpected error calling Gemini API after {elapsed_time:.2f}s: {e}")
        logger.error(f"Detailed error: {traceback.format_exc()}")
        
        # Don't expose internal error details to end users
        error_type = type(e).__name__
        return f"Sorry, an unexpected error ({error_type}) occurred. Please try again later or contact support if this persists."

# Example Usage (for testing this service directly if needed):
# (Keep this section for your own testing if desired, but ensure IS_GEMINI_CONFIGURED is handled)
if __name__ == '__main__':
    logger.info("Testing LLM feedback service directly...")
    
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
        logger.info("Generated feedback for test case")
        logger.debug(f"Feedback length: {len(feedback)} characters")
    else:
        logger.warning("Skipping standalone LLM test as Gemini API is not configured.")

