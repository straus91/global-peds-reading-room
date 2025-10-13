"""
Unit tests for feedback_parser.py

Tests parsing of LLM-generated feedback into structured format.
"""

from django.test import TestCase
from cases.feedback_parser import (
    parse_ai_feedback,
    get_feedback_summary,
    FeedbackParseError,
    _extract_overall_assessment,
    _extract_discrepancies,
    _extract_section_assessments,
    _normalize_severity,
)


class OverallAssessmentExtractionTest(TestCase):
    """Test extraction of overall assessment paragraph."""

    def test_extract_overall_assessment_standard(self):
        """Test standard format with clear separation."""
        feedback = """You correctly identified the diagnosis of pneumothorax.

1. CRITICAL DISCREPANCIES:
- You missed something"""

        result = _extract_overall_assessment(feedback)
        self.assertEqual(result, "You correctly identified the diagnosis of pneumothorax.")

    def test_extract_overall_assessment_multiline(self):
        """Test multiline overall assessment."""
        feedback = """You provided a good report overall.
Your findings were detailed and accurate.

1. CRITICAL DISCREPANCIES:"""

        result = _extract_overall_assessment(feedback)
        self.assertIn("You provided a good report overall", result)
        self.assertIn("Your findings were detailed", result)

    def test_extract_overall_assessment_missing(self):
        """Test fallback when no clear separation."""
        feedback = """1. CRITICAL DISCREPANCIES:
- You missed the pneumothorax"""

        result = _extract_overall_assessment(feedback)
        # Should return empty or first line
        self.assertIsInstance(result, str)


class DiscrepancyExtractionTest(TestCase):
    """Test extraction of discrepancy lists."""

    def test_extract_critical_discrepancies_multiple(self):
        """Test extracting multiple critical discrepancies."""
        feedback = """1. CRITICAL DISCREPANCIES:
- You missed the right-sided pneumothorax
- You incorrectly identified the cardiac silhouette as enlarged

2. NON-CRITICAL DISCREPANCIES:"""

        result = _extract_discrepancies(feedback, 1, 'CRITICAL DISCREPANCIES')

        self.assertEqual(len(result), 2)
        self.assertIn("You missed the right-sided pneumothorax", result)
        self.assertIn("You incorrectly identified the cardiac silhouette as enlarged", result)

    def test_extract_critical_discrepancies_none(self):
        """Test when no critical discrepancies."""
        feedback = """1. CRITICAL DISCREPANCIES:
None identified.

2. NON-CRITICAL DISCREPANCIES:"""

        result = _extract_discrepancies(feedback, 1, 'CRITICAL DISCREPANCIES')
        self.assertEqual(len(result), 0)

    def test_extract_non_critical_discrepancies(self):
        """Test extracting non-critical discrepancies."""
        feedback = """2. NON-CRITICAL DISCREPANCIES:
- You did not mention the patient's surgical history
- You did not comment on rib counting

SECTION SEVERITY ASSESSMENT:"""

        result = _extract_discrepancies(feedback, 2, 'NON-CRITICAL DISCREPANCIES')

        self.assertEqual(len(result), 2)
        self.assertIn("You did not mention the patient's surgical history", result)

    def test_extract_discrepancies_bullet_variations(self):
        """Test different bullet point styles."""
        feedback = """1. CRITICAL DISCREPANCIES:
- You missed finding A
• You missed finding B
* You missed finding C

2. NON-CRITICAL"""

        result = _extract_discrepancies(feedback, 1, 'CRITICAL DISCREPANCIES')
        self.assertEqual(len(result), 3)


class SectionAssessmentExtractionTest(TestCase):
    """Test extraction of section severity assessments."""

    def test_extract_section_assessments_single(self):
        """Test extracting single section assessment."""
        feedback = """SECTION SEVERITY ASSESSMENT:
Section: Findings
Severity: Critical
Reason: You missed the primary diagnosis of pneumothorax."""

        result = _extract_section_assessments(feedback)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['section_name'], 'Findings')
        self.assertEqual(result[0]['severity'], 'Critical')
        self.assertIn('pneumothorax', result[0]['reason'])

    def test_extract_section_assessments_multiple(self):
        """Test extracting multiple section assessments."""
        feedback = """SECTION SEVERITY ASSESSMENT:
Section: Findings
Severity: Critical
Reason: Major discrepancy in findings.

Section: Impression
Severity: Moderate
Reason: Minor difference in impression.

Section: Recommendations
Severity: Consistent
Reason: Your recommendations align with expert."""

        result = _extract_section_assessments(feedback)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['section_name'], 'Findings')
        self.assertEqual(result[0]['severity'], 'Critical')
        self.assertEqual(result[1]['section_name'], 'Impression')
        self.assertEqual(result[1]['severity'], 'Moderate')
        self.assertEqual(result[2]['section_name'], 'Recommendations')
        self.assertEqual(result[2]['severity'], 'Consistent')

    def test_extract_section_assessments_missing(self):
        """Test error when section assessment missing."""
        feedback = """1. CRITICAL DISCREPANCIES:
None identified."""

        with self.assertRaises(FeedbackParseError):
            _extract_section_assessments(feedback)

    def test_extract_section_assessments_multiline_reason(self):
        """Test section with multiline reason."""
        feedback = """SECTION SEVERITY ASSESSMENT:
Section: Findings
Severity: Moderate
Reason: Your findings were mostly correct. However, you did not mention
the patient's surgical clips which are visible on the image."""

        result = _extract_section_assessments(feedback)

        self.assertEqual(len(result), 1)
        self.assertIn('surgical clips', result[0]['reason'])


class SeverityNormalizationTest(TestCase):
    """Test severity level normalization."""

    def test_normalize_severity_critical_variants(self):
        """Test critical severity variations."""
        self.assertEqual(_normalize_severity('Critical'), 'Critical')
        self.assertEqual(_normalize_severity('critical'), 'Critical')
        self.assertEqual(_normalize_severity('CRITICAL'), 'Critical')
        self.assertEqual(_normalize_severity('severe'), 'Critical')
        self.assertEqual(_normalize_severity('major'), 'Critical')

    def test_normalize_severity_moderate_variants(self):
        """Test moderate severity variations."""
        self.assertEqual(_normalize_severity('Moderate'), 'Moderate')
        self.assertEqual(_normalize_severity('moderate'), 'Moderate')
        self.assertEqual(_normalize_severity('minor'), 'Moderate')
        self.assertEqual(_normalize_severity('notable'), 'Moderate')

    def test_normalize_severity_consistent_variants(self):
        """Test consistent severity variations."""
        self.assertEqual(_normalize_severity('Consistent'), 'Consistent')
        self.assertEqual(_normalize_severity('consistent'), 'Consistent')
        self.assertEqual(_normalize_severity('aligned'), 'Consistent')
        self.assertEqual(_normalize_severity('good'), 'Consistent')
        self.assertEqual(_normalize_severity('appropriate'), 'Consistent')

    def test_normalize_severity_unknown(self):
        """Test unknown severity defaults to Moderate."""
        result = _normalize_severity('unknown_level')
        self.assertEqual(result, 'Moderate')


class ParseAIFeedbackTest(TestCase):
    """Test complete feedback parsing."""

    def test_parse_perfect_feedback(self):
        """Test parsing perfect format feedback."""
        feedback = """You correctly identified the final diagnosis of a normal chest.

1. CRITICAL DISCREPANCIES:
None identified.

2. NON-CRITICAL DISCREPANCIES:
- You did not mention the patient's surgical history in the findings.

SECTION SEVERITY ASSESSMENT:
Section: Findings
Severity: Moderate
Reason: The report is good, but omitting relevant patient history is a moderate discrepancy.

Section: Impression
Severity: Consistent
Reason: Your impression of a normal chest aligns with the expert's conclusion."""

        result = parse_ai_feedback(feedback)

        # Check parse success
        self.assertTrue(result['parse_success'])
        self.assertEqual(len(result['parse_errors']), 0)

        # Check overall assessment
        self.assertIn('correctly identified', result['overall_assessment'])

        # Check discrepancies
        self.assertEqual(len(result['critical_discrepancies']), 0)
        self.assertEqual(len(result['non_critical_discrepancies']), 1)
        self.assertIn('surgical history', result['non_critical_discrepancies'][0])

        # Check section feedback
        self.assertEqual(len(result['section_feedback']), 2)
        self.assertEqual(result['section_feedback'][0]['section_name'], 'Findings')
        self.assertEqual(result['section_feedback'][0]['severity'], 'Moderate')
        self.assertEqual(result['section_feedback'][1]['section_name'], 'Impression')
        self.assertEqual(result['section_feedback'][1]['severity'], 'Consistent')

        # Check raw feedback preserved
        self.assertEqual(result['raw_feedback'], feedback)

    def test_parse_feedback_with_critical_discrepancies(self):
        """Test parsing feedback with critical issues."""
        feedback = """You missed the primary diagnosis.

1. CRITICAL DISCREPANCIES:
- You missed the right-sided pneumothorax
- You incorrectly stated the heart was enlarged

2. NON-CRITICAL DISCREPANCIES:
None identified.

SECTION SEVERITY ASSESSMENT:
Section: Findings
Severity: Critical
Reason: Major diagnostic error - pneumothorax missed."""

        result = parse_ai_feedback(feedback)

        self.assertTrue(result['parse_success'])
        self.assertEqual(len(result['critical_discrepancies']), 2)
        self.assertIn('pneumothorax', result['critical_discrepancies'][0])
        self.assertEqual(len(result['non_critical_discrepancies']), 0)
        self.assertEqual(result['section_feedback'][0]['severity'], 'Critical')

    def test_parse_feedback_multiple_sections(self):
        """Test parsing feedback with many sections."""
        feedback = """Good overall report with minor issues.

1. CRITICAL DISCREPANCIES:
None identified.

2. NON-CRITICAL DISCREPANCIES:
- You did not mention rib counting

SECTION SEVERITY ASSESSMENT:
Section: Technique
Severity: Consistent
Reason: Appropriate technique description.

Section: Findings
Severity: Moderate
Reason: Minor omission of rib counting.

Section: Impression
Severity: Consistent
Reason: Accurate impression.

Section: Recommendations
Severity: Consistent
Reason: Appropriate recommendations."""

        result = parse_ai_feedback(feedback)

        self.assertTrue(result['parse_success'])
        self.assertEqual(len(result['section_feedback']), 4)

        section_names = [s['section_name'] for s in result['section_feedback']]
        self.assertIn('Technique', section_names)
        self.assertIn('Findings', section_names)
        self.assertIn('Impression', section_names)
        self.assertIn('Recommendations', section_names)

    def test_parse_feedback_malformed(self):
        """Test parsing malformed feedback (missing sections)."""
        feedback = """Some text but missing required structure."""

        result = parse_ai_feedback(feedback)

        # Should fail gracefully
        self.assertFalse(result['parse_success'])
        self.assertGreater(len(result['parse_errors']), 0)
        self.assertEqual(result['raw_feedback'], feedback)


class FeedbackSummaryTest(TestCase):
    """Test feedback summary generation."""

    def test_summary_no_issues(self):
        """Test summary for perfect report."""
        parsed = {
            'critical_discrepancies': [],
            'non_critical_discrepancies': [],
            'section_feedback': [
                {'section_name': 'Findings', 'severity': 'Consistent', 'reason': 'Good'},
                {'section_name': 'Impression', 'severity': 'Consistent', 'reason': 'Good'}
            ]
        }

        summary = get_feedback_summary(parsed)

        self.assertEqual(summary['total_discrepancies'], 0)
        self.assertEqual(summary['critical_count'], 0)
        self.assertEqual(summary['non_critical_count'], 0)
        self.assertEqual(summary['consistent_sections'], 2)
        self.assertFalse(summary['has_major_issues'])

    def test_summary_with_critical_issues(self):
        """Test summary with critical issues."""
        parsed = {
            'critical_discrepancies': ['Missed pneumothorax', 'Missed fracture'],
            'non_critical_discrepancies': ['Minor detail'],
            'section_feedback': [
                {'section_name': 'Findings', 'severity': 'Critical', 'reason': 'Major error'},
                {'section_name': 'Impression', 'severity': 'Moderate', 'reason': 'Minor issue'}
            ]
        }

        summary = get_feedback_summary(parsed)

        self.assertEqual(summary['total_discrepancies'], 3)
        self.assertEqual(summary['critical_count'], 2)
        self.assertEqual(summary['non_critical_count'], 1)
        self.assertEqual(summary['critical_sections'], 1)
        self.assertEqual(summary['moderate_sections'], 1)
        self.assertTrue(summary['has_major_issues'])

    def test_summary_mixed_sections(self):
        """Test summary with mixed section severities."""
        parsed = {
            'critical_discrepancies': [],
            'non_critical_discrepancies': ['Minor 1', 'Minor 2'],
            'section_feedback': [
                {'section_name': 'Section1', 'severity': 'Critical', 'reason': 'Bad'},
                {'section_name': 'Section2', 'severity': 'Moderate', 'reason': 'OK'},
                {'section_name': 'Section3', 'severity': 'Moderate', 'reason': 'OK'},
                {'section_name': 'Section4', 'severity': 'Consistent', 'reason': 'Good'}
            ]
        }

        summary = get_feedback_summary(parsed)

        self.assertEqual(summary['section_count'], 4)
        self.assertEqual(summary['critical_sections'], 1)
        self.assertEqual(summary['moderate_sections'], 2)
        self.assertEqual(summary['consistent_sections'], 1)
        self.assertTrue(summary['has_major_issues'])  # Has critical section
