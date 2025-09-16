AI Assistant Guide - Global Peds Reading RoomThis guide provides an in-depth look into the architecture, implementation, and development patterns of the AI-powered feedback system within the Global Peds Reading Room platform. The system leverages Google Gemini to provide constructive critiques on user-submitted radiology reports.1. Context and Goals of the AI Feedback SystemThe primary goal of the AI feedback system is to enhance the learning experience for medical professionals by providing automated, intelligent, and structured critiques of their diagnostic reports. This system aims to:Simulate Expert Review: Offer feedback that mimics an expert radiologist's review.Identify Discrepancies: Highlight key differences, omissions, or errors between a trainee's report and an expert's gold standard.Provide Actionable Advice: Guide trainees towards specific areas for improvement and further study.Scale Learning: Enable personalized feedback at scale, which is challenging with manual expert review.Improve Over Time: Incorporate user feedback on AI performance to continuously refine the system.2. Key Files and Their RolesThis section details the most critical files involved in the AI feedback pipeline.2.1 Backend (Django)cases/models.py:Case: Stores essential context for the AI, including case_identifier (non-spoiling ID), patient_sex, clinical_history, key_findings, diagnosis, discussion, and difficulty. These fields are crucial for grounding the AI's understanding.CaseTemplateSectionContent: Enhanced with key_concepts_text, an admin-defined field for specifying case-specific, section-linked key phrases that the AI should look for in user reports.AIFeedbackRating: A new model to capture user ratings (1-5 stars) and optional comments on the quality and helpfulness of the AI-generated feedback.cases/llm_feedback_service.py:This is the core service responsible for interacting with the Google Gemini API.get_feedback_from_llm(): The main function that constructs the prompt for Gemini. It accepts a comprehensive set of inputs including the user's report, expert report, programmatic pre-analysis, and all relevant case context. The prompt is carefully engineered to instruct Gemini on the desired structured output, including severity levels and justifications for discrepancies.cases/utils.py:generate_report_comparison_summary(): A utility function that performs a preliminary, programmatic comparison between a user's report and the expert's content. This pre-analysis identifies basic textual differences, checks for the presence of key_concepts_text in user sections, and compares the user's overall impression against the expert's diagnosis. The output of this function is then fed into the LLM prompt to guide Gemini.cases/views.py:AIReportFeedbackView: This APIView orchestrates the entire AI feedback generation process. It gathers all necessary data (user report, expert template, case context), calls generate_report_comparison_summary for pre-analysis, invokes llm_feedback_service.get_feedback_from_llm, and then processes Gemini's raw text response into a structured JSON format for the frontend.AIFeedbackRatingCreateView: A new API view responsible for receiving and saving user-submitted ratings for AI feedback into the AIFeedbackRating model.cases/serializers.py:Contains serializers for all cases app models. These are updated to handle the new fields (case_identifier, patient_sex, key_concepts_text) and the new AIFeedbackRating model. Serializers also define how the structured AI feedback is represented in API responses.2.2 Frontend (Vanilla JS)js/main.js:This file contains the core JavaScript logic for the user-facing application.displayUserSubmittedReport(): Responsible for fetching and displaying the user's submitted report. It is being updated to also fetch and render the structured AI feedback.viewCase(): Manages the display of the case detail page, including the integration points for the AI feedback UI.js/admin-case-edit.js:This script manages the "Add/Edit Case" form in the admin panel. It's updated to allow administrators to input patient_sex for cases and, crucially, to add/edit key_concepts_text for individual sections within expert-filled templates.3. Important Patterns for AI Feedback DevelopmentWhen developing or extending the AI feedback system, keep the following patterns in mind:Context is King: The quality of AI feedback heavily depends on the context provided. Ensure that the get_feedback_from_llm function receives all relevant case details (demographics, history, difficulty) and expert summaries (key_findings, diagnosis, discussion from the Case model).Programmatic Pre-analysis: Leverage generate_report_comparison_summary to perform initial, rule-based comparisons. This reduces the cognitive load on the LLM and helps it focus on more nuanced discrepancies.Admin-Guided AI (key_concepts_text): The key_concepts_text field in CaseTemplateSectionContent is a powerful tool for administrators to explicitly guide the AI on what constitutes a "key point" for a specific case and section. This improves the relevance and accuracy of AI feedback.Structured Output: Design the LLM prompt to encourage structured output (e.g., JSON-like format, clear headings, severity levels). This makes parsing and displaying the feedback on the frontend much easier and more consistent.User Feedback Loop: The AIFeedbackRating system is vital for continuous improvement. Encourage users to rate the AI's feedback, as this data can be used to fine-tune prompts or even retrain models in the future.Non-Spoiling Case IDs: Always use the case_identifier for user-facing elements and when passing case context to the LLM. The internal Case.title is for admin use only to prevent giving away the diagnosis.4. Common Development Tasks Related to AI Feedback4.1 Enhancing AI Prompt or Backend LogicModify LLM Prompt: The primary place to refine the AI's behavior is within the get_feedback_from_llm() function in cases/llm_feedback_service.py. Experiment with prompt engineering techniques to achieve desired feedback quality and format.Add New Context to Prompt: If the AI needs more information (e.g., specific image features), first ensure that data is available in the Case model or related models. Then, update AIReportFeedbackView in cases/views.py to gather this new data and pass it to get_feedback_from_llm(). Finally, update the prompt in llm_feedback_service.py to utilize this new context.Refine Pre-analysis: If the programmatic comparison needs to be more sophisticated, modify generate_report_comparison_summary() in cases/utils.py. Ensure its output format is consistent with what llm_feedback_service.py expects.4.2 Changing AI Feedback Display (Frontend)

