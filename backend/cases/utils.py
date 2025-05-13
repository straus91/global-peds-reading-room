# Create this file as cases/utils.py

from .models import Case, Language, TemplateSection, Template, TemplateSectionContent

def create_case_template(case_id, language_code, template_data):
    """
    Helper function to create or update a template for a case.
    
    Args:
        case_id (int): The ID of the case to create a template for.
        language_code (str): The language code for the template.
        template_data (dict): A dictionary mapping section names to content.
            Example: {'Findings': 'Template text...', 'Impression': 'Template text...'}
    
    Returns:
        Template: The created or updated template object.
    
    Raises:
        Case.DoesNotExist: If the case with the given ID doesn't exist.
        Language.DoesNotExist: If the language with the given code doesn't exist.
        TemplateSection.DoesNotExist: If a section in template_data doesn't exist.
    """
    # Get case and language objects
    case = Case.objects.get(pk=case_id)
    language = Language.objects.get(code=language_code)
    
    # Create or get the template
    template, created = Template.objects.get_or_create(
        case=case,
        language=language
    )
    
    # Process each section
    for section_name, content in template_data.items():
        # Get the template section
        try:
            section = TemplateSection.objects.get(name=section_name, modality__in=[case.modality, None])
        except TemplateSection.DoesNotExist:
            # If the section doesn't exist with the case's modality, try to get a common section
            section = TemplateSection.objects.get(name=section_name, modality=None)
        
        # Create or update the section content
        TemplateSectionContent.objects.update_or_create(
            template=template,
            section=section,
            defaults={'content': content}
        )
    
    return template


def get_available_template_sections(modality):
    """
    Get all template sections available for a given modality.
    
    Args:
        modality (str): The modality to get sections for.
    
    Returns:
        QuerySet: All TemplateSection objects available for the modality,
                  including common sections (modality=None).
    """
    return TemplateSection.objects.filter(modality__in=[modality, None]).order_by('order', 'name')