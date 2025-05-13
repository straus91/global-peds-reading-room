// Global Peds Reading Room - Report Templates

// In a real application, this data would come from the database
// This is just a simulation of the templates database for demonstration
const reportTemplatesDB = {
    // CT Brain Template
    "ct-brain": {
        id: 1,
        name: "CT Brain Template",
        modality: "ct",
        bodyPart: "brain",
        sections: [
            { title: "Ventricles", content: "Size and configuration of lateral, third and fourth ventricles...", required: true },
            { title: "Extra-axial Spaces", content: "Presence/absence of extra-axial collections...", required: true },
            { title: "Brain Parenchyma", content: "Density of gray and white matter, presence of infarcts, hemorrhage...", required: true },
            { title: "Vascular Structures", content: "Patency of major intracranial vessels...", required: true },
            { title: "Skull & Sinuses", content: "Integrity of calvarium, skull base, and paranasal sinuses...", required: true },
            { title: "Impression", content: "Summary of findings and differential diagnosis...", required: true }
        ]
    },
    
    // CT Chest Template
    "ct-chest": {
        id: 2,
        name: "CT Chest Template",
        modality: "ct",
        bodyPart: "chest",
        sections: [
            { title: "Lungs", content: "Parenchymal abnormalities, nodules, infiltrates...", required: true },
            { title: "Pleura", content: "Presence/absence of effusion, pneumothorax, thickening...", required: true },
            { title: "Mediastinum", content: "Lymphadenopathy, masses, vascular structures...", required: true },
            { title: "Heart", content: "Size, pericardium, calcifications...", required: true },
            { title: "Chest Wall", content: "Integrity of ribs, soft tissues...", required: true },
            { title: "Upper Abdomen", content: "Visualized upper abdominal structures...", required: false },
            { title: "Impression", content: "Summary of findings and differential diagnosis...", required: true }
        ]
    },
    
    // MRI Brain Template
    "mri-brain": {
        id: 3,
        name: "MRI Brain Template",
        modality: "mri",
        bodyPart: "brain",
        sections: [
            { title: "Ventricles", content: "Size and configuration of ventricles...", required: true },
            { title: "Extra-axial Spaces", content: "Presence/absence of collections...", required: true },
            { title: "Brain Parenchyma", content: "Signal intensity of gray and white matter...", required: true },
            { title: "White Matter", content: "Presence/absence of white matter lesions...", required: true },
            { title: "Gray Matter", content: "Cortical thickness, signal abnormalities...", required: true },
            { title: "Posterior Fossa", content: "Cerebellum, pons, medulla...", required: true },
            { title: "Vascular Structures", content: "Flow voids, aneurysms, malformations...", required: true },
            { title: "Impression", content: "Summary of findings and differential diagnosis...", required: true }
        ]
    },
    
    // X-Ray Chest Template
    "xray-chest": {
        id: 4,
        name: "X-Ray Chest Template",
        modality: "xray",
        bodyPart: "chest",
        sections: [
            { title: "Lungs", content: "Describe the lung fields, including aeration, consolidation, and nodules.", required: true },
            { title: "Heart & Mediastinum", content: "Comment on heart size, mediastinal contours, and vascular structures.", required: true },
            { title: "Pleura", content: "Describe pleural spaces, including effusions if present.", required: true },
            { title: "Bones", content: "Comment on bony structures visible on the image.", required: true },
            { title: "Impression", content: "Provide diagnosis and recommendations.", required: true }
        ]
    },
    
    // Ultrasound Abdomen Template
    "us-abdomen": {
        id: 5,
        name: "Ultrasound Abdomen Template",
        modality: "us",
        bodyPart: "abdomen",
        sections: [
            { title: "Liver", content: "Size, echogenicity, focal lesions, intrahepatic biliary ducts...", required: true },
            { title: "Gallbladder & Biliary Tree", content: "Gallbladder size, wall thickness, presence of stones, common bile duct...", required: true },
            { title: "Pancreas", content: "Size, echogenicity, focal lesions, pancreatic duct...", required: true },
            { title: "Spleen", content: "Size, echogenicity, focal lesions...", required: true },
            { title: "Kidneys", content: "Size, echogenicity, cortical thickness, hydronephrosis, calculi...", required: true },
            { title: "Impression", content: "Summary of findings and differential diagnosis...", required: true }
        ]
    }
};

// Get template by ID
function getTemplateById(templateId) {
    return reportTemplatesDB[templateId] || null;
}

// Get template by modality and body part
function getTemplateByModalityAndBodyPart(modality, bodyPart) {
    const templateKey = `${modality}-${bodyPart}`;
    return reportTemplatesDB[templateKey] || null;
}

// Generate template HTML based on template ID
function generateTemplateHTML(templateId, language = 'en') {
    const template = getTemplateById(templateId);
    
    if (!template) {
        return `<div class="error-message">Template not found: ${templateId}</div>`;
    }
    
    return generateTemplateHTMLFromData(template, language);
}

// Generate template HTML from template data
function generateTemplateHTMLFromData(template, language = 'en') {
    let html = `
        <div class="case-report-template" data-template-id="${template.id}">
            <h3 class="case-section-title">${language === 'en' ? 'Report Template' : 'Plantilla de Informe'}</h3>
            <form id="reportForm">
    `;
    
    // Add template sections
    template.sections.forEach(section => {
        html += `
            <div class="report-section">
                <label>${translateSectionTitle(section.title, language)} ${section.required ? '<span class="required">*</span>' : ''}</label>
                <textarea name="${section.title.toLowerCase().replace(/\s/g, '_')}" 
                    placeholder="${translatePlaceholder(section.content, language)}" 
                    ${section.required ? 'required' : ''}></textarea>
            </div>
        `;
    });
    
    // Add form actions
    html += `
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" id="saveReportBtn">${language === 'en' ? 'Save Draft' : 'Guardar Borrador'}</button>
                    <button type="submit" class="btn">${language === 'en' ? 'Submit Report' : 'Enviar Informe'}</button>
                </div>
            </form>
        </div>
    `;
    
    return html;
}

// Translate section titles based on language
function translateSectionTitle(title, language) {
    if (language === 'en') return title;
    
    // Spanish translations (example)
    const spanishTitles = {
        "Ventricles": "Ventrículos",
        "Extra-axial Spaces": "Espacios Extra-axiales",
        "Brain Parenchyma": "Parénquima Cerebral",
        "Vascular Structures": "Estructuras Vasculares",
        "Skull & Sinuses": "Cráneo y Senos",
        "Impression": "Impresión",
        "Lungs": "Pulmones",
        "Pleura": "Pleura",
        "Mediastinum": "Mediastino",
        "Heart": "Corazón",
        "Heart & Mediastinum": "Corazón y Mediastino",
        "Chest Wall": "Pared Torácica",
        "Upper Abdomen": "Abdomen Superior",
        "White Matter": "Sustancia Blanca",
        "Gray Matter": "Sustancia Gris",
        "Posterior Fossa": "Fosa Posterior",
        "Liver": "Hígado",
        "Gallbladder & Biliary Tree": "Vesícula Biliar y Vías Biliares",
        "Pancreas": "Páncreas",
        "Spleen": "Bazo",
        "Kidneys": "Riñones",
        "Bones": "Huesos"
    };
    
    // Return translated title or original if translation not found
    return spanishTitles[title] || title;
}

// Translate placeholder text based on language
function translatePlaceholder(content, language) {
    if (language === 'en') return content;
    
    // Simple placeholder translation (in a real app, this would be more comprehensive)
    if (language === 'es') {
        return "Escriba su informe aquí...";
    }
    
    if (language === 'pt') {
        return "Escreva seu relatório aqui...";
    }
    
    return content;
}