Adjust Backend Output Structure: If the frontend requires a different JSON structure for the AI feedback, modify the _parse_llm_feedback_text method within AIReportFeedbackView in cases/views.py.

Update Frontend Rendering: The main task is to modify frontend/js/main.js (specifically displayUserSubmittedReport and the UI components it renders) to correctly parse and visually present the structured AI feedback. This includes handling severity levels (e.g., color-coding critical discrepancies), displaying learning points, and integrating the feedback rating UI.

Implement Feedback Rating UI: Develop the user interface for submitting 1-5 star ratings and comments on AI feedback. This UI will interact with the POST /api/cases/ai-feedback-ratings/ endpoint.

5. Recent Enhancements to the AI Feedback System

5.1 Section Color Coding
The system now provides visual color-coding for report sections based on their alignment with the expert assessment:
- Green (Consistent): Section aligns well with expert assessment
- Yellow (Moderate): Notable differences but would not affect immediate patient care
- Red (Critical): Major discrepancies that could impact patient care

This color-coding helps trainees quickly identify areas that need attention.

5.2 Optimized LLM Processing
The AI feedback system now includes optimization for more efficient LLM usage:

- Section Comparison Optimization: The system identifies sections that are identical to the expert report and marks them accordingly in the LLM prompt. These sections are automatically rated as "Consistent" without detailed analysis, saving tokens and processing time.

- Special Case Detection: Critical findings like pneumothorax are specially handled to ensure proper severity classification.

- Structured Section Assessment: The LLM now provides a specific section-by-section assessment with standardized severity levels (Critical/Moderate/Consistent) and justifications.

5.3 Improved Feedback Display
The AI feedback display has been redesigned to be cleaner and more focused:

- Discrepancy List: Shows critical and non-critical discrepancies in clearly separated, color-coded sections
- Proper HTML Formatting: Bullet points and paragraphs are properly formatted for readability
- Visual Differentiation: Different severity levels have distinct visual styling

5.4 Implementation Details

The optimization involves several components:
1. Backend preprocessing to identify identical sections (`generate_report_comparison_summary` in `utils.py`)
2. Enhanced report formatting to mark identical sections (`format_report_for_llm` in `llm_feedback_service.py`)
3. Updated LLM prompt with instructions for handling identical sections
4. Structured output format with section-by-section severity assessment
5. Revised frontend display for both report sections and AI feedback

This approach significantly improves efficiency while maintaining the quality of feedback for sections that require detailed analysis.

5.5 Security Enhancements

The AI feedback system has been enhanced with comprehensive security measures:

- **Input Sanitization**: All inputs to the LLM are now sanitized using the `sanitize_text()` function in `llm_feedback_service.py`, which prevents prompt injection attacks and other security issues.

- **Rate Limiting**: The system now includes a rate limiting mechanism through the `check_rate_limit()` function, which prevents abuse of the LLM API by enforcing a configurable maximum number of calls per minute.

- **Transactional Safety**: All database operations in `AIReportFeedbackView` and other critical views are now wrapped in Django's atomic transactions with savepoints, ensuring data integrity even if operations fail mid-execution.

- **Robust Error Handling**: The LLM service now has comprehensive error handling for various API error conditions, providing appropriate user-friendly error messages without exposing internal details.

- **Structured Logging**: Print statements have been replaced with proper Python logging, with different log levels for appropriate severity and consistent formatting.

- **Model Caching**: The Gemini model instance is now cached using Python's LRU cache, improving performance and reducing API initialization overhead.

- **Safety Settings**: API calls to Gemini now include safety settings optimized for medical content to prevent false positives in content filtering.

These security enhancements ensure the AI feedback system is robust, resilient to errors, and protected against potential misuse while maintaining high performance.