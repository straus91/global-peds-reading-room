// frontend/js/admin-case-edit.js
// Handles adding and editing radiology cases in the admin panel.

// --- Global module-level variables ---
let currentCaseId = null; 
let availableMasterTemplates = []; 
let availableLanguages = []; 
let activeExpertTemplate = null; // Stores data of the expert template currently being edited.
let loadedCaseDataForEdit = null; 

/**
 * Main initialization function for the Add/Edit Case page.
 */
async function initializeAddCasePage() {
    console.log("[CaseEdit] Admin auth confirmed. Initializing Add/Edit Case Page logic...");

    initCommonFormElements();
    
    await loadMasterTemplatesForDropdown();
    await loadAvailableLanguages();

    const urlParams = new URLSearchParams(window.location.search);
    currentCaseId = urlParams.get('edit_id');

    const pageTitleElement = document.querySelector('title');
    const formTitleElement = document.querySelector('.admin-content .admin-header h1');
    const submitButton = document.querySelector('#addCaseForm button[type="submit"]');
    const caseIdentifierDisplay = document.getElementById('caseIdentifierDisplay');

    if (currentCaseId) {
        console.log(`[CaseEdit] Edit mode for case ID: ${currentCaseId}`);
        if (formTitleElement) formTitleElement.textContent = `Edit Case (ID: ${currentCaseId})`;
        if (pageTitleElement) pageTitleElement.textContent = `Edit Case (ID: ${currentCaseId}) - Global Peds Reading Room`;
        if (submitButton) submitButton.textContent = 'Update Case';
        
        await loadCaseForEditing(currentCaseId); 
        await loadAndDisplayExpertTemplates(currentCaseId); 
    } else {
        console.log("[CaseEdit] Add New Case mode.");
        if (formTitleElement) formTitleElement.textContent = 'Add New Case';
        if (pageTitleElement) pageTitleElement.textContent = `Add New Case - Global Peds Reading Room`;
        if (submitButton) submitButton.textContent = 'Create Case';
        if (caseIdentifierDisplay) caseIdentifierDisplay.value = "Will be auto-generated upon saving.";
        
        const findingsContainer = document.getElementById('findingsContainer');
        if (findingsContainer && findingsContainer.children.length === 0) {
            handleAddFinding(false); 
        } else {
            updateFindingsRemoveButtonsState(); 
        }
        updateExpertTemplatesDisplay([]); 
    }

    const caseForm = document.getElementById('addCaseForm');
    if (caseForm) {
        caseForm.removeEventListener('submit', handleCaseFormSubmit); 
        caseForm.addEventListener('submit', handleCaseFormSubmit);
    } else {
        console.error("[CaseEdit] CRITICAL: Form #addCaseForm not found in HTML!");
        window.showToast("Error: Case form is missing. Page may not work correctly.", "error");
    }

    const addLangTemplateBtn = document.getElementById('addLangTemplateBtn');
    if (addLangTemplateBtn) {
        addLangTemplateBtn.removeEventListener('click', handleAddLanguageTemplateClick); 
        addLangTemplateBtn.addEventListener('click', handleAddLanguageTemplateClick);
    }

    // Save Draft Button
    const saveDraftBtn = document.getElementById('saveDraftBtn');
    if (saveDraftBtn) {
        saveDraftBtn.addEventListener('click', () => {
            const form = document.getElementById('addCaseForm');
            handleCaseFormSubmit({ preventDefault: () => {}, target: form }, true); // true for saveAsDraft
        });
    }

    console.log("[CaseEdit] Page initialization complete.");
}

window.initializeCurrentAdminPage = initializeAddCasePage;

function initCommonFormElements() {
    console.log("[CaseEdit] Initializing common form element listeners...");

    document.getElementById('addFindingBtn')?.addEventListener('click', () => handleAddFinding(true)); // Focus new input
    document.getElementById('reportTemplate')?.addEventListener('change', function() {
        loadAndDisplayTemplateSummary(this.value);
    });

    document.getElementById('createNewMasterTemplateBtn')?.addEventListener('click', () => {
        const modality = document.getElementById('caseModality')?.value || '';
        const subspecialty = document.getElementById('caseSubspecialty')?.value || '';
        const params = new URLSearchParams({ action: 'create' });
        if (modality) params.append('modality', modality);
        if (subspecialty) {
            const bodyPart = getBodyPartFromSubspecialty(subspecialty); 
            if (bodyPart) params.append('bodyPart', bodyPart);
        }
        window.location.href = `manage-templates.html?${params.toString()}`;
    });

    document.getElementById('previewMasterTemplateBtn')?.addEventListener('click', async () => {
        const selectedTemplateId = document.getElementById('reportTemplate')?.value;
        if (selectedTemplateId) {
            await previewSelectedMasterTemplate(selectedTemplateId);
        } else {
            window.showToast('Please select a master template to preview.', 'warning');
        }
    });
    updateFindingsRemoveButtonsState(); 
}

function getBodyPartFromSubspecialty(subspecialtyCode) {
    const mapping = { 'NR': 'NR', 'CH': 'CH', 'MK': 'MK', 'PD': 'PD' };
    return mapping[subspecialtyCode] || subspecialtyCode; 
}

async function loadMasterTemplatesForDropdown() {
    const reportTemplateSelect = document.getElementById('reportTemplate');
    if (!reportTemplateSelect) {
        console.error("[CaseEdit] Master template select dropdown (#reportTemplate) not found.");
        return;
    }
    reportTemplateSelect.innerHTML = '<option value="">Loading templates...</option>';
    clearTemplateSummaryDisplay(); 

    try {
        if (window.showLoading) window.showLoading(true, 'Loading master templates...');
        const response = await apiRequest('/cases/admin/templates/?is_active=true&page_size=1000');
        availableMasterTemplates = response.results || []; 

        reportTemplateSelect.innerHTML = '<option value="">Select Master Template</option>';
        if (availableMasterTemplates.length === 0) {
            reportTemplateSelect.innerHTML += '<option value="" disabled>No active master templates found</option>';
        } else {
            availableMasterTemplates.forEach(template => {
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = `${template.name} (${template.modality_display || template.modality} - ${template.body_part_display || template.body_part})`;
                reportTemplateSelect.appendChild(option);
            });
        }

        if (loadedCaseDataForEdit && loadedCaseDataForEdit.master_template) {
            reportTemplateSelect.value = loadedCaseDataForEdit.master_template;
            if (reportTemplateSelect.value === String(loadedCaseDataForEdit.master_template)) {
                loadAndDisplayTemplateSummary(loadedCaseDataForEdit.master_template);
            } else {
                console.warn(`[CaseEdit] Previously associated master template (ID: ${loadedCaseDataForEdit.master_template}) is not in the active list.`);
            }
        }
    } catch (error) {
        console.error("[CaseEdit] Error fetching master templates for dropdown:", error);
        reportTemplateSelect.innerHTML = '<option value="">Error loading templates</option>';
        if (window.showToast) window.showToast(`Failed to load report templates: ${error.message || 'Unknown error'}`, 'error');
    } finally {
        if (window.showLoading) window.showLoading(false);
    }
}

async function loadAvailableLanguages() {
    try {
        const response = await apiRequest('/cases/admin/languages/?is_active=true&page_size=100'); // Fetch more languages
        availableLanguages = (Array.isArray(response.results) ? response.results : (Array.isArray(response) ? response : []));
        console.log("[CaseEdit] Available active languages loaded:", availableLanguages);
    } catch (error) {
        console.error("[CaseEdit] Error fetching available languages:", error);
        if (window.showToast) window.showToast("Could not load available languages for expert templates.", "error");
        availableLanguages = []; 
    }
}

async function loadCaseForEditing(caseId) {
    console.log(`[CaseEdit] Loading case data for ID: ${caseId}`);
    if (window.showLoading) window.showLoading(true, `Loading case ${caseId}...`);
    try {
        const caseData = await apiRequest(`/cases/admin/cases/${caseId}/`); 
        loadedCaseDataForEdit = caseData; 
        populateFormWithCaseData(caseData);
    } catch (error) {
        console.error(`[CaseEdit] Error loading case ${caseId} for editing:`, error);
        loadedCaseDataForEdit = null;
        if (window.showToast) window.showToast(`Error loading case data: ${error.message || 'Unknown error'}`, 'error');
        const formContainer = document.querySelector('.admin-content .admin-form');
        if (formContainer) { 
            formContainer.innerHTML = `<p style="color:red; text-align:center;">Could not load case data. Please check the case ID or try again.</p><p style="text-align:center;"><a href="manage-cases.html" class="btn">Back to Manage Cases</a></p>`;
        }
    } finally {
        if (window.showLoading) window.showLoading(false);
    }
}

function populateFormWithCaseData(caseData) {
    console.log("[CaseEdit] Populating form with fetched case data:", caseData);
    const form = document.getElementById('addCaseForm');
    if (!form) {
        console.error("[CaseEdit] Form #addCaseForm not found during populateFormWithCaseData.");
        return;
    }

    form.elements['title'].value = caseData.title || '';
    
    // Display case_identifier
    const caseIdentifierDisplay = document.getElementById('caseIdentifierDisplay');
    if (caseIdentifierDisplay) {
        caseIdentifierDisplay.value = caseData.case_identifier || "Will be auto-generated upon saving.";
    }

    form.elements['subspecialty'].value = caseData.subspecialty || ''; 
    form.elements['modality'].value = caseData.modality || '';     
    form.elements['difficulty'].value = caseData.difficulty || '';

    const patientAgeValueInput = form.elements['patientAgeValue'];
    const patientAgeUnitSelect = form.elements['patientAgeUnit'];
    if (caseData.patient_age && patientAgeValueInput && patientAgeUnitSelect) {
        const ageString = String(caseData.patient_age).toLowerCase();
        const parts = ageString.match(/^(\d+)\s*(years|months|days|neonate)$/i); 
        if (parts) {
            patientAgeValueInput.value = parts[1]; 
            const unit = parts[2].toLowerCase();   
            if (Array.from(patientAgeUnitSelect.options).some(opt => opt.value === unit)) {
                patientAgeUnitSelect.value = unit;
            } else {
                console.warn(`[CaseEdit] Age unit "${unit}" from DB not in select. Defaulting.`);
                patientAgeUnitSelect.value = 'years'; 
            }
        } else if (ageString === "neonate") { 
            patientAgeValueInput.value = ''; 
            patientAgeUnitSelect.value = 'neonate';
        } else {
            console.warn(`[CaseEdit] Could not parse patient_age string: '${caseData.patient_age}'. Clearing fields.`);
            patientAgeValueInput.value = '';
            patientAgeUnitSelect.value = 'years';
        }
    } else if (patientAgeValueInput && patientAgeUnitSelect) { 
        patientAgeValueInput.value = '';
        patientAgeUnitSelect.value = 'years';
    }

    // Populate patient_sex
    if (form.elements['patient_sex']) {
        form.elements['patient_sex'].value = caseData.patient_sex || "";
    }

    form.elements['clinical_history'].value = caseData.clinical_history || '';
    form.elements['image_description_placeholder'].value = caseData.image_description_placeholder || '';
    form.elements['image_url_placeholder'].value = caseData.image_url_placeholder || '';

    if (form.elements['orthanc_study_uid']) { 
        form.elements['orthanc_study_uid'].value = caseData.orthanc_study_uid || '';
    }
    
    const findingsContainer = document.getElementById('findingsContainer');
    findingsContainer.innerHTML = ''; 
    if (caseData.key_findings) {
        const findingsArray = String(caseData.key_findings).split('\n').filter(f => f.trim() !== '');
        if (findingsArray.length > 0) {
            findingsArray.forEach(findingText => {
                const newInputGroup = handleAddFinding(false); 
                if (newInputGroup) {
                    const newFindingInput = newInputGroup.querySelector('.finding-input');
                    if (newFindingInput) newFindingInput.value = findingText;
                }
            });
        } else {
            handleAddFinding(false); 
        }
    } else {
        handleAddFinding(false); 
    }
    updateFindingsRemoveButtonsState(); 

    form.elements['diagnosis'].value = caseData.diagnosis || '';
    form.elements['discussion'].value = caseData.discussion || '';
    form.elements['references'].value = caseData.references || '';

    const reportTemplateSelect = form.elements['master_template']; 
    if (caseData.master_template) { 
        reportTemplateSelect.value = caseData.master_template;
        if (reportTemplateSelect.value === String(caseData.master_template)) {
             loadAndDisplayTemplateSummary(caseData.master_template);
        } else {
            console.warn(`[CaseEditPopulate] Master template ID ${caseData.master_template} (from case data) not found or not active in dropdown.`);
            clearTemplateSummaryDisplay();
        }
    } else {
        reportTemplateSelect.value = ""; 
        clearTemplateSummaryDisplay();
    }

    form.elements['status'].value = caseData.status || 'draft';
    form.elements['published_at'].value = caseData.published_at ? caseData.published_at.substring(0, 10) : ''; 

    console.log("[CaseEdit] Form population complete.");
}


async function loadAndDisplayExpertTemplates(caseId) {
    const container = document.getElementById('languageTemplatesContainer');
    if (!container) {
        console.error("[ExpertTpl] Container 'languageTemplatesContainer' not found.");
        return;
    }
    container.innerHTML = '<p>Loading expert templates...</p>';

    try {
        if (window.showLoading) window.showLoading(true, 'Loading expert templates for case...');
        const response = await apiRequest(`/cases/admin/cases/${caseId}/expert-templates/`);
        const expertTemplates = response.results || response || [];
        console.log("[ExpertTpl] Fetched expert templates:", expertTemplates);
        updateExpertTemplatesDisplay(expertTemplates, caseId);
    } catch (error) {
        console.error(`[ExpertTpl] Error loading expert templates for case ${caseId}:`, error);
        container.innerHTML = `<p style="color:red;">Could not load expert templates: ${error.message || 'Unknown error'}</p>`;
        if (window.showToast) window.showToast(`Error loading expert templates: ${error.message || 'Unknown error'}`, 'error');
    } finally {
        if (window.showLoading) window.showLoading(false);
    }
}

function updateExpertTemplatesDisplay(expertTemplates, caseId) {
    const container = document.getElementById('languageTemplatesContainer');
    const noTemplatesMsgEl = document.getElementById('noTemplatesMsg'); 

    if (!container) return;
    container.innerHTML = ''; 

    if (!expertTemplates || expertTemplates.length === 0) {
        if (noTemplatesMsgEl) {
            container.appendChild(noTemplatesMsgEl); 
            noTemplatesMsgEl.style.display = 'block'; 
        } else { 
            const p = document.createElement('p');
            p.id = 'noTemplatesMsg'; 
            p.style.cssText = 'font-style: italic; color: #777;';
            p.textContent = 'No expert language templates added yet. Select a Master Template and click "+ Add Language Version".';
            container.appendChild(p);
        }
        const activeEditor = document.querySelector('.expert-template-sections-active-editor'); 
        if (activeEditor) activeEditor.innerHTML = '';
        activeExpertTemplate = null;
        return;
    }

    if (noTemplatesMsgEl) noTemplatesMsgEl.style.display = 'none'; 

    expertTemplates.forEach(et => {
        const div = document.createElement('div');
        div.className = 'language-template-block';
        div.dataset.expertTemplateId = et.id; 
        div.dataset.languageCode = et.language_code; 

        const sectionsDisplayContainerId = `expert-sections-for-${et.id}`;

        div.innerHTML = `
            <div class="controls">
                <h4 style="margin:0; flex-grow:1;">${et.language_name || et.language_code} Version</h4>
                <button type="button" class="btn btn-sm btn-secondary view-edit-expert-content-btn">Edit Content</button>
                <button type="button" class="btn btn-sm btn-danger remove-expert-template-btn">Delete</button>
            </div>
            <div id="${sectionsDisplayContainerId}" class="template-fields-container expert-template-sections-for-id-${et.id}" style="display:none; margin-top: 10px; padding-top: 10px; border-top: 1px dashed #ddd;">
                <p class="template-placeholder">Click "Edit Content" to load sections.</p>
            </div>
        `;
        container.appendChild(div);

        div.querySelector('.view-edit-expert-content-btn').addEventListener('click', () => handleEditExpertTemplateContent(et, sectionsDisplayContainerId));
        div.querySelector('.remove-expert-template-btn').addEventListener('click', () => handleDeleteExpertTemplate(et.id, caseId));
    });
}

async function handleAddLanguageTemplateClick() {
    const masterTemplateId = document.getElementById('reportTemplate').value;
    if (!masterTemplateId) {
        if (window.showToast) window.showToast("Please select a Master Report Template for this case first.", "warning");
        return;
    }

    if (!currentCaseId) {
        if (window.showToast) window.showToast("Saving case as draft before adding language versions...", "info");
        const form = document.getElementById('addCaseForm');
        try {
            await handleCaseFormSubmit({ preventDefault: () => {}, target: form }, true); 

            if (!currentCaseId) {
                if (window.showToast) window.showToast("Failed to save the case as a draft. Please save manually and try again.", "error");
                return;
            }
        } catch (error) {
            if (window.showToast) window.showToast("Error saving case as draft. Please try manually.", "error");
            console.error("Error during auto-draft save:", error);
            return;
        }
    }

    await loadAvailableLanguages();
    
    if (availableLanguages.length === 0) {
        if (window.showToast) window.showToast("No active languages are defined in the system. Please add/activate languages in the Django admin.", "warning");
        return;
    }

    const existingLangCodesOnPage = Array.from(document.querySelectorAll('#languageTemplatesContainer .language-template-block'))
                                   .map(el => el.dataset.languageCode);

    const availableLangsForModal = availableLanguages.filter(lang => {
        return lang.code && !existingLangCodesOnPage.includes(lang.code);
    });

    if (availableLangsForModal.length === 0) {
        if (window.showToast) window.showToast("All available languages have already been added for this case.", "info");
        return;
    }

    const modal = document.getElementById('addLanguageModal');
    const selectEl = document.getElementById('selectNewExpertLang');

    if (!modal || !selectEl) {
        console.error("[CaseEdit] Add language modal or its select element not found.");
        if (window.showToast) window.showToast("Error: Could not open language selection dialog.", "error");
        return;
    }

    selectEl.innerHTML = '<option value="">-- Select Language --</option>'; 
    console.log("Data for language dropdown:", JSON.stringify(availableLangsForModal, null, 2));

    availableLangsForModal.forEach(lang => {
        const option = document.createElement('option');
        option.value = lang.id; 
        option.textContent = `${lang.name} (${lang.code})`;
        selectEl.appendChild(option);
    });

    const confirmBtn = document.getElementById('confirmAddLangBtn');
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

    newConfirmBtn.onclick = async () => { 
        const selectedLangId = selectEl.value;
        if (selectedLangId) {
            await createNewExpertTemplate(currentCaseId, selectedLangId); 
            if (window.closeModal) window.closeModal('addLanguageModal'); 
        } else {
            if (window.showToast) window.showToast("Please select a language.", "warning");
        }
    };
    if (window.openModal) window.openModal('addLanguageModal'); 
}

async function createNewExpertTemplate(caseId, languageId) {
    console.log(`[ExpertTpl] Creating new expert template for case ${caseId}, language ID ${languageId}`);
    if (window.showLoading) window.showLoading(true, 'Adding language version...');
    try {
        const newExpertTemplate = await apiRequest(
            `/cases/admin/cases/${caseId}/expert-templates/`,
            {
                method: 'POST',
                body: JSON.stringify({ language: parseInt(languageId) })
            }
        );
        if (window.showToast) window.showToast(`Expert template for ${newExpertTemplate.language_name || 'the selected language'} added successfully.`, 'success');
        await loadAndDisplayExpertTemplates(caseId); 

        const newTemplateBlock = document.querySelector(`.language-template-block[data-expert-template-id="${newExpertTemplate.id}"]`);
        if (newTemplateBlock) {
            const sectionsDisplayContainerId = `expert-sections-for-${newExpertTemplate.id}`;
            handleEditExpertTemplateContent(newExpertTemplate, sectionsDisplayContainerId); 
        }
    } catch (error) {
        console.error('[ExpertTpl] Error creating new expert template:', error);
        const errorDetail = error.data?.detail || (error.data && typeof error.data === 'object' ? JSON.stringify(error.data) : error.message) || 'Unknown error';
        if (window.showToast) window.showToast(`Failed to add language version: ${errorDetail}`, 'error');
    } finally {
        if (window.showLoading) window.showLoading(false);
    }
}

async function handleDeleteExpertTemplate(expertTemplateId, caseId) {
    if (!confirm(`Are you sure you want to delete this expert template version (ID: ${expertTemplateId})? All its content will be lost.`)) {
        return;
    }
    console.log(`[ExpertTpl] Deleting expert template ID: ${expertTemplateId} for case ID: ${caseId}`);
    if (window.showLoading) window.showLoading(true, 'Deleting expert template version...');
    try {
        await apiRequest(`/cases/admin/cases/${caseId}/expert-templates/${expertTemplateId}/`, {
            method: 'DELETE'
        });
        if (window.showToast) window.showToast('Expert template version deleted successfully.', 'success');
        await loadAndDisplayExpertTemplates(caseId); 

        if (activeExpertTemplate && activeExpertTemplate.id === expertTemplateId) {
            const activeEditorContainer = document.getElementById(`expert-sections-for-${expertTemplateId}`);
            if (activeEditorContainer) {
                 activeEditorContainer.innerHTML = '<p class="template-placeholder">Editor closed as template was deleted.</p>';
                 activeEditorContainer.style.display = 'none';
            }
            activeExpertTemplate = null;
        }
    } catch (error) {
        console.error('[ExpertTpl] Error deleting expert template:', error);
        if (window.showToast) window.showToast(`Failed to delete expert template version: ${error.message || 'Unknown error'}`, 'error');
    } finally {
        if (window.showLoading) window.showLoading(false);
    }
}

function handleEditExpertTemplateContent(expertTemplateData, containerId) {
    console.log('[ExpertTpl] Toggling edit content for:', expertTemplateData, "Target container ID:", containerId);
    const targetFieldsContainer = document.getElementById(containerId);
    if (!targetFieldsContainer) {
        console.error(`[ExpertTpl] Target container for sections (#${containerId}) not found.`);
        return;
    }

    document.querySelectorAll('#languageTemplatesContainer .template-fields-container').forEach(fc => {
        if (fc.id !== containerId && fc.style.display === 'block') { 
            fc.style.display = 'none';
            fc.innerHTML = '<p class="template-placeholder">Click "Edit Content" to load sections.</p>';
        }
    });
    
    if (targetFieldsContainer.style.display === 'block' && activeExpertTemplate && activeExpertTemplate.id === expertTemplateData.id) {
        targetFieldsContainer.style.display = 'none';
        targetFieldsContainer.innerHTML = '<p class="template-placeholder">Click "Edit Content" to load sections.</p>';
        activeExpertTemplate = null;
    } else {
        targetFieldsContainer.style.display = 'block';
        targetFieldsContainer.innerHTML = '<p>Loading sections content...</p>'; 
        activeExpertTemplate = expertTemplateData; 
        renderExpertTemplateSectionsForEditing(expertTemplateData, targetFieldsContainer);
    }
}

async function renderExpertTemplateSectionsForEditing(expertTemplate, containerElement) {
    let sectionsToRender = expertTemplate.section_contents;

    if ((!sectionsToRender || sectionsToRender.length === 0) && expertTemplate.id) {
        try {
            if (window.showLoading) window.showLoading(true, `Loading sections for ${expertTemplate.language_name || expertTemplate.language_code}...`);
            const detailedTemplate = await apiRequest(`/cases/admin/case-templates/${expertTemplate.id}/`);
            sectionsToRender = detailedTemplate.section_contents; 
            if (activeExpertTemplate && activeExpertTemplate.id === expertTemplate.id) {
                activeExpertTemplate = detailedTemplate; 
            }
        } catch (err) {
            console.error("Failed to fetch detailed sections for expert template:", err);
            containerElement.innerHTML = `<p style="color:red;">Could not load sections: ${err.message || 'Unknown error'}</p>`;
            if (window.showLoading) window.showLoading(false);
            return;
        } finally {
            if (window.showLoading) window.showLoading(false);
        }
    }
    
    if (!sectionsToRender || sectionsToRender.length === 0) {
        containerElement.innerHTML = '<p>This expert template has no sections. This might be because the associated Master Template has no sections defined, or they failed to load.</p>';
        return;
    }

    let sectionsHTML = '';
    sectionsToRender.forEach(secContent => {
        // NEW: Add input for key_concepts_text
        sectionsHTML += `
            <div class="form-group template-section-item" data-casetemplatesectioncontent-id="${secContent.id}">
                <label for="expert_sec_content_${secContent.id}">
                    ${secContent.master_section_name || 'Unnamed Section'} 
                    ${secContent.master_section_is_required ? '<span class="required" style="color:red;">*</span>' : ''}
                </label>
                <textarea id="expert_sec_content_${secContent.id}" class="form-control expert-section-content-input" 
                          rows="4" placeholder="${secContent.master_section_placeholder || ''}">${secContent.content || ''}</textarea>
                
                <div style="margin-top: 8px;">
                    <label for="expert_sec_key_concepts_${secContent.id}" style="font-size: 0.9em; color: #555;">
                        Case-Specific Key Concepts for this Section (Optional):
                    </label>
                    <textarea id="expert_sec_key_concepts_${secContent.id}" class="form-control expert-section-key-concepts-input" 
                              rows="2" placeholder="Semicolon-separated phrases, e.g., large mass; renal claw sign present">${secContent.key_concepts_text || ''}</textarea>
                    <p class="field-hint" style="font-size:0.8em;">These help guide AI feedback for this specific case and section.</p>
                </div>
            </div>
        `;
    });
    
    sectionsHTML += `
        <div style="text-align: right; margin-top: 15px;">
            <button type="button" class="btn btn-primary save-this-expert-content-btn" data-casetemplate-id="${expertTemplate.id}">
                Save ${expertTemplate.language_name || expertTemplate.language_code} Content
            </button>
        </div>
    `;
    containerElement.innerHTML = sectionsHTML;

    const saveBtn = containerElement.querySelector('.save-this-expert-content-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', (e) => {
            const caseTemplateId = e.target.dataset.casetemplateId;
            handleSaveExpertTemplateContent(caseTemplateId, containerElement); 
        });
    }
}

async function handleSaveExpertTemplateContent(caseTemplateId, fieldsContainer) {
    if (!caseTemplateId) {
        if (window.showToast) window.showToast("Cannot save: No active expert template specified.", "error");
        return;
    }
    if (!fieldsContainer) { 
        if (window.showToast) window.showToast("Cannot save: Content editor container not found.", "error");
        return;
    }

    const sectionItems = fieldsContainer.querySelectorAll('.template-section-item'); // Get each section item
    const payload = []; 

    sectionItems.forEach(item => {
        const caseTemplateSectionContentId = item.dataset.casetemplatesectioncontentId;
        const contentInput = item.querySelector('.expert-section-content-input');
        const keyConceptsInput = item.querySelector('.expert-section-key-concepts-input'); // NEW

        if (contentInput && keyConceptsInput) { // Check if keyConceptsInput exists
            payload.push({
                id: parseInt(caseTemplateSectionContentId),
                content: contentInput.value, 
                key_concepts_text: keyConceptsInput.value.trim() // NEW: Get value from key concepts input
            });
        } else if (contentInput) { // Fallback if keyConceptsInput somehow isn't there (shouldn't happen)
             payload.push({
                id: parseInt(caseTemplateSectionContentId),
                content: contentInput.value,
                key_concepts_text: "" // Default to empty if input not found
            });
        }
    });

    const langName = activeExpertTemplate?.language_name || activeExpertTemplate?.language_code || 'template';
    console.log(`[ExpertTpl] Saving content for CaseTemplate ID ${caseTemplateId} (${langName}). Payload:`, payload);
    if (window.showLoading) window.showLoading(true, `Saving content for ${langName}...`);

    try {
        // Backend API needs to accept 'key_concepts_text' in the payload for each section.
        // The BulkCaseTemplateSectionContentUpdateSerializer and its child CaseTemplateSectionContentUpdateSerializer
        // will need to be updated to handle this new field.
        const updatedCaseTemplateWithSections = await apiRequest(
            `/cases/admin/case-templates/${caseTemplateId}/update-sections/`, 
            {
                method: 'PUT',
                body: JSON.stringify(payload)
            }
        );
        if (window.showToast) window.showToast(`${langName} content saved successfully!`, 'success');
        
        if (activeExpertTemplate && activeExpertTemplate.id.toString() === caseTemplateId.toString()) {
            activeExpertTemplate.section_contents = updatedCaseTemplateWithSections.section_contents;
            // Also update key_concepts_text on the activeExpertTemplate if the API returns it per section
            // This depends on the serializer for CaseTemplateSectionContent including key_concepts_text
        }
    } catch (error) {
        console.error('[ExpertTpl] Error saving expert template content:', error);
        const errorDetail = error.data?.detail || (error.data && typeof error.data === 'object' ? JSON.stringify(error.data) : error.message) || 'Unknown error';
        if (window.showToast) window.showToast(`Failed to save content: ${errorDetail}`, 'error');
    } finally {
        if (window.showLoading) window.showLoading(false);
    }
}

async function handleCaseFormSubmit(event, saveAsDraft = false) {
    event.preventDefault();
    console.log(`[CaseEdit] Main case form submitted. Edit Mode: ${!!currentCaseId}, Save as Draft: ${saveAsDraft}`);
    const form = event.target || document.getElementById('addCaseForm');

    const patientAgeValue = form.elements['patientAgeValue'].value;
    const patientAgeUnit = form.elements['patientAgeUnit'].value;
    let combinedPatientAge = "";
    if (patientAgeUnit === "neonate" && !patientAgeValue) {
        combinedPatientAge = "Neonate";
    } else if (patientAgeValue && patientAgeUnit) {
        combinedPatientAge = `${patientAgeValue} ${patientAgeUnit}`;
    }

    const findingsInputs = form.querySelectorAll('input[name="key_findings_list_item"]');
    const findingsArray = Array.from(findingsInputs).map(input => input.value.trim()).filter(value => value !== "");
    const combinedKeyFindings = findingsArray.join('\n');

    const formData = new FormData(form);
    const caseDataPayload = {};
    for (let [key, value] of formData.entries()) {
        if (['key_findings_list_item', 'patientAgeValue', 'patientAgeUnit', 'case_identifier_display'].includes(key)) { // Exclude display field
            continue;
        }
        if (key === 'master_template') {
            caseDataPayload[key] = value ? parseInt(value, 10) : null;
        } else if (key === 'published_at') {
            caseDataPayload[key] = value || null;
        } else if (key === 'patient_sex') { // Ensure patient_sex is included
             caseDataPayload[key] = value || null; // Send null if empty, backend handles blank=True
        }
         else {
            caseDataPayload[key] = typeof value === 'string' ? value.trim() : value;
        }
    }
    caseDataPayload['patient_age'] = combinedPatientAge || null;
    caseDataPayload['key_findings'] = combinedKeyFindings;

    if (saveAsDraft) {
        caseDataPayload['status'] = 'draft';
    } else if (!caseDataPayload['status']) {
        caseDataPayload['status'] = 'draft';
    }

    console.log("[CaseEdit] Case data payload for API:", caseDataPayload);

    const method = currentCaseId ? 'PUT' : 'POST';
    const endpoint = currentCaseId ? `/cases/admin/cases/${currentCaseId}/` : '/cases/admin/cases/';
    const actionText = currentCaseId ? 'Updating' : 'Creating';

    if (window.showLoading) window.showLoading(true, `${actionText} case...`);
    try {
        const response = await apiRequest(endpoint, {
            method: method,
            body: JSON.stringify(caseDataPayload),
        });
        console.log(`[CaseEdit] Case ${actionText.toLowerCase()} successful:`, response);
        if (window.showToast) window.showToast(`Case ${actionText.toLowerCase().replace(/ing$/, 'ed')} successfully!`, 'success');
        
        loadedCaseDataForEdit = response; // Update with response which should include generated case_identifier

        // Update the caseIdentifierDisplay field
        const caseIdentifierDisplayEl = document.getElementById('caseIdentifierDisplay');
        if (caseIdentifierDisplayEl && response.case_identifier) {
            caseIdentifierDisplayEl.value = response.case_identifier;
        }


        if (!currentCaseId && response.id) {
            currentCaseId = response.id; 
            
            const newUrl = `add-case.html?edit_id=${response.id}`;
            window.history.replaceState({}, document.title, newUrl);
            
            const formTitleElement = document.querySelector('.admin-content .admin-header h1');
            const submitButton = document.querySelector('#addCaseForm button[type="submit"]');
            if (formTitleElement) formTitleElement.textContent = `Edit Case (ID: ${response.id})`;
            if (submitButton) submitButton.textContent = 'Update Case';
            
            await loadAndDisplayExpertTemplates(currentCaseId);
        } else if (currentCaseId) {
            // Re-populate form to ensure all fields (like case_identifier_display) are fresh
            populateFormWithCaseData(response); 
            await loadAndDisplayExpertTemplates(currentCaseId);
        }
    } catch (error) {
        console.error(`[CaseEdit] Error ${actionText.toLowerCase()} case:`, error);
        let errorMsg = `Failed to ${actionText.toLowerCase()} case.`;
        if (error.data && typeof error.data === 'object') {
            errorMsg = Object.entries(error.data)
                .map(([key, value]) => `${key.replace(/_/g, ' ')}: ${Array.isArray(value) ? value.join(', ') : value}`)
                .join('; ');
        } else if (error.message) {
            errorMsg = error.message;
        }
        if (window.showToast) window.showToast(`Error: ${errorMsg}`, 'error', 5000);
    } finally {
        if (window.showLoading) window.showLoading(false);
    }
}

function handleAddFinding(focusNewInput = true) {
    const findingsContainer = document.getElementById('findingsContainer');
    if (!findingsContainer) {
        console.error("[CaseEdit] Findings container #findingsContainer not found.");
        return null;
    }

    const existingFindingInputs = findingsContainer.querySelectorAll('.finding-input');
    const newIndex = existingFindingInputs.length + 1;

    const newInputGroup = document.createElement('div');
    newInputGroup.className = 'finding-input-group';
    newInputGroup.innerHTML = `
        <input type="text" name="key_findings_list_item" class="finding-input" placeholder="Enter key finding #${newIndex}" required>
        <button type="button" class="remove-finding-btn">Remove</button>
    `;

    const newFindingInput = newInputGroup.querySelector('.finding-input');
    const removeBtn = newInputGroup.querySelector('.remove-finding-btn');

    removeBtn.addEventListener('click', function() {
        this.parentElement.remove(); 
        updateFindingsRemoveButtonsState();
        reNumberFindingPlaceholders(); 
    });

    findingsContainer.appendChild(newInputGroup);
    updateFindingsRemoveButtonsState(); 

    if (focusNewInput && newFindingInput) {
        newFindingInput.focus();
    }
    return newInputGroup; 
}

function reNumberFindingPlaceholders() {
    const findingsContainer = document.getElementById('findingsContainer');
    if (!findingsContainer) return;
    const allFindingInputs = findingsContainer.querySelectorAll('.finding-input');
    allFindingInputs.forEach((input, index) => {
        input.placeholder = `Enter key finding #${index + 1}`;
    });
}


function updateFindingsRemoveButtonsState() {
    const findingsContainer = document.getElementById('findingsContainer');
    if (!findingsContainer) return;
    const allFindingGroups = findingsContainer.querySelectorAll('.finding-input-group');
    
    allFindingGroups.forEach((group, index) => {
        const removeBtn = group.querySelector('.remove-finding-btn');
        if (removeBtn) {
            removeBtn.disabled = (allFindingGroups.length <= 1);
        }
    });
}

async function loadAndDisplayTemplateSummary(templateId) {
    const templateSummaryDiv = document.getElementById('templateSummary');
    if (!templateSummaryDiv) return;
    if (!templateId) {
        clearTemplateSummaryDisplay();
        return;
    }
    templateSummaryDiv.innerHTML = '<p class="empty-template-message" style="font-style:italic;">Loading template details...</p>';
    try {
        const selectedTemplate = await apiRequest(`/cases/admin/templates/${templateId}/`);
        if (!selectedTemplate || typeof selectedTemplate.id === 'undefined') {
            throw new Error("Selected master template data not found or invalid from API.");
        }
        let sectionsHTML = '<p class="empty-template-message" style="font-style:italic; color:#777;">This template has no sections defined.</p>';
        if (selectedTemplate.sections && selectedTemplate.sections.length > 0) {
            const sortedSections = [...selectedTemplate.sections].sort((a, b) => (a.order || 0) - (b.order || 0));
            sectionsHTML = '<ul class="section-list">';
            sortedSections.forEach(section => {
                sectionsHTML += `
                    <li class="section-list-item">
                        <span>${section.name || 'Unnamed Section'}</span>
                        ${section.is_required ? '<span class="required-badge">Required</span>' : ''}
                    </li>`;
            });
            sectionsHTML += '</ul>';
        }
        templateSummaryDiv.innerHTML = `
            <div class="template-info">
                <h4>${selectedTemplate.name || 'Unnamed Template'}</h4>
                <p style="margin-bottom:10px;"><small>
                    <strong>Modality:</strong> ${selectedTemplate.modality_display || selectedTemplate.modality || 'N/A'} |
                    <strong>Body Part:</strong> ${selectedTemplate.body_part_display || selectedTemplate.body_part || 'N/A'}
                </small></p>
            </div>
            <div class="template-sections-summary">
                <h5 style="margin-bottom:5px; border-bottom: 1px solid #eee; padding-bottom:3px;">Master Template Sections:</h5>
                ${sectionsHTML}
            </div>
        `;
    } catch (error) {
        console.error(`[CaseEdit] Failed to load full template info for ID ${templateId}:`, error);
        templateSummaryDiv.innerHTML = '<p class="empty-template-message" style="color:red;">Could not load template details.</p>';
        if (window.showToast) window.showToast(`Error loading template details: ${error.message || 'Unknown error'}`, 'error');
    }
}

function clearTemplateSummaryDisplay() {
    const templateSummaryDiv = document.getElementById('templateSummary');
    if (templateSummaryDiv) {
        templateSummaryDiv.innerHTML = '<p class="empty-template-message">Please select a master template to see its structure.</p>';
    }
}

async function previewSelectedMasterTemplate(templateId) {
    console.log(`[CaseEdit] Previewing master template ID: ${templateId}`);
    try {
        const template = await apiRequest(`/cases/admin/templates/${templateId}/`);
        const modalPreviewContainer = document.getElementById('templatePreviewContainer'); 
        const modal = document.getElementById('templatePreviewModal');

        if (modal && modalPreviewContainer && typeof generateMasterTemplatePreviewHTML === 'function') { 
            modalPreviewContainer.innerHTML = generateMasterTemplatePreviewHTML(template);
            if (window.openModal) window.openModal('templatePreviewModal'); 
        } else {
             console.warn("[CaseEdit] Preview modal elements or 'generateMasterTemplatePreviewHTML' function not found. Using alert fallback.");
             let previewText = `Previewing Master Template: ${template.name || 'Unknown'}\n`;
             if (template.sections && template.sections.length > 0) {
                previewText += "Sections:\n" + template.sections.map(s => `- ${s.name} ${s.is_required ? '(Required)' : ''}`).join('\n');
             } else {
                previewText += "No sections defined for this template.";
             }
            alert(previewText);
        }
    } catch (error) {
        if (window.showToast) window.showToast("Could not load template preview data.", "error");
        console.error("[CaseEdit] Error previewing master template:", error);
    }
}

function generateMasterTemplatePreviewHTML(template) {
    let sectionsHtml = '<h6>Sections:</h6>';
    if (template.sections && template.sections.length > 0) {
        const sortedSections = [...template.sections].sort((a, b) => (a.order || 0) - (b.order || 0));
        sectionsHtml += '<ul style="list-style:none; padding-left:0;">';
        sortedSections.forEach(section => {
            sectionsHtml += `<li style="padding: 5px 0; border-bottom: 1px solid #eee;">
                <strong>${section.name || 'Unnamed Section'}</strong> ${section.is_required ? '<span style="color:green; font-size:0.9em;">(Required)</span>' : ''}
                <br><small style="color:#777;">Placeholder: ${section.placeholder_text || '<em>None</em>'}</small>
            </li>`;
        });
        sectionsHtml += '</ul>';
    } else {
        sectionsHtml += '<p><em>No sections defined for this template.</em></p>';
    }
    return `
        <h4>${template.name || 'Unnamed Template'}</h4>
        <p>
            <strong>Modality:</strong> ${template.modality_display || template.modality || 'N/A'} | 
            <strong>Body Part:</strong> ${template.body_part_display || template.body_part || 'N/A'}
        </p>
        <p><strong>Description:</strong> ${template.description || '<em>No description.</em>'}</p>
        <hr>
        ${sectionsHtml}
    `;
}

