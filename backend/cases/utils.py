# backend/cases/utils.py
from .models import MasterTemplateSection # Required for type hinting if used, or direct access

def generate_report_comparison_summary(
    user_report_structured_content, # List of dicts: [{'master_template_section_id': id, 'content': 'text', 'section_name': 'name', ...}]
    expert_section_contents, # QuerySet or list of CaseTemplateSectionContent objects
    case_diagnosis_text # String: The expert's diagnosis for the overall case
):
    """
    Compares a user's structured report against expert section contents and overall diagnosis.
    Identifies textual differences and checks for key concepts.

    Args:
        user_report_structured_content (list): The user's report, already enriched with section names and IDs.
        expert_section_contents (iterable): A list or QuerySet of CaseTemplateSectionContent objects
                                            for the expert version, including 'master_section_id', 
                                            'content', and 'key_concepts_text'.
        case_diagnosis_text (str): The expert's final diagnosis for the case.

    Returns:
        dict: A dictionary containing:
            'overall_diagnosis_comparison': {'status': str, 'detail': str},
            'section_comparisons': [
                {
                    'section_name': str,
                    'master_template_section_id': int,
                    'text_comparison_status': str ('Identical' or 'Content Differs'),
                    'key_concepts_status': str ('Not Applicable', 'All Addressed', 'Some Missing'),
                    'missing_key_concepts': list (of strings),
                    'user_content_preview': str,
                    'expert_content_preview': str
                }, ...
            ]
    """
    comparison_summary = {
        'overall_diagnosis_comparison': {'status': "Not Assessed", 'detail': ""},
        'section_comparisons': []
    }

    # Create a dictionary for expert sections for easier lookup
    expert_sections_map = {
        esc.master_section_id: {
            'content': esc.content,
            'key_concepts': [kc.strip() for kc in esc.key_concepts_text.split(';') if kc.strip()] if esc.key_concepts_text else []
        } for esc in expert_section_contents
    }

    user_impression_content = ""

    # Process each section from the user's report (assuming it's based on a master template)
    for user_section in user_report_structured_content:
        section_id = user_section.get('master_template_section_id')
        section_name = user_section.get('section_name', f"Section ID {section_id}")
        user_content = user_section.get('content', "")

        # Store user impression for later comparison with case_diagnosis_text
        if section_name.lower().strip() == "impression":
            user_impression_content = user_content.lower() # Case-insensitive comparison for diagnosis

        expert_section_data = expert_sections_map.get(section_id)
        
        section_comp = {
            'section_name': section_name,
            'master_template_section_id': section_id,
            'text_comparison_status': "Expert Section Missing" if not expert_section_data else "Content Differs",
            'key_concepts_status': "Not Applicable", # Default if no expert data or no key concepts
            'missing_key_concepts': [],
            'user_content_preview': (user_content[:100] + '...') if len(user_content) > 100 else user_content,
            'expert_content_preview': ""
        }

        if expert_section_data:
            expert_content = expert_section_data['content']
            expert_key_concepts = expert_section_data['key_concepts']
            section_comp['expert_content_preview'] = (expert_content[:100] + '...') if len(expert_content) > 100 else expert_content

            # Normalize whitespace for simpler text comparison (basic check)
            if user_content.strip() == expert_content.strip():
                section_comp['text_comparison_status'] = "Identical"
            
            if expert_key_concepts:
                section_comp['key_concepts_status'] = "All Addressed" # Assume all addressed initially
                user_content_lower = user_content.lower()
                for concept in expert_key_concepts:
                    if concept.lower() not in user_content_lower:
                        section_comp['key_concepts_status'] = "Some Missing"
                        section_comp['missing_key_concepts'].append(concept)
            else:
                section_comp['key_concepts_status'] = "No Key Concepts Defined by Expert for this Section"
        
        comparison_summary['section_comparisons'].append(section_comp)

    # Compare user's impression with the overall case diagnosis
    if case_diagnosis_text:
        case_diagnosis_lower = case_diagnosis_text.lower()
        if not user_impression_content:
            comparison_summary['overall_diagnosis_comparison']['status'] = "User Impression Missing"
            comparison_summary['overall_diagnosis_comparison']['detail'] = f"User did not provide an impression. Expert diagnosis is: '{case_diagnosis_text}'."
        elif case_diagnosis_lower in user_impression_content:
            comparison_summary['overall_diagnosis_comparison']['status'] = "Aligns with Expert Diagnosis"
            comparison_summary['overall_diagnosis_comparison']['detail'] = f"User's impression mentions the expert diagnosis: '{case_diagnosis_text}'."
        else:
            comparison_summary['overall_diagnosis_comparison']['status'] = "Deviates from Expert Diagnosis"
            comparison_summary['overall_diagnosis_comparison']['detail'] = f"User's impression does not clearly state the expert diagnosis ('{case_diagnosis_text}'). User Impression: '{user_impression_content[:150]}...'."
    else:
        comparison_summary['overall_diagnosis_comparison']['status'] = "Expert Diagnosis Not Provided for Case"
        comparison_summary['overall_diagnosis_comparison']['detail'] = "No overall expert diagnosis was provided for this case to compare against."
        
    return comparison_summary

# Example of how you might have your existing utils.py content
# (Keep any existing functions you have in utils.py)

# def get_available_template_sections(modality):
# """
# Get all template sections available for a given modality.
# ... (your existing function)
# """
# return TemplateSection.objects.filter(modality__in=[modality, None]).order_by('order', 'name')
