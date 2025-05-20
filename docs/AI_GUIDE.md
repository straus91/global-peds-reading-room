# AI Assistant Guide - Global Peds Reading Room

## Quick Context

This is the Global Peds Reading Room - a medical education platform for pediatric radiology. Current development is heavily focused on enhancing the AI-powered feedback system for user-submitted reports using Google Gemini.

## Key Files for AI Feedback Development

### Backend (Django)
- **`cases/models.py`**:
    - `Case`: Contains crucial context for AI (new `case_identifier`, `patient_sex`, existing `clinical_history`, `key_findings`, `diagnosis`, `discussion`, `difficulty`).
    - `CaseTemplateSectionContent`: Now has `key_concepts_text` for admin-defined, case-specific, section-linked concepts to guide AI.
    - `AIFeedbackRating`: New model to store user ratings of AI feedback.
- **`cases/llm_feedback_service.py`**:
    - `get_feedback_from_llm()`: Core function interacting with Gemini. Prompt is significantly enhanced to use more context, receive pre-analysis, and request structured output (severity, justifications).
- **`cases/utils.py`**:
    - `generate_report_comparison_summary()`: New function for programmatic pre-analysis of user vs. expert reports.
- **`cases/views.py`**:
    - `AIReportFeedbackView`: Orchestrates data gathering, calls pre-analysis, calls LLM service, and structures the AI feedback response as JSON.
    - `AIFeedbackRatingCreateView`: New view to save user ratings on AI feedback.
- **`cases/serializers.py`**: Updated for new model fields and the `AIFeedbackRating` model.

### Frontend (Vanilla JS)
- **`js/main.js`**:
    - `displayUserSubmittedReport()`: Will fetch and eventually display the structured AI feedback (currently displays raw text). Will also host the UI for `addFeedbackRatingUI`.
    - `viewCase()`: Needs to be updated to display the new UI for AI feedback (Point 8).
- **`js/admin-case-edit.js`**: Updated to allow admins to input `patient_sex` for cases and `key_concepts_text` for expert template sections.

## Common Tasks Related to AI Feedback

### Enhancing AI Prompt or Logic
1.  Modify `cases/llm_feedback_service.py` (prompt engineering, interaction with Gemini).
2.  If new data is needed for the prompt, update `AIReportFeedbackView` in `cases/views.py` to gather and pass it.
3.  If the structure of the pre-analysis changes, update `cases/utils.py` and how `AIReportFeedbackView` uses it.

### Changing AI Feedback Display (Frontend)
1.  Modify `AIReportFeedbackView` (`_parse_llm_feedback_text` method in `cases/views.py`) if the backend needs to change how it structures the JSON response from the LLM's text.
2.  Modify `frontend/js/main.js` (primarily `displayUserSubmittedReport` and later the Point 8 UI overhaul) to render the structured AI feedback.

## Important Patterns for AI Feedback
- **Context is Key:** The AI (Gemini) receives comprehensive case details (ID, demographics, history, difficulty) and expert summaries (`key_findings`, `diagnosis`, `discussion` from `Case` model).
- **Programmatic Pre-analysis:** The backend performs an initial comparison (user section text vs. expert section text; user impression vs. `Case.diagnosis`; presence of admin-defined `key_concepts_text` from `CaseTemplateSectionContent` in user's sections) to guide the LLM.
- **Structured Output Goal:** The API aims to provide structured JSON feedback to the frontend (overall alignment, section-by-section analysis with severity/justification, key learning points).
- **User Feedback Loop:** Users will be able to rate the AI's feedback (1-5 stars, optional comment) via the new `AIFeedbackRating` system.
- **Non-Spoiling Case IDs:** Use `case_identifier` for user-facing elements and LLM context.

## Recent Backend Enhancements (May 17, 2025)
- Added `case_identifier`, `patient_sex` to `Case` model.
- Added `key_concepts_text` to `CaseTemplateSectionContent` for admin input.
- Implemented `generate_report_comparison_summary` for programmatic pre-analysis.
- Overhauled `get_feedback_from_llm` prompt and signature to accept more context and request severity.
- `AIReportFeedbackView` now provides more context to LLM and structures output into JSON.
- Added `AIFeedbackRating` model and API for users to rate AI feedback.
