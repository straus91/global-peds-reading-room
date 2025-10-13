"""
Feedback Parser for LLM-generated AI feedback.

This module parses structured text responses from the LLM into a standardized
JSON format for storage in Report.ai_feedback_content and AIFeedbackDetailedRating.

Expected LLM Response Format:
-------------------------------
[Opening assessment paragraph]

1. CRITICAL DISCREPANCIES:
- You missed [finding]...
- You incorrectly identified [finding]...

2. NON-CRITICAL DISCREPANCIES:
- You did not mention [detail]...

SECTION SEVERITY ASSESSMENT:
Section: [Section Name]
Severity: [Critical|Moderate|Consistent]
Reason: [Explanation]

Section: [Another Section]
Severity: [...]
Reason: [...]
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class FeedbackParseError(Exception):
    """Raised when feedback parsing fails."""
    pass


def parse_ai_feedback(raw_feedback: str) -> Dict:
    """
    Parse raw LLM feedback text into structured format.

    Args:
        raw_feedback (str): Raw text response from LLM

    Returns:
        Dict with structure:
        {
            'raw_feedback': str,
            'overall_assessment': str,
            'critical_discrepancies': List[str],
            'non_critical_discrepancies': List[str],
            'section_feedback': List[Dict],
            'parse_success': bool,
            'parse_errors': List[str]
        }

    Example:
        >>> feedback = parse_ai_feedback(llm_response)
        >>> print(feedback['overall_assessment'])
        'You correctly identified the diagnosis.'
        >>> print(feedback['critical_discrepancies'])
        ['You missed the right-sided pneumothorax']
        >>> print(feedback['section_feedback'][0])
        {'section_name': 'Findings', 'severity': 'Critical', 'reason': '...'}
    """
    logger.info("Parsing AI feedback response")

    # Initialize result structure
    result = {
        'raw_feedback': raw_feedback,
        'overall_assessment': '',
        'critical_discrepancies': [],
        'non_critical_discrepancies': [],
        'section_feedback': [],
        'parse_success': True,
        'parse_errors': []
    }

    try:
        # 1. Extract overall assessment (everything before "1. CRITICAL DISCREPANCIES:")
        result['overall_assessment'] = _extract_overall_assessment(raw_feedback)

        # 2. Extract critical discrepancies
        result['critical_discrepancies'] = _extract_discrepancies(
            raw_feedback,
            section_number=1,
            section_name='CRITICAL DISCREPANCIES'
        )

        # 3. Extract non-critical discrepancies
        result['non_critical_discrepancies'] = _extract_discrepancies(
            raw_feedback,
            section_number=2,
            section_name='NON-CRITICAL DISCREPANCIES'
        )

        # 4. Extract section severity assessments
        result['section_feedback'] = _extract_section_assessments(raw_feedback)

        # 5. Validate parsed content
        _validate_parsed_feedback(result)

        logger.info(
            f"✅ Parsing successful: "
            f"{len(result['critical_discrepancies'])} critical, "
            f"{len(result['non_critical_discrepancies'])} non-critical, "
            f"{len(result['section_feedback'])} sections"
        )

    except FeedbackParseError as e:
        logger.error(f"❌ Parsing failed: {e}")
        result['parse_success'] = False
        result['parse_errors'].append(str(e))

    except Exception as e:
        logger.error(f"❌ Unexpected parsing error: {e}", exc_info=True)
        result['parse_success'] = False
        result['parse_errors'].append(f"Unexpected error: {str(e)}")

    return result


def _extract_overall_assessment(raw_feedback: str) -> str:
    """
    Extract the opening assessment paragraph (before discrepancy lists).

    Args:
        raw_feedback (str): Raw LLM response

    Returns:
        str: Overall assessment text (stripped)

    Example:
        >>> text = "You correctly identified the diagnosis.\\n\\n1. CRITICAL DISCREPANCIES:"
        >>> _extract_overall_assessment(text)
        'You correctly identified the diagnosis.'
    """
    # Find text before "1. CRITICAL DISCREPANCIES:"
    match = re.search(r'^(.*?)(?=1\.\s*CRITICAL DISCREPANCIES:)', raw_feedback, re.DOTALL)

    if match:
        assessment = match.group(1).strip()
        logger.debug(f"Extracted overall assessment: {assessment[:50]}...")
        return assessment
    else:
        logger.warning("Could not extract overall assessment - using first paragraph")
        # Fallback: use first paragraph
        first_paragraph = raw_feedback.split('\n\n')[0].strip()
        return first_paragraph


def _extract_discrepancies(raw_feedback: str, section_number: int, section_name: str) -> List[str]:
    """
    Extract discrepancy list items from a numbered section.

    Args:
        raw_feedback (str): Raw LLM response
        section_number (int): Section number (1 or 2)
        section_name (str): Section name for logging

    Returns:
        List[str]: List of discrepancy statements (without bullets)

    Example:
        >>> text = "1. CRITICAL DISCREPANCIES:\\n- You missed finding A\\n- You missed finding B\\n\\n2. NON-CRITICAL"
        >>> _extract_discrepancies(text, 1, 'CRITICAL DISCREPANCIES')
        ['You missed finding A', 'You missed finding B']
    """
    # Pattern: "1. CRITICAL DISCREPANCIES:" followed by bullet points
    pattern = rf'{section_number}\.\s*{re.escape(section_name)}:\s*(.*?)(?=\n\n|\n\d+\.|SECTION SEVERITY ASSESSMENT:|$)'

    match = re.search(pattern, raw_feedback, re.DOTALL | re.IGNORECASE)

    if not match:
        logger.warning(f"Could not find section: {section_number}. {section_name}")
        return []

    section_content = match.group(1).strip()

    # Check for "None identified" or similar
    if re.search(r'none\s+identified', section_content, re.IGNORECASE):
        logger.debug(f"{section_name}: None identified")
        return []

    # Extract bullet points (lines starting with -, •, *, or numbers)
    bullet_pattern = r'^[\s]*[-•*]\s*(.+?)$'
    discrepancies = []

    for line in section_content.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Match bullet points
        bullet_match = re.match(bullet_pattern, line)
        if bullet_match:
            discrepancy = bullet_match.group(1).strip()
            discrepancies.append(discrepancy)
            logger.debug(f"Found discrepancy: {discrepancy[:50]}...")

    logger.debug(f"Extracted {len(discrepancies)} items from {section_name}")
    return discrepancies


def _extract_section_assessments(raw_feedback: str) -> List[Dict]:
    """
    Extract section-by-section severity assessments.

    Args:
        raw_feedback (str): Raw LLM response

    Returns:
        List[Dict]: List of section assessments with structure:
        [
            {
                'section_name': str,
                'severity': str,  # 'Critical', 'Moderate', or 'Consistent'
                'reason': str
            },
            ...
        ]

    Example:
        >>> text = "SECTION SEVERITY ASSESSMENT:\\nSection: Findings\\nSeverity: Critical\\nReason: Major issue"
        >>> _extract_section_assessments(text)
        [{'section_name': 'Findings', 'severity': 'Critical', 'reason': 'Major issue'}]
    """
    # Find "SECTION SEVERITY ASSESSMENT:" section
    pattern = r'SECTION SEVERITY ASSESSMENT:\s*(.*?)$'
    match = re.search(pattern, raw_feedback, re.DOTALL | re.IGNORECASE)

    if not match:
        logger.warning("Could not find SECTION SEVERITY ASSESSMENT section")
        raise FeedbackParseError("Missing SECTION SEVERITY ASSESSMENT section")

    assessment_text = match.group(1).strip()

    # Parse individual section blocks
    # Format:
    # Section: [Name]
    # Severity: [Level]
    # Reason: [Explanation]
    section_pattern = r'Section:\s*(.+?)\s*\n\s*Severity:\s*(.+?)\s*\n\s*Reason:\s*(.+?)(?=\n\s*Section:|$)'

    sections = []
    for match in re.finditer(section_pattern, assessment_text, re.DOTALL | re.IGNORECASE):
        section_name = match.group(1).strip()
        severity = match.group(2).strip()
        reason = match.group(3).strip()

        # Validate severity level
        severity_normalized = _normalize_severity(severity)

        section_data = {
            'section_name': section_name,
            'severity': severity_normalized,
            'reason': reason
        }

        sections.append(section_data)
        logger.debug(f"Parsed section: {section_name} - {severity_normalized}")

    if not sections:
        logger.warning("No section assessments found in SECTION SEVERITY ASSESSMENT")
        raise FeedbackParseError("No valid section assessments found")

    logger.debug(f"Extracted {len(sections)} section assessments")
    return sections


def _normalize_severity(severity: str) -> str:
    """
    Normalize severity level to standard values.

    Args:
        severity (str): Raw severity from LLM (may have variations)

    Returns:
        str: Normalized severity ('Critical', 'Moderate', or 'Consistent')

    Raises:
        FeedbackParseError: If severity is not recognized

    Example:
        >>> _normalize_severity("critical")
        'Critical'
        >>> _normalize_severity("Moderate ")
        'Moderate'
        >>> _normalize_severity("aligned")
        'Consistent'
    """
    severity_lower = severity.strip().lower()

    # Map variations to standard values
    if severity_lower in ['critical', 'severe', 'major']:
        return 'Critical'
    elif severity_lower in ['moderate', 'minor', 'notable']:
        return 'Moderate'
    elif severity_lower in ['consistent', 'aligned', 'good', 'appropriate']:
        return 'Consistent'
    else:
        logger.warning(f"Unrecognized severity level: '{severity}' - defaulting to 'Moderate'")
        # Default to Moderate to avoid breaking
        return 'Moderate'


def _validate_parsed_feedback(result: Dict) -> None:
    """
    Validate that parsed feedback has required components.

    Args:
        result (Dict): Parsed feedback dictionary

    Raises:
        FeedbackParseError: If validation fails

    Note:
        This function modifies result['parse_errors'] if issues found.
    """
    errors = []

    # Check that we have at least one section assessment
    if not result['section_feedback']:
        errors.append("No section assessments found")

    # Check that overall assessment exists
    if not result['overall_assessment']:
        errors.append("Missing overall assessment")

    # Validate severity levels in section feedback
    for section in result['section_feedback']:
        if section['severity'] not in ['Critical', 'Moderate', 'Consistent']:
            errors.append(
                f"Invalid severity '{section['severity']}' for section '{section['section_name']}'"
            )

    if errors:
        logger.warning(f"Validation found {len(errors)} issues: {errors}")
        result['parse_errors'].extend(errors)
        # Don't raise exception - allow partial success


def get_feedback_summary(parsed_feedback: Dict) -> Dict:
    """
    Generate summary statistics from parsed feedback.

    Args:
        parsed_feedback (Dict): Result from parse_ai_feedback()

    Returns:
        Dict with summary statistics:
        {
            'total_discrepancies': int,
            'critical_count': int,
            'non_critical_count': int,
            'section_count': int,
            'critical_sections': int,
            'moderate_sections': int,
            'consistent_sections': int,
            'has_major_issues': bool
        }

    Example:
        >>> feedback = parse_ai_feedback(llm_text)
        >>> summary = get_feedback_summary(feedback)
        >>> print(f"Critical issues: {summary['critical_count']}")
        Critical issues: 2
    """
    summary = {
        'total_discrepancies': (
            len(parsed_feedback['critical_discrepancies']) +
            len(parsed_feedback['non_critical_discrepancies'])
        ),
        'critical_count': len(parsed_feedback['critical_discrepancies']),
        'non_critical_count': len(parsed_feedback['non_critical_discrepancies']),
        'section_count': len(parsed_feedback['section_feedback']),
        'critical_sections': 0,
        'moderate_sections': 0,
        'consistent_sections': 0,
        'has_major_issues': False
    }

    # Count section severities
    for section in parsed_feedback['section_feedback']:
        severity = section['severity']
        if severity == 'Critical':
            summary['critical_sections'] += 1
        elif severity == 'Moderate':
            summary['moderate_sections'] += 1
        elif severity == 'Consistent':
            summary['consistent_sections'] += 1

    # Determine if there are major issues
    summary['has_major_issues'] = (
        summary['critical_count'] > 0 or
        summary['critical_sections'] > 0
    )

    return summary
