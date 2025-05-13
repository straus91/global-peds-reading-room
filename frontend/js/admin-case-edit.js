// frontend/js/admin-case-edit.js
// Handles adding and editing radiology cases in the admin panel.
// This script is initialized by admin.js after successful admin authentication.

// --- Global module-level variables ---
let currentCaseId = null; // Stores the ID of the case being edited, if any.
let availableMasterTemplates = []; // Caches master templates for the dropdown.
let availableLanguages = []; // Caches available languages for expert templates.
let activeExpertTemplate = null; // Stores data of the expert template currently being edited.
let loadedCaseDataForEdit = null; // Caches the full case data when in edit mode.

/**
 * Main initialization function for the Add/Edit Case page.
 * This function is assigned to window.initializeCurrentAdminPage and called by admin.js.
 */
async function initializeAddCasePage() {
    console.log("[CaseEdit] Admin auth confirmed. Initializing Add/Edit Case Page logic...");

    // Setup static event listeners for elements always present in the HTML.
    initCommonFormElements();
    
    // Asynchronously load data needed for the form.
    // These calls will use window.showLoading and window.showToast from admin.js.
    await loadMasterTemplatesForDropdown();
    await loadAvailableLanguages();

    // Determine if we are in "add new" or "edit" mode based on URL parameters.
    const urlParams = new URLSearchParams(window.location.search);
    currentCaseId = urlParams.get('edit_id');

    const formTitleElement = document.querySelector('.admin-content .admin-header h1');
    const submitButton = document.querySelector('#addCaseForm button[type="submit"]');

    if (currentCaseId) {
        // --- Edit Mode ---
        console.log(`[CaseEdit] Edit mode for case ID: ${currentCaseId}`);
        if (formTitleElement) formTitleElement.textContent = 'Edit Case';
        document.title = `Edit Case (ID: ${currentCaseId}) - Global Peds Reading Room`;
        if (submitButton) submitButton.textContent = 'Update Case';
        
        await loadCaseForEditing(currentCaseId); // Load existing case data into the form.
        await loadAndDisplayExpertTemplates(currentCaseId); // Load expert templates for this case.
    } else {
        // --- Add New Case Mode ---
        console.log("[CaseEdit] Add New Case mode.");
        if (formTitleElement) formTitleElement.textContent = 'Add New Case';
        document.title = `Add New Case - Global Peds Reading Room`;
        if (submitButton) submitButton.textContent = 'Create Case';
        
        // Ensure at least one finding input field is present.
        const findingsContainer = document.getElementById('findingsContainer');
        if (findingsContainer && findingsContainer.children.length === 0) {
            handleAddFinding(false); // Add one initial finding input, don't focus.
        } else {
            updateFindingsRemoveButtonsState(); // Ensure button state is correct if HTML already has one.
        }
        updateExpertTemplatesDisplay([]); // Display "No expert templates" message.
    }

    // Attach the main form submission handler.
    const caseForm = document.getElementById('addCaseForm');
    if (caseForm) {
        caseForm.removeEventListener('submit', handleCaseFormSubmit); // Prevent duplicates
        caseForm.addEventListener('submit', handleCaseFormSubmit);
    } else {
        console.error("[CaseEdit] CRITICAL: Form #addCaseForm not found in HTML!");
        window.showToast("Error: Case form is missing. Page may not work correctly.", "error");
    }

    // Attach listener for adding new expert language templates.
    const addLangTemplateBtn = document.getElementById('addLangTemplateBtn');
    if (addLangTemplateBtn) {
        addLangTemplateBtn.removeEventListener('click', handleAddLanguageTemplateClick); // Prevent duplicates
        addLangTemplateBtn.addEventListener('click', handleAddLanguageTemplateClick);
    }
    console.log("[CaseEdit] Page initialization complete.");
}

// Assign the main initializer to the global scope so admin.js can call it.
window.initializeCurrentAdminPage = initializeAddCasePage;

/**
 * Initializes event listeners for static form elements like buttons and select dropdowns.
 */
function initCommonFormElements() {
    console.log("[CaseEdit] Initializing common form element listeners...");

    document.getElementById('addFindingBtn')?.addEventListener('click', handleAddFinding);
    document.getElementById('reportTemplate')?.addEventListener('change', function() {
        loadAndDisplayTemplateSummary(this.value);
    });

    document.getElementById('createNewMasterTemplateBtn')?.addEventListener('click', () => {
        const modality = document.getElementById('caseModality')?.value || '';
        const subspecialty = document.getElementById('caseSubspecialty')?.value || '';
        const params = new URLSearchParams({ action: 'create' });
        if (modality) params.append('modality', modality);
        if (subspecialty) {
            const bodyPart = getBodyPartFromSubspecialty(subspecialty); // Helper to map if needed
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
    updateFindingsRemoveButtonsState(); // Initial state for findings remove button
}

/**
 * Helper to map a case's subspecialty code to a body part code for template pre-filling.
 * @param {string} subspecialtyCode - The subspecialty code (e.g., 'NR', 'CH').
 * @returns {string} The corresponding body part code or the original code.
 */
function getBodyPartFromSubspecialty(subspecialtyCode) {
    // This mapping should align with your SubspecialtyChoices and how they relate to template body parts.
    const mapping = {
        'NR': 'NR', // Neuroradiology often maps to Brain or Head/Neck body parts in templates
        'CH': 'CH', // Chest Radiology -> Chest template
        'MK': 'MK', // Musculoskeletal
        'PD': 'PD', // Pediatric
        // Add more specific mappings if 'body_part' in MasterTemplate uses different codes than case 'subspecialty'
    };
    return mapping[subspecialtyCode] || subspecialtyCode; // Fallback
}

/**
 * Fetches active master templates from the API and populates the dropdown.
 */
async function loadMasterTemplatesForDropdown() {
    const reportTemplateSelect = document.getElementById('reportTemplate');
    if (!reportTemplateSelect) {
        console.error("[CaseEdit] Master template select dropdown (#reportTemplate) not found.");
        return;
    }
    reportTemplateSelect.innerHTML = '<option value="">Loading templates...</option>';
    clearTemplateSummaryDisplay(); // Clear any old summary

    try {
        window.showLoading(true, 'Loading master templates...');
        // Fetch all active templates, assuming pagination is handled or page_size is large enough
        const response = await apiRequest('/cases/admin/templates/?is_active=true&page_size=1000');
        availableMasterTemplates = response.results || []; // Store for potential re-use

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

        // If editing a case and its data is already loaded, try to set the selected template
        if (loadedCaseDataForEdit && loadedCaseDataForEdit.master_template) {
            reportTemplateSelect.value = loadedCaseDataForEdit.master_template;
            // Verify if the value was actually set (i.e., the option exists)
            if (reportTemplateSelect.value === String(loadedCaseDataForEdit.master_template)) {
                loadAndDisplayTemplateSummary(loadedCaseDataForEdit.master_template);
            } else {
                console.warn(`[CaseEdit] Previously associated master template (ID: ${loadedCaseDataForEdit.master_template}) is not in the active list.`);
                // Optionally, you could try to fetch and display details for an inactive associated template
                // but the select dropdown would still not show it as a selectable option.
            }
        }
    } catch (error) {
        console.error("[CaseEdit] Error fetching master templates for dropdown:", error);
        reportTemplateSelect.innerHTML = '<option value="">Error loading templates</option>';
        window.showToast(`Failed to load report templates: ${error.message || 'Unknown error'}`, 'error');
    } finally {
        window.showLoading(false);
    }
}

/**
 * Fetches available active languages from the API.
 */
async function loadAvailableLanguages() {
    try {
        const response = await apiRequest('/cases/admin/languages/?is_active=true');
        // API might return paginated results or a direct list. Handle both.
        availableLanguages = (Array.isArray(response.results) ? response.results : (Array.isArray(response) ? response : []));
        console.log("[CaseEdit] Available active languages loaded:", availableLanguages);
    } catch (error) {
        console.error("[CaseEdit] Error fetching available languages:", error);
        window.showToast("Could not load available languages for expert templates.", "error");
        availableLanguages = []; // Ensure it's an empty array on error
    }
}

/**
 * Fetches data for a specific case (in edit mode) and populates the form.
 * @param {string|number} caseId - The ID of the case to load.
 */
async function loadCaseForEditing(caseId) {
    console.log(`[CaseEdit] Loading case data for ID: ${caseId}`);
    window.showLoading(true, `Loading case ${caseId}...`);
    try {
        const caseData = await apiRequest(`/cases/admin/cases/${caseId}/`); // Endpoint for single case admin view
        loadedCaseDataForEdit = caseData; // Cache the loaded data
        populateFormWithCaseData(caseData);
    } catch (error) {
        console.error(`[CaseEdit] Error loading case ${caseId} for editing:`, error);
        loadedCaseDataForEdit = null;
        window.showToast(`Error loading case data: ${error.message || 'Unknown error'}`, 'error');
        const formContainer = document.querySelector('.admin-content .admin-form');
        if (formContainer) { // Display error directly in form area
            formContainer.innerHTML = `<p style="color:red; text-align:center;">Could not load case data. Please check the case ID or try again.</p><p style="text-align:center;"><a href="manage-cases.html" class="btn">Back to Manage Cases</a></p>`;
        }
    } finally {
        window.showLoading(false);
    }
}

/**
 * Populates the main case form with data from a fetched case object.
 * @param {object} caseData - The case data object from the API.
 */
function populateFormWithCaseData(caseData) {
    console.log("[CaseEdit] Populating form with fetched case data:", caseData);
    const form = document.getElementById('addCaseForm');
    if (!form) {
        console.error("[CaseEdit] Form #addCaseForm not found during populateFormWithCaseData.");
        return;
    }

    form.elements['title'].value = caseData.title || '';
    form.elements['subspecialty'].value = caseData.subspecialty || ''; // Assumes backend sends abbreviation
    form.elements['modality'].value = caseData.modality || '';     // Assumes backend sends abbreviation
    form.elements['difficulty'].value = caseData.difficulty || '';

    // Populate Patient Age (number and unit)
    const patientAgeValueInput = form.elements['patientAgeValue'];
    const patientAgeUnitSelect = form.elements['patientAgeUnit'];
    if (caseData.patient_age && patientAgeValueInput && patientAgeUnitSelect) {
        const ageString = String(caseData.patient_age).toLowerCase();
        const parts = ageString.match(/^(\d+)\s*(years|months|days|neonate)$/i); // Updated regex
        if (parts) {
            patientAgeValueInput.value = parts[1]; // The number part
            const unit = parts[2].toLowerCase();   // The unit part
            // Check if the unit exists in the dropdown options
            if (Array.from(patientAgeUnitSelect.options).some(opt => opt.value === unit)) {
                patientAgeUnitSelect.value = unit;
            } else {
                console.warn(`[CaseEdit] Age unit "${unit}" from DB not in select. Defaulting.`);
                patientAgeUnitSelect.value = 'years'; // Default if unit not found
            }
        } else if (ageString === "neonate") { // Handle if patient_age is just "Neonate"
            patientAgeValueInput.value = ''; // Or a conventional value like 0 or 1
            patientAgeUnitSelect.value = 'neonate';
        } else {
            console.warn(`[CaseEdit] Could not parse patient_age string: '${caseData.patient_age}'. Clearing fields.`);
            patientAgeValueInput.value = '';
            patientAgeUnitSelect.value = 'years';
        }
    } else if (patientAgeValueInput && patientAgeUnitSelect) { // If no age data, clear/default
        patientAgeValueInput.value = '';
        patientAgeUnitSelect.value = 'years';
    }

    form.elements['clinical_history'].value = caseData.clinical_history || '';
    form.elements['image_description_placeholder'].value = caseData.image_description_placeholder || '';
    form.elements['image_url_placeholder'].value = caseData.image_url_placeholder || '';

    // ***** NEWLY ADDED: Populate Orthanc Study UID field *****
    if (form.elements['orthanc_study_uid']) { // Check if the element exists on the form
        form.elements['orthanc_study_uid'].value = caseData.orthanc_study_uid || '';
    }
    // ***** END OF ADDITION *****

    // Populate Key Findings
    const findingsContainer = document.getElementById('findingsContainer');
    findingsContainer.innerHTML = ''; // Clear previous findings
    if (caseData.key_findings) {
        const findingsArray = String(caseData.key_findings).split('\n').filter(f => f.trim() !== '');
        if (findingsArray.length > 0) {
            findingsArray.forEach(findingText => {
                const newInputGroup = handleAddFinding(false); // Add new input group, don't focus
                if (newInputGroup) {
                    const newFindingInput = newInputGroup.querySelector('.finding-input');
                    if (newFindingInput) newFindingInput.value = findingText;
                }
            });
        } else {
            handleAddFinding(false); // Add one empty field if key_findings was an empty string
        }
    } else {
        handleAddFinding(false); // Add one empty field if key_findings is null/undefined
    }
    updateFindingsRemoveButtonsState(); // Correctly enable/disable remove buttons

    form.elements['diagnosis'].value = caseData.diagnosis || '';
    form.elements['discussion'].value = caseData.discussion || '';
    form.elements['references'].value = caseData.references || '';

    // Set Master Template dropdown
    const reportTemplateSelect = form.elements['master_template']; // HTML name is master_template
    if (caseData.master_template) { // master_template here is the ID
        reportTemplateSelect.value = caseData.master_template;
        // If the value was successfully set (i.e., the option exists in the dropdown)
        if (reportTemplateSelect.value === String(caseData.master_template)) {
             loadAndDisplayTemplateSummary(caseData.master_template);
        } else {
            console.warn(`[CaseEditPopulate] Master template ID ${caseData.master_template} (from case data) not found or not active in dropdown.`);
            clearTemplateSummaryDisplay();
        }
    } else {
        reportTemplateSelect.value = ""; // Clear selection if no master_template on case
        clearTemplateSummaryDisplay();
    }

    form.elements['status'].value = caseData.status || 'draft';
    form.elements['published_at'].value = caseData.published_at ? caseData.published_at.substring(0, 10) : ''; // Format YYYY-MM-DD

    console.log("[CaseEdit] Form population complete.");
}


/**
 * Fetches and displays the list of expert-filled language templates for the current case.
 * @param {string|number} caseId - The ID of the current case.
 */
async function loadAndDisplayExpertTemplates(caseId) {
    const container = document.getElementById('languageTemplatesContainer');
    if (!container) {
        console.error("[ExpertTpl] Container 'languageTemplatesContainer' not found.");
        return;
    }
    container.innerHTML = '<p>Loading expert templates...</p>';

    try {
        window.showLoading(true, 'Loading expert templates for case...');
        // This endpoint should list CaseTemplate instances for the given case.
        const response = await apiRequest(`/cases/admin/cases/${caseId}/expert-templates/`);
        // The response might be paginated or a direct list.
        // Assuming it's { results: [...] } or directly [...]
        const expertTemplates = response.results || response || [];
        console.log("[ExpertTpl] Fetched expert templates:", expertTemplates);
        updateExpertTemplatesDisplay(expertTemplates, caseId);
    } catch (error) {
        console.error(`[ExpertTpl] Error loading expert templates for case ${caseId}:`, error);
        container.innerHTML = `<p style="color:red;">Could not load expert templates: ${error.message || 'Unknown error'}</p>`;
        window.showToast(`Error loading expert templates: ${error.message || 'Unknown error'}`, 'error');
    } finally {
        window.showLoading(false);
    }
}

/**
 * Renders the list of expert-filled language templates in the UI.
 * @param {Array} expertTemplates - Array of expert template objects.
 * @param {string|number} caseId - The ID of the current case (for delete action context).
 */
function updateExpertTemplatesDisplay(expertTemplates, caseId) {
    const container = document.getElementById('languageTemplatesContainer');
    const noTemplatesMsgEl = document.getElementById('noTemplatesMsg'); // Get existing message element

    if (!container) return;
    container.innerHTML = ''; // Clear previous content

    if (!expertTemplates || expertTemplates.length === 0) {
        if (noTemplatesMsgEl) {
            container.appendChild(noTemplatesMsgEl); // Re-add the existing message element
            noTemplatesMsgEl.style.display = 'block'; // Make sure it's visible
        } else { // Fallback if the #noTemplatesMsg was somehow removed from HTML
            const p = document.createElement('p');
            p.id = 'noTemplatesMsg'; // Assign ID for future reference
            p.style.cssText = 'font-style: italic; color: #777;';
            p.textContent = 'No expert language templates added yet. Select a Master Template and click "+ Add Language Version".';
            container.appendChild(p);
        }
        // Clear any active editor for expert template sections
        const activeEditor = document.querySelector('.expert-template-sections-active-editor'); // A hypothetical class for the active editor container
        if (activeEditor) activeEditor.innerHTML = '';
        activeExpertTemplate = null;
        return;
    }

    if (noTemplatesMsgEl) noTemplatesMsgEl.style.display = 'none'; // Hide if templates exist

    expertTemplates.forEach(et => {
        const div = document.createElement('div');
        div.className = 'language-template-block';
        div.dataset.expertTemplateId = et.id; // This is the CaseTemplate ID
        div.dataset.languageCode = et.language_code; // language_code should come from CaseTemplateSerializer

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

/**
 * Handles the click event for the "+ Add Language Version" button.
 * Shows a modal for selecting a language.
 */
// In frontend/js/admin-case-edit.js

async function handleAddLanguageTemplateClick() {
    const masterTemplateId = document.getElementById('reportTemplate').value;
    if (!masterTemplateId) {
        window.showToast("Please select a Master Report Template for this case first.", "warning");
        return;
    }

    // Ensure current case ID exists, save as draft if not
    if (!currentCaseId) {
        window.showToast("Saving case as draft before adding language versions...", "info");
        const form = document.getElementById('addCaseForm');
        try {
            // Assuming handleCaseFormSubmit is async and updates currentCaseId
            await handleCaseFormSubmit({ preventDefault: () => {}, target: form }, true); // true for saveAsDraft

            if (!currentCaseId) {
                window.showToast("Failed to save the case as a draft. Please save manually and try again.", "error");
                return;
            }
        } catch (error) {
            window.showToast("Error saving case as draft. Please try manually.", "error");
            console.error("Error during auto-draft save:", error);
            return;
        }
    }

    // ***** ADDED: Re-fetch available languages just in case they changed or initial load failed *****
    await loadAvailableLanguages();
    // ***** END ADDED SECTION *****

    if (availableLanguages.length === 0) {
        window.showToast("No active languages are defined in the system. Please add/activate languages in the Django admin.", "warning");
        return;
    }

    const existingLangCodesOnPage = Array.from(document.querySelectorAll('#languageTemplatesContainer .language-template-block'))
                                   .map(el => el.dataset.languageCode);

    const availableLangsForModal = availableLanguages.filter(lang => {
        return lang.code && !existingLangCodesOnPage.includes(lang.code);
    });

    if (availableLangsForModal.length === 0) {
        window.showToast("All available languages have already been added for this case.", "info");
        return;
    }

    const modal = document.getElementById('addLanguageModal');
    const selectEl = document.getElementById('selectNewExpertLang');

    if (!modal || !selectEl) {
        console.error("[CaseEdit] Add language modal or its select element not found.");
        window.showToast("Error: Could not open language selection dialog.", "error");
        return;
    }

    selectEl.innerHTML = '<option value="">-- Select Language --</option>'; // Clear previous options
    console.log("Data for language dropdown:", JSON.stringify(availableLangsForModal, null, 2));

    availableLangsForModal.forEach(lang => {
        const option = document.createElement('option');
        option.value = lang.id; // Use the Language ID for the API call
        option.textContent = `${lang.name} (${lang.code})`;
        selectEl.appendChild(option);
    });

    const confirmBtn = document.getElementById('confirmAddLangBtn');
    // Clone and replace to remove old event listeners and prevent multiple calls
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

    newConfirmBtn.onclick = async () => { // Make this async
        const selectedLangId = selectEl.value;
        if (selectedLangId) {
            await createNewExpertTemplate(currentCaseId, selectedLangId); // Await this
            window.closeModal('addLanguageModal'); // Use global closeModal
        } else {
            window.showToast("Please select a language.", "warning");
        }
    };
    window.openModal('addLanguageModal'); // Use global openModal
}

// New helper function to call the main save logic as a draft
async function triggerSaveAsDraft() {
    const form = document.getElementById('addCaseForm');
    if (!form) return false;

    // We need to replicate the data gathering and API call from handleCaseFormSubmit
    // or refactor handleCaseFormSubmit to be more generally callable.
    // For now, let's assume a refactor of handleCaseFormSubmit is too much.
    // The most direct way is to ensure handleCaseFormSubmit is robust.

    // The previous approach of saveButton.click() was problematic due to event handler restoration timing.
    // Let's try to make handleCaseFormSubmit more directly callable for "save as draft"
    // The main challenge is that it's an event handler.

    // If `handleCaseFormSubmit` can be called programmatically (e.g., by passing a mock event or null):
    // This is a simplification and might need `handleCaseFormSubmit` to be robust to `event` being null or a simple object.
    // Let's assume for a moment that `handleCaseFormSubmit(null, true)` would work.
    await handleCaseFormSubmit({
        preventDefault: () => {}, // Mock preventDefault
        target: form // Provide the form as the target
    }, true); // true for saveAsDraft

    return !!currentCaseId; // Return true if currentCaseId was set (meaning save likely succeeded)
}

/**
 * Makes an API call to create a new expert-filled template for a given case and language.
 * @param {string|number} caseId - The ID of the case.
 * @param {string|number} languageId - The ID of the language.
 */
async function createNewExpertTemplate(caseId, languageId) {
    console.log(`[ExpertTpl] Creating new expert template for case ${caseId}, language ID ${languageId}`);
    window.showLoading(true, 'Adding language version...');
    try {
        // API endpoint from project doc: POST /api/cases/admin/cases/<case_pk>/expert-templates/
        // Body: {language: <lang_id>}
        const newExpertTemplate = await apiRequest(
            `/cases/admin/cases/${caseId}/expert-templates/`,
            {
                method: 'POST',
                body: JSON.stringify({ language: parseInt(languageId) })
            }
        );
        window.showToast(`Expert template for ${newExpertTemplate.language_name || 'the selected language'} added successfully.`, 'success');
        await loadAndDisplayExpertTemplates(caseId); // Refresh the list of expert templates

        // Optionally, find the newly added template block and open its editor
        const newTemplateBlock = document.querySelector(`.language-template-block[data-expert-template-id="${newExpertTemplate.id}"]`);
        if (newTemplateBlock) {
            const sectionsDisplayContainerId = `expert-sections-for-${newExpertTemplate.id}`;
            handleEditExpertTemplateContent(newExpertTemplate, sectionsDisplayContainerId); // Open editor
        }
    } catch (error) {
        console.error('[ExpertTpl] Error creating new expert template:', error);
        const errorDetail = error.data?.detail || (error.data && typeof error.data === 'object' ? JSON.stringify(error.data) : error.message) || 'Unknown error';
        window.showToast(`Failed to add language version: ${errorDetail}`, 'error');
    } finally {
        window.showLoading(false);
    }
}

/**
 * Makes an API call to delete an expert-filled template.
 * @param {string|number} expertTemplateId - The ID of the CaseTemplate to delete.
 * @param {string|number} caseId - The ID of the parent case (for refreshing the list).
 */
async function handleDeleteExpertTemplate(expertTemplateId, caseId) {
    if (!confirm(`Are you sure you want to delete this expert template version (ID: ${expertTemplateId})? All its content will be lost.`)) {
        return;
    }
    console.log(`[ExpertTpl] Deleting expert template ID: ${expertTemplateId} for case ID: ${caseId}`);
    window.showLoading(true, 'Deleting expert template version...');
    try {
        // API endpoint from project doc: DELETE /api/cases/admin/cases/<case_pk>/expert-templates/<case_template_pk>/
        await apiRequest(`/cases/admin/cases/${caseId}/expert-templates/${expertTemplateId}/`, {
            method: 'DELETE'
        });
        window.showToast('Expert template version deleted successfully.', 'success');
        await loadAndDisplayExpertTemplates(caseId); // Refresh the list

        // If the deleted template was being edited, clear its editor display
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
        window.showToast(`Failed to delete expert template version: ${error.message || 'Unknown error'}`, 'error');
    } finally {
        window.showLoading(false);
    }
}

/**
 * Handles the "Edit Content" button click for an expert template.
 * Toggles the display of the section editor for that template.
 * @param {object} expertTemplateData - The data of the expert template to edit.
 * @param {string} containerId - The ID of the div that will hold the section editor.
 */
function handleEditExpertTemplateContent(expertTemplateData, containerId) {
    console.log('[ExpertTpl] Toggling edit content for:', expertTemplateData, "Target container ID:", containerId);
    const targetFieldsContainer = document.getElementById(containerId);
    if (!targetFieldsContainer) {
        console.error(`[ExpertTpl] Target container for sections (#${containerId}) not found.`);
        return;
    }

    // Collapse all other open expert template editors on the page
    document.querySelectorAll('#languageTemplatesContainer .template-fields-container').forEach(fc => {
        if (fc.id !== containerId && fc.style.display === 'block') { // If it's another container and it's visible
            fc.style.display = 'none';
            fc.innerHTML = '<p class="template-placeholder">Click "Edit Content" to load sections.</p>';
        }
    });
    
    // Toggle display of the clicked editor
    if (targetFieldsContainer.style.display === 'block' && activeExpertTemplate && activeExpertTemplate.id === expertTemplateData.id) {
        // If it's already open and is the active one, close it
        targetFieldsContainer.style.display = 'none';
        targetFieldsContainer.innerHTML = '<p class="template-placeholder">Click "Edit Content" to load sections.</p>';
        activeExpertTemplate = null;
    } else {
        // Open it (or switch to it if another was open)
        targetFieldsContainer.style.display = 'block';
        targetFieldsContainer.innerHTML = '<p>Loading sections content...</p>'; // Placeholder while fetching
        activeExpertTemplate = expertTemplateData; // Set this as the one being edited
        renderExpertTemplateSectionsForEditing(expertTemplateData, targetFieldsContainer);
    }
}

/**
 * Fetches (if needed) and renders the sections of an expert template for editing.
 * @param {object} expertTemplate - The CaseTemplate object (might be summary or detailed).
 * @param {HTMLElement} containerElement - The DOM element to render the sections into.
 */
async function renderExpertTemplateSectionsForEditing(expertTemplate, containerElement) {
    let sectionsToRender = expertTemplate.section_contents;

    // If section_contents are not present or empty (might be a summary object from list view),
    // fetch the full CaseTemplate details.
    if ((!sectionsToRender || sectionsToRender.length === 0) && expertTemplate.id) {
        try {
            window.showLoading(true, `Loading sections for ${expertTemplate.language_name || expertTemplate.language_code}...`);
            // API endpoint from project doc: GET /api/cases/admin/case-templates/<case_template_pk>/
            const detailedTemplate = await apiRequest(`/cases/admin/case-templates/${expertTemplate.id}/`);
            sectionsToRender = detailedTemplate.section_contents; // Update with full data
            // Update activeExpertTemplate if it was a summary object, to ensure it has full section data
            if (activeExpertTemplate && activeExpertTemplate.id === expertTemplate.id) {
                activeExpertTemplate = detailedTemplate; // Now activeExpertTemplate has full section_contents
            }
        } catch (err) {
            console.error("Failed to fetch detailed sections for expert template:", err);
            containerElement.innerHTML = `<p style="color:red;">Could not load sections: ${err.message || 'Unknown error'}</p>`;
            window.showLoading(false);
            return;
        } finally {
            window.showLoading(false);
        }
    }
    
    if (!sectionsToRender || sectionsToRender.length === 0) {
        containerElement.innerHTML = '<p>This expert template has no sections. This might be because the associated Master Template has no sections defined, or they failed to load.</p>';
        return;
    }

    let sectionsHTML = '';
    // sectionsToRender should already be ordered if sourced from 'section_contents_ordered' in CaseTemplateSerializer
    sectionsToRender.forEach(secContent => {
        // secContent.id is the ID of the CaseTemplateSectionContent record
        sectionsHTML += `
            <div class="form-group template-section-item" data-casetemplatesectioncontent-id="${secContent.id}">
                <label for="expert_sec_content_${secContent.id}">
                    ${secContent.master_section_name || 'Unnamed Section'} 
                    ${secContent.master_section_is_required ? '<span class="required" style="color:red;">*</span>' : ''}
                </label>
                <textarea id="expert_sec_content_${secContent.id}" class="form-control expert-section-content-input" 
                          rows="4" placeholder="${secContent.master_section_placeholder || ''}">${secContent.content || ''}</textarea>
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

    // Add event listener to the save button for this specific editor instance
    const saveBtn = containerElement.querySelector('.save-this-expert-content-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', (e) => {
            const caseTemplateId = e.target.dataset.casetemplateId;
            handleSaveExpertTemplateContent(caseTemplateId, containerElement); // Pass container to find inputs
        });
    }
}

/**
 * Handles saving the edited content of an expert template's sections.
 * @param {string|number} caseTemplateId - The ID of the CaseTemplate being saved.
 * @param {HTMLElement} fieldsContainer - The DOM element containing the section input fields.
 */
async function handleSaveExpertTemplateContent(caseTemplateId, fieldsContainer) {
    if (!caseTemplateId) {
        window.showToast("Cannot save: No active expert template specified.", "error");
        return;
    }
    if (!fieldsContainer) { // Should be the specific div holding this template's sections
        window.showToast("Cannot save: Content editor container not found.", "error");
        return;
    }

    const sectionInputs = fieldsContainer.querySelectorAll('.expert-section-content-input');
    const payload = []; // Array of {id: CaseTemplateSectionContent_id, content: "..."}

    sectionInputs.forEach(input => {
        const sectionItemDiv = input.closest('.template-section-item');
        const caseTemplateSectionContentId = sectionItemDiv.dataset.casetemplatesectioncontentId;
        const content = input.value; // No trim, preserve user formatting
        payload.push({
            id: parseInt(caseTemplateSectionContentId),
            content: content
        });
    });

    const langName = activeExpertTemplate?.language_name || activeExpertTemplate?.language_code || 'template';
    console.log(`[ExpertTpl] Saving content for CaseTemplate ID ${caseTemplateId} (${langName}). Payload:`, payload);
    window.showLoading(true, `Saving content for ${langName}...`);

    try {
        // API from project doc: PUT /api/cases/admin/case-templates/<case_template_pk>/update-sections/
        // Body: list of {"id": <ctsc_id>, "content": "new_text"}
        const updatedCaseTemplateWithSections = await apiRequest(
            `/cases/admin/case-templates/${caseTemplateId}/update-sections/`, 
            {
                method: 'PUT',
                body: JSON.stringify(payload)
            }
        );
        window.showToast(`${langName} content saved successfully!`, 'success');
        
        // Update the local activeExpertTemplate object with the newly saved section_contents
        // This is important if the user continues to edit or if other parts of the UI depend on it.
        if (activeExpertTemplate && activeExpertTemplate.id.toString() === caseTemplateId.toString()) {
            activeExpertTemplate.section_contents = updatedCaseTemplateWithSections.section_contents;
        }
        // The textareas already reflect the new content visually. No re-render of inputs is strictly necessary
        // unless the API response could change IDs or order, which is not expected for this endpoint.

    } catch (error) {
        console.error('[ExpertTpl] Error saving expert template content:', error);
        const errorDetail = error.data?.detail || (error.data && typeof error.data === 'object' ? JSON.stringify(error.data) : error.message) || 'Unknown error';
        window.showToast(`Failed to save content: ${errorDetail}`, 'error');
    } finally {
        window.showLoading(false);
    }
}

/**
 * Handles the submission of the main case form (create or update).
 */
async function handleCaseFormSubmit(event, saveAsDraft = false) {
    event.preventDefault();
    console.log(`[CaseEdit] Main case form submitted. Edit Mode: ${!!currentCaseId}, Save as Draft: ${saveAsDraft}`);
    const form = event.target || document.getElementById('addCaseForm');

    // Consolidate Patient Age
    const patientAgeValue = form.elements['patientAgeValue'].value;
    const patientAgeUnit = form.elements['patientAgeUnit'].value;
    let combinedPatientAge = "";
    if (patientAgeUnit === "neonate" && !patientAgeValue) {
        combinedPatientAge = "Neonate";
    } else if (patientAgeValue && patientAgeUnit) {
        combinedPatientAge = `${patientAgeValue} ${patientAgeUnit}`;
    }

    // Consolidate Key Findings
    const findingsInputs = form.querySelectorAll('input[name="key_findings_list_item"]');
    const findingsArray = Array.from(findingsInputs).map(input => input.value.trim()).filter(value => value !== "");
    const combinedKeyFindings = findingsArray.join('\n');

    // Build the payload
    const formData = new FormData(form);
    const caseDataPayload = {};
    for (let [key, value] of formData.entries()) {
        if (['key_findings_list_item', 'patientAgeValue', 'patientAgeUnit'].includes(key)) {
            continue;
        }
        if (key === 'master_template') {
            caseDataPayload[key] = value ? parseInt(value, 10) : null;
        } else if (key === 'published_at') {
            caseDataPayload[key] = value || null;
        } else {
            caseDataPayload[key] = typeof value === 'string' ? value.trim() : value;
        }
    }
    caseDataPayload['patient_age'] = combinedPatientAge || null;
    caseDataPayload['key_findings'] = combinedKeyFindings;

    // Force draft status if saveAsDraft is true
    if (saveAsDraft) {
        caseDataPayload['status'] = 'draft';
    } else if (!caseDataPayload['status']) {
        caseDataPayload['status'] = 'draft';
    }

    console.log("[CaseEdit] Case data payload for API:", caseDataPayload);

    const method = currentCaseId ? 'PUT' : 'POST';
    const endpoint = currentCaseId ? `/cases/admin/cases/${currentCaseId}/` : '/cases/admin/cases/';
    const actionText = currentCaseId ? 'Updating' : 'Creating';

    window.showLoading(true, `${actionText} case...`);
    try {
        const response = await apiRequest(endpoint, {
            method: method,
            body: JSON.stringify(caseDataPayload),
        });
        console.log(`[CaseEdit] Case ${actionText.toLowerCase()} successful:`, response);
        window.showToast(`Case ${actionText.toLowerCase().replace(/ing$/, 'ed')} successfully!`, 'success');
        
        loadedCaseDataForEdit = response;

        if (!currentCaseId && response.id) {
            currentCaseId = response.id; // Store the new case ID
            
            // Update the URL without reloading if we just created a new case
            const newUrl = `add-case.html?edit_id=${response.id}`;
            window.history.replaceState({}, document.title, newUrl);
            
            // Update the form title and button
            const formTitleElement = document.querySelector('.admin-content .admin-header h1');
            const submitButton = document.querySelector('#addCaseForm button[type="submit"]');
            if (formTitleElement) formTitleElement.textContent = 'Edit Case';
            if (submitButton) submitButton.textContent = 'Update Case';
            
            // Load expert templates for the new case
            await loadAndDisplayExpertTemplates(currentCaseId);
        } else if (currentCaseId) {
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
        window.showToast(`Error: ${errorMsg}`, 'error', 5000);
    } finally {
        window.showLoading(false);
    }
}

/**
 * Adds a new input field for a key finding.
 * @param {boolean} focusNewInput - Whether to focus the newly added input field.
 * @returns {HTMLElement|null} The newly created finding input group element, or null if container not found.
 */
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
    // Ensure the name attribute is consistent for collecting findings
    newInputGroup.innerHTML = `
        <input type="text" name="key_findings_list_item" class="finding-input" placeholder="Enter key finding #${newIndex}" required>
        <button type="button" class="remove-finding-btn">Remove</button>
    `;

    const newFindingInput = newInputGroup.querySelector('.finding-input');
    const removeBtn = newInputGroup.querySelector('.remove-finding-btn');

    removeBtn.addEventListener('click', function() {
        this.parentElement.remove(); // Remove the entire group
        updateFindingsRemoveButtonsState();
        // Optional: re-number placeholders after removal if desired
        // reNumberFindingPlaceholders(); 
    });

    findingsContainer.appendChild(newInputGroup);
    updateFindingsRemoveButtonsState(); // Update button states after adding

    if (focusNewInput && newFindingInput) {
        newFindingInput.focus();
    }
    return newInputGroup; // Return the group for potential value setting (e.g., in populateForm)
}

/**
 * Enables or disables the "Remove" button for key findings based on how many exist.
 * The first finding cannot be removed.
 */
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

/**
 * Fetches and displays a summary of the selected master template.
 * @param {string|number} templateId - The ID of the master template.
 */
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
        window.showToast(`Error loading template details: ${error.message || 'Unknown error'}`, 'error');
    }
}

/**
 * Clears the master template summary display area.
 */
function clearTemplateSummaryDisplay() {
    const templateSummaryDiv = document.getElementById('templateSummary');
    if (templateSummaryDiv) {
        templateSummaryDiv.innerHTML = '<p class="empty-template-message">Please select a master template to see its structure.</p>';
    }
}

/**
 * Handles the preview of a selected master template in a modal.
 * @param {string|number} templateId - The ID of the master template to preview.
 */
async function previewSelectedMasterTemplate(templateId) {
    console.log(`[CaseEdit] Previewing master template ID: ${templateId}`);
    try {
        const template = await apiRequest(`/cases/admin/templates/${templateId}/`);
        const modalPreviewContainer = document.getElementById('templatePreviewContainer'); 
        const modal = document.getElementById('templatePreviewModal');

        if (modal && modalPreviewContainer && typeof generateMasterTemplatePreviewHTML === 'function') { 
            modalPreviewContainer.innerHTML = generateMasterTemplatePreviewHTML(template);
            window.openModal('templatePreviewModal'); // Use global openModal from admin.js
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
        window.showToast("Could not load template preview data.", "error");
        console.error("[CaseEdit] Error previewing master template:", error);
    }
}

/**
 * Generates HTML for previewing a master template's structure.
 * @param {object} template - The master template data object.
 * @returns {string} HTML string for the preview.
 */
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

// Note: showLoading, showToast, openModal, closeModal are expected to be globally available
// from admin.js. If they are not, define simple fallbacks here or ensure admin.js loads first
// and provides them on the window object.