// Initialize report template functionality
function initReportTemplate(caseData) {
    // Get template for this case
    const templateId = `${caseData.modality}-${caseData.bodyPart || 'general'}`;
    const template = getTemplateById(templateId);
    
    if (!template) {
        console.error(`No template found for ${templateId}`);
        return;
    }
    
    // Get container
    const templateContainer = document.getElementById('templateContainer');
    if (!templateContainer) {
        console.error('Template container not found');
        return;
    }
    
    // Default language
    let currentLanguage = 'en';
    if (caseData.languages && caseData.languages.length > 0) {
        currentLanguage = caseData.languages[0];
    }
    
    // Generate and insert template HTML
    templateContainer.innerHTML = generateTemplateHTMLFromData(template, currentLanguage);
    
    // Set up form handlers
    const reportForm = document.getElementById('reportForm');
    if (reportForm) {
        // Submit handler
        reportForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Check if all required fields are filled
            const requiredFields = reportForm.querySelectorAll('[required]');
            let allFilled = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    allFilled = false;
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });
            
            if (!allFilled) {
                window.showToast('Please fill in all required fields', 'error');
                return;
            }
            
            // Collect form data
            const formData = {};
            const formElements = reportForm.elements;
            for (let i = 0; i < formElements.length; i++) {
                const element = formElements[i];
                if (element.name && element.tagName === 'TEXTAREA') {
                    formData[element.name] = element.value;
                }
            }
            
            // In a real app, this would submit the form data to the server
            console.log('Submitting report:', formData);
            window.showToast('Report submitted successfully', 'success');
            
            // Return to case list after a delay
            setTimeout(() => {
                loadCaseList(); // This function should be defined in main.js
            }, 1500);
        });
        
        // Save draft handler
        const saveReportBtn = document.getElementById('saveReportBtn');
        if (saveReportBtn) {
            saveReportBtn.addEventListener('click', function() {
                // Collect form data
                const formData = {};
                const formElements = reportForm.elements;
                for (let i = 0; i < formElements.length; i++) {
                    const element = formElements[i];
                    if (element.name && element.tagName === 'TEXTAREA') {
                        formData[element.name] = element.value;
                    }
                }
                
                // In a real app, this would save the form data to the server as a draft
                console.log('Saving draft report:', formData);
                window.showToast('Report draft saved', 'success');
            });
        }
    }
    
    // Set up language switching
    const languageOptions = document.querySelectorAll('.language-option');
    if (languageOptions.length > 0) {
        languageOptions.forEach(option => {
            option.addEventListener('click', function() {
                const lang = this.getAttribute('data-lang');
                
                // Skip if already selected
                if (lang === currentLanguage) {
                    return;
                }
                
                // Remove active class from all language options
                languageOptions.forEach(opt => opt.classList.remove('active'));
                
                // Add active class to selected language option
                this.classList.add('active');
                
                // Get current form data to preserve it
                const formData = {};
                const formElements = reportForm.elements;
                for (let i = 0; i < formElements.length; i++) {
                    const element = formElements[i];
                    if (element.name && element.tagName === 'TEXTAREA') {
                        formData[element.name] = element.value;
                    }
                }
                
                // Update current language
                currentLanguage = lang;
                
                // Regenerate template with new language
                templateContainer.innerHTML = generateTemplateHTMLFromData(template, lang);
                
                // Reattach event handlers
                const newReportForm = document.getElementById('reportForm');
                if (newReportForm) {
                    // Submit handler
                    newReportForm.addEventListener('submit', function(e) {
                        e.preventDefault();
                        
                        // Check if all required fields are filled
                        const requiredFields = newReportForm.querySelectorAll('[required]');
                        let allFilled = true;
                        
                        requiredFields.forEach(field => {
                            if (!field.value.trim()) {
                                allFilled = false;
                                field.classList.add('error');
                            } else {
                                field.classList.remove('error');
                            }
                        });
                        
                        if (!allFilled) {
                            window.showToast('Please fill in all required fields', 'error');
                            return;
                        }
                        
                        // In a real app, this would submit the form data to the server
                        window.showToast('Report submitted successfully', 'success');
                        
                        // Return to case list after a delay
                        setTimeout(() => {
                            loadCaseList(); // This function should be defined in main.js
                        }, 1500);
                    });
                    
                    // Save draft handler
                    const newSaveReportBtn = document.getElementById('saveReportBtn');
                    if (newSaveReportBtn) {
                        newSaveReportBtn.addEventListener('click', function() {
                            // In a real app, this would save the form data to the server as a draft
                            window.showToast('Report draft saved', 'success');
                        });
                    }
                    
                    // Restore form data
                    const newFormElements = newReportForm.elements;
                    for (let i = 0; i < newFormElements.length; i++) {
                        const element = newFormElements[i];
                        if (element.name && element.tagName === 'TEXTAREA' && formData[element.name]) {
                            element.value = formData[element.name];
                        }
                    }
                }
                
                // Show notification
                window.showToast(`Switched to ${formatLanguage(lang)} language`, 'info');
            });
        });
    }
}

// Format language for display
function formatLanguage(lang) {
    switch (lang) {
        case 'en': return 'English';
        case 'es': return 'Spanish';
        case 'pt': return 'Portuguese';
        case 'fr': return 'French';
        default: return lang;
    }
}

// Export functions for use in main.js
window.reportTemplates = {
    getTemplateById,
    getTemplateByModalityAndBodyPart,
    generateTemplateHTML,
    initReportTemplate
};