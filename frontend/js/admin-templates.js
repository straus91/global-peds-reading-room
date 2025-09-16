// frontend/js/admin-templates.js
// Manages the "Manage Report Templates" admin page.

(function() {
    'use strict';

    // --- Global State & API Wrapper ---
    const templatesState = {
        languages: [], // Populated from API
        // UPDATED modalityOptions with abbreviations and descriptive labels
        modalityOptions: [
            { value: 'CT', label: 'CT - Computer Tomography' },
            { value: 'MR', label: 'MR - Magnetic Resonance' },
            { value: 'US', label: 'US - Ultrasound' },
            { value: 'XR', label: 'XR - X-ray' },
            { value: 'FL', label: 'FL - Fluoroscopy' },
            { value: 'NM', label: 'NM - Nuclear Medicine' },
            { value: 'OT', label: 'OT - Other' }
        ],
        // UPDATED bodyPartOptions (using Subspecialty list) with abbreviations and descriptive labels
        bodyPartOptions: [
            { value: 'BR', label: 'BR - Breast (Imaging and Interventional)' },
            { value: 'CA', label: 'CA - Cardiac Radiology' },
            { value: 'CH', label: 'CH - Chest Radiology' },
            { value: 'ER', label: 'ER - Emergency Radiology' },
            { value: 'GI', label: 'GI - Gastrointestinal Radiology' },
            { value: 'GU', label: 'GU - Genitourinary Radiology' },
            { value: 'HN', label: 'HN - Head and Neck' },
            { value: 'IR', label: 'IR - Interventional Radiology' },
            { value: 'MK', label: 'MK - Musculoskeletal Radiology' },
            { value: 'NM', label: 'NM - Nuclear Medicine (Subspecialty)' }, // Clarified it's the subspecialty context
            { value: 'NR', label: 'NR - Neuroradiology' },
            { value: 'OB', label: 'OB - Obstetric/Gynecologic Radiology' },
            { value: 'OI', label: 'OI - Oncologic Imaging' },
            { value: 'VA', label: 'VA - Vascular Radiology' },
            { value: 'PD', label: 'PD - Pediatric Radiology' },
            { value: 'OT', label: 'OT - Other' }
        ],
        currentEditTemplateId: null,
        currentEditSectionData: null, // Stores {id, title, placeholder, required, index, translations}
        currentSectionsInForm: [], // Holds section objects currently in the create/edit form UI
        pagination: {
            currentPage: 1,
            totalPages: 1,
            totalItems: 0,
            nextUrl: null,
            prevUrl: null,
            itemsPerPage: 10 // Should match backend page_size
        },
        currentFilters: { // For the template list
            searchTerm: '',
            modality: '',
            bodyPart: ''
        }
    };

    // DOM Elements Cache
    const DOM = {};

    // --- API Interaction --- (using global apiRequest from api.js)
    const templatesApi = {
        getLanguages: async () => apiRequest('/cases/admin/languages/?is_active=true&page_size=100'), // Get all active languages
        getTemplates: async (params = {}) => {
            const query = new URLSearchParams();
            if (params.page) query.append('page', params.page);
            if (params.searchTerm) query.append('search', params.searchTerm);
            if (params.modality) query.append('modality', params.modality);
            if (params.bodyPart) query.append('body_part', params.bodyPart); // Ensure backend filter name is 'body_part'
            query.append('page_size', templatesState.pagination.itemsPerPage);
            
            return apiRequest(`/cases/admin/templates/?${query.toString()}`);
        },
        getTemplateById: async (id) => apiRequest(`/cases/admin/templates/${id}/`),
        createTemplate: async (data) => apiRequest('/cases/admin/templates/', { method: 'POST', body: JSON.stringify(data) }),
        updateTemplate: async (id, data) => apiRequest(`/cases/admin/templates/${id}/`, { method: 'PUT', body: JSON.stringify(data) }),
        deleteTemplate: async (id) => apiRequest(`/cases/admin/templates/${id}/`, { method: 'DELETE' })
    };

    // --- Initialization ---
    document.addEventListener('DOMContentLoaded', function() {
        if (!window.location.pathname.includes('manage-templates.html')) return;
        console.log("[AdminTemplates] Initializing Manage Templates page...");
        cacheDOMElements();
        setupEventListeners();
        loadInitialData();
        handleUrlParams(); // Check for action=create in URL
    });

    function cacheDOMElements() {
        DOM.tabs = document.querySelectorAll('.admin-tabs .tab');
        DOM.tabContents = {
            list: document.getElementById('templateListContainer'),
            create: document.getElementById('createTemplateContainer')
        };
        DOM.masterTemplatesTableBody = document.getElementById('masterTemplatesTableBody');
        DOM.templateListPaginationContainer = document.getElementById('templateListPaginationContainer');
        
        // Search and Filter for List
        DOM.templateSearchInput = document.getElementById('templateSearchInput');
        DOM.templateSearchBtn = document.getElementById('templateSearchBtn');
        DOM.listModalityFilter = document.getElementById('listModalityFilter');
        DOM.listBodyPartFilter = document.getElementById('listBodyPartFilter');

        // Create/Edit Form Elements
        DOM.templateForm = document.getElementById('templateForm');
        DOM.templateFormTitle = document.getElementById('templateFormTitle');
        DOM.templateIdInput = document.getElementById('templateId'); // Hidden input for ID
        DOM.templateNameInput = document.getElementById('templateName');
        DOM.templateModalitySelect = document.getElementById('templateModality');
        DOM.templateBodyPartSelect = document.getElementById('templateBodyPart');
        DOM.templateDescriptionTextarea = document.getElementById('templateDescription');
        DOM.templateIsActiveCheckbox = document.getElementById('templateIsActive');
        DOM.templateSectionsContainer = document.getElementById('templateSectionsContainer');
        DOM.addSectionBtn = document.getElementById('addSectionBtn');
        DOM.formLanguageTabsContainer = document.getElementById('formLanguageTabs');
        DOM.languageTranslationsContainer = document.getElementById('languageTranslationsContainer');
        DOM.formSaveBtn = document.getElementById('formSaveBtn');
        DOM.formCancelBtn = document.getElementById('formCancelBtn');
        DOM.formPreviewTemplateBtn = document.getElementById('formPreviewTemplateBtn');


        // Section Modal Elements
        DOM.sectionModal = document.getElementById('sectionModal');
        DOM.sectionModalTitle = document.getElementById('sectionModalTitle');
        DOM.sectionModalEditIndex = document.getElementById('sectionModalEditIndex'); // Hidden input for index
        DOM.sectionTitleInput = document.getElementById('sectionTitle');
        DOM.sectionPlaceholderInput = document.getElementById('sectionPlaceholder');
        DOM.sectionRequiredCheckbox = document.getElementById('sectionRequired');
        DOM.saveSectionBtn = document.getElementById('saveSectionBtn');

        // Preview Modal
        DOM.templatePreviewModal = document.getElementById('templatePreviewModal');
        DOM.templatePreviewContainer = document.getElementById('templatePreviewContainer');
        
        // Delete Modal
        DOM.deleteConfirmationModal = document.getElementById('deleteConfirmationModal');
        DOM.deleteConfirmMessage = document.getElementById('deleteConfirmMessage');
        DOM.confirmDeleteMasterTemplateBtn = document.getElementById('confirmDeleteMasterTemplateBtn');

        console.log("[AdminTemplates] DOM elements cached.");
    }

    function setupEventListeners() {
        // Tab switching
        DOM.tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                switchTab(this.dataset.tab);
            });
        });

        // List Search and Filters
        DOM.templateSearchBtn?.addEventListener('click', () => TemplateListManager.handleFilterOrSearchChange());
        DOM.templateSearchInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') TemplateListManager.handleFilterOrSearchChange();
        });
        DOM.listModalityFilter?.addEventListener('change', () => TemplateListManager.handleFilterOrSearchChange());
        DOM.listBodyPartFilter?.addEventListener('change', () => TemplateListManager.handleFilterOrSearchChange());


        // Form actions
        DOM.templateForm?.addEventListener('submit', TemplateFormManager.handleSubmit);
        DOM.addSectionBtn?.addEventListener('click', () => ModalManager.showSectionModal()); // For new section
        DOM.formCancelBtn?.addEventListener('click', () => {
            if (confirm("Are you sure you want to cancel? Any unsaved changes will be lost.")) {
                TemplateFormManager.resetForm();
                switchTab('template-list');
            }
        });
        DOM.formPreviewTemplateBtn?.addEventListener('click', TemplateFormManager.handlePreview);


        // Section Modal actions
        DOM.saveSectionBtn?.addEventListener('click', ModalManager.handleSaveSection);
        DOM.sectionModal?.querySelectorAll('[data-dismiss-modal="sectionModal"]').forEach(btn => {
            btn.addEventListener('click', () => ModalManager.closeModal('sectionModal'));
        });
        
        // Preview Modal Close
        DOM.templatePreviewModal?.querySelectorAll('[data-dismiss-modal="templatePreviewModal"]').forEach(btn => {
            btn.addEventListener('click', () => ModalManager.closeModal('templatePreviewModal'));
        });

        // Delete Modal actions
        DOM.confirmDeleteMasterTemplateBtn?.addEventListener('click', TemplateListManager.handleConfirmDelete);
        DOM.deleteConfirmationModal?.querySelectorAll('[data-dismiss-modal="deleteConfirmationModal"]').forEach(btn => {
            btn.addEventListener('click', () => ModalManager.closeModal('deleteConfirmationModal'));
        });

        // General modal close on ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                ModalManager.closeAllModals();
            }
        });
        console.log("[AdminTemplates] Event listeners set up.");
    }

    function handleUrlParams() {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('action') === 'create') {
            switchTab('create-template'); // Switch to the create/edit tab
            TemplateFormManager.resetForm(); // Ensure it's a clean form

            // Pre-fill from URL params if provided
            const modality = urlParams.get('modality');
            const bodyPart = urlParams.get('bodyPart'); // Note: HTML uses name="body_part"
            if (modality && DOM.templateModalitySelect) DOM.templateModalitySelect.value = modality;
            if (bodyPart && DOM.templateBodyPartSelect) DOM.templateBodyPartSelect.value = bodyPart;
            
            // Clean URL (optional, to prevent re-triggering on refresh)
            // window.history.replaceState({}, document.title, window.location.pathname + window.location.hash);
        }
    }

    async function loadInitialData() {
        showLoading(true, "Loading initial data...");
        try {
            // Populate filter dropdowns first as they use the same options as the form
            Utils.populateSelect(DOM.listModalityFilter, templatesState.modalityOptions, "All Modalities");
            Utils.populateSelect(DOM.listBodyPartFilter, templatesState.bodyPartOptions, "All Body Parts/Regions");
            
            // Populate form dropdowns (these are static in HTML now, but JS might adjust them or use them for validation)
            // If they are purely static in HTML, this step might not be needed for form population,
            // but good to have the options available in JS state.
            // Utils.populateSelect(DOM.templateModalitySelect, templatesState.modalityOptions, "Select Modality");
            // Utils.populateSelect(DOM.templateBodyPartSelect, templatesState.bodyPartOptions, "Select Body Part/Region");


            const langResponse = await templatesApi.getLanguages();
            templatesState.languages = (langResponse.results || langResponse || []).filter(lang => lang.is_active);
            TemplateFormManager.populateLanguageTabs(); // Populate language tabs in the form

            await TemplateListManager.loadAndRenderTemplates(); // Load initial list of templates
        } catch (error) {
            console.error("[AdminTemplates] Error loading initial data:", error);
            showToast(`Failed to load initial data: ${error.message}`, 'error');
        } finally {
            showLoading(false);
        }
    }

    function switchTab(tabName) {
        DOM.tabs.forEach(t => t.classList.remove('active'));
        document.querySelector(`.admin-tabs .tab[data-tab="${tabName}"]`)?.classList.add('active');

        Object.values(DOM.tabContents).forEach(content => content.classList.remove('active'));
        if (DOM.tabContents[tabName === 'template-list' ? 'list' : 'create']) {
            DOM.tabContents[tabName === 'template-list' ? 'list' : 'create'].classList.add('active');
        }

        if (tabName === 'create-template' && !templatesState.currentEditTemplateId) {
            // If switching to create tab and not in edit mode, reset form
            TemplateFormManager.resetForm();
        } else if (tabName === 'template-list') {
            TemplateFormManager.resetForm(); // Also reset form when switching away from create/edit
            TemplateListManager.loadAndRenderTemplates(); // Refresh list
        }
        console.log(`[AdminTemplates] Switched to tab: ${tabName}`);
    }

    const Utils = {
        populateSelect: function(selectElement, optionsArray, defaultOptionText = "Select an option") {
            if (!selectElement) return;
            selectElement.innerHTML = `<option value="">${defaultOptionText}</option>`;
            optionsArray.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt.value;
                option.textContent = opt.label; // Assumes optionsArray has {value: '...', label: '...'}
                selectElement.appendChild(option);
            });
        },
        escapeHtml: function(unsafe) { // Basic HTML escaping
            if (unsafe === null || typeof unsafe === 'undefined') return '';
            return String(unsafe)
                 .replace(/&/g, "&amp;")
                 .replace(/</g, "&lt;")
                 .replace(/>/g, "&gt;")
                 .replace(/"/g, "&quot;")
                 .replace(/'/g, "&#039;");
        }
    };

    // --- Template List Management ---
    const TemplateListManager = {
        loadAndRenderTemplates: async function(page = 1) {
            showLoading(true, "Loading templates...");
            DOM.masterTemplatesTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center;">Loading...</td></tr>`;
            try {
                templatesState.currentFilters.searchTerm = DOM.templateSearchInput?.value || '';
                templatesState.currentFilters.modality = DOM.listModalityFilter?.value || '';
                templatesState.currentFilters.bodyPart = DOM.listBodyPartFilter?.value || '';

                const params = { 
                    page, 
                    searchTerm: templatesState.currentFilters.searchTerm,
                    modality: templatesState.currentFilters.modality,
                    bodyPart: templatesState.currentFilters.bodyPart
                };
                const response = await templatesApi.getTemplates(params);
                
                this.renderTable(response.results || []);
                templatesState.pagination = {
                    currentPage: page,
                    totalItems: response.count || 0,
                    totalPages: Math.ceil((response.count || 0) / templatesState.pagination.itemsPerPage),
                    nextUrl: response.next,
                    prevUrl: response.previous,
                    itemsPerPage: templatesState.pagination.itemsPerPage
                };
                this.renderPagination();

            } catch (error) {
                console.error("[AdminTemplates] Error fetching templates:", error);
                DOM.masterTemplatesTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:red;">Failed to load templates.</td></tr>`;
                showToast(`Error loading templates: ${error.message}`, 'error');
            } finally {
                showLoading(false);
            }
        },

        renderTable: function(templates) {
            DOM.masterTemplatesTableBody.innerHTML = ''; // Clear
            if (templates.length === 0) {
                DOM.masterTemplatesTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center;">No master templates found.</td></tr>`;
                return;
            }
            templates.forEach(template => {
                const row = DOM.masterTemplatesTableBody.insertRow();
                row.dataset.templateId = template.id;
                row.innerHTML = `
                    <td>${template.id}</td>
                    <td>${Utils.escapeHtml(template.name)}</td>
                    <td>${Utils.escapeHtml(template.modality_display || template.modality)}</td>
                    <td>${Utils.escapeHtml(template.body_part_display || template.body_part)}</td>
                    <td>${template.sections?.length || 0}</td>
                    <td><span class="status-badge ${template.is_active ? 'active' : 'inactive'}">${template.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td class="actions-cell">
                        <button class="action-btn view-btn" data-id="${template.id}" title="Preview">👁️</button>
                        <button class="action-btn edit-btn" data-id="${template.id}" title="Edit">✏️</button>
                        <button class="action-btn duplicate-btn" data-id="${template.id}" title="Duplicate">📋</button>
                        <button class="action-btn delete-btn" data-id="${template.id}" title="Delete">🗑️</button>
                    </td>
                `;
            });
            this.attachActionListeners();
        },
        
        attachActionListeners: function() {
            DOM.masterTemplatesTableBody.querySelectorAll('.action-btn').forEach(btn => {
                // Simple way to avoid duplicate listeners if re-rendering frequently
                const newBtn = btn.cloneNode(true);
                btn.parentNode.replaceChild(newBtn, btn);

                if (newBtn.classList.contains('view-btn')) newBtn.addEventListener('click', this.handleViewAction);
                if (newBtn.classList.contains('edit-btn')) newBtn.addEventListener('click', this.handleEditAction);
                if (newBtn.classList.contains('duplicate-btn')) newBtn.addEventListener('click', this.handleDuplicateAction);
                if (newBtn.classList.contains('delete-btn')) newBtn.addEventListener('click', this.handleDeleteAction);
            });
        },

        handleViewAction: async function(event) {
            const templateId = event.currentTarget.dataset.id;
            ModalManager.showPreviewModalById(templateId);
        },
        handleEditAction: async function(event) {
            const templateId = event.currentTarget.dataset.id;
            showLoading(true, `Loading template ${templateId} for editing...`);
            try {
                const template = await templatesApi.getTemplateById(templateId);
                TemplateFormManager.populateFormForEdit(template);
                switchTab('create-template');
            } catch (e) { showToast(`Error loading template for editing: ${e.message}`, "error"); }
            finally { showLoading(false); }
        },
        handleDuplicateAction: async function(event) {
            const templateId = event.currentTarget.dataset.id;
             if (!confirm("Are you sure you want to duplicate this template? A new template form will be pre-filled with its details.")) return;
            showLoading(true, `Duplicating template ${templateId}...`);
            try {
                const template = await templatesApi.getTemplateById(templateId);
                TemplateFormManager.populateFormForDuplicate(template);
                switchTab('create-template');
                showToast('Template duplicated. Modify and save as new.', 'info');
            } catch (e) { showToast(`Error duplicating template: ${e.message}`, "error"); }
            finally { showLoading(false); }
        },
        handleDeleteAction: function(event) {
            const templateId = event.currentTarget.dataset.id;
            ModalManager.showDeleteConfirmModal(templateId);
        },
        handleConfirmDelete: async function() { // Called by ModalManager
            const templateId = DOM.deleteConfirmationModal.dataset.templateId;
            if (!templateId) return;
            showLoading(true, `Deleting template ${templateId}...`);
            try {
                await templatesApi.deleteTemplate(templateId);
                showToast(`Template ID ${templateId} deleted successfully.`, 'success');
                TemplateListManager.loadAndRenderTemplates(templatesState.pagination.currentPage); // Refresh current page
            } catch (e) { showToast(`Error deleting template: ${e.message || 'Unknown error'}`, 'error'); }
            finally {
                showLoading(false);
                ModalManager.closeModal('deleteConfirmationModal');
            }
        },
        handleFilterOrSearchChange: function() {
            this.loadAndRenderTemplates(1); // Reset to page 1 on new filter/search
        },
        renderPagination: function() {
            Utils.renderPaginationControls(
                DOM.templateListPaginationContainer,
                templatesState.pagination,
                (page) => this.loadAndRenderTemplates(page) // Click handler for page numbers
            );
        }
    };

    // --- Template Form Management (Create/Edit) ---
    const TemplateFormManager = {
        resetForm: function() {
            DOM.templateForm.reset();
            DOM.templateFormTitle.textContent = 'Create New Template';
            DOM.templateIdInput.value = ''; // Clear hidden ID
            templatesState.currentEditTemplateId = null;
            templatesState.currentSectionsInForm = [];
            this.renderSectionsUI(); // Clears and shows empty message
            this.populateLanguageTabs(); // Reset language tabs and content
            DOM.formSaveBtn.textContent = 'Save Template';
            // Ensure default values for dropdowns are re-selected if form.reset() doesn't do it
            if (DOM.templateModalitySelect) DOM.templateModalitySelect.value = "";
            if (DOM.templateBodyPartSelect) DOM.templateBodyPartSelect.value = "";
            if (DOM.templateIsActiveCheckbox) DOM.templateIsActiveCheckbox.checked = true;

            console.log("[AdminTemplates] Form reset.");
        },

        populateFormForEdit: function(templateData) {
            this.resetForm();
            DOM.templateFormTitle.textContent = `Edit Template (ID: ${templateData.id})`;
            DOM.templateIdInput.value = templateData.id;
            templatesState.currentEditTemplateId = templateData.id;

            DOM.templateNameInput.value = templateData.name || '';
            DOM.templateModalitySelect.value = templateData.modality || '';
            DOM.templateBodyPartSelect.value = templateData.body_part || ''; // Field name is body_part
            DOM.templateDescriptionTextarea.value = templateData.description || '';
            DOM.templateIsActiveCheckbox.checked = templateData.is_active === true;

            // Sections need to be sorted by order before storing and rendering
            templatesState.currentSectionsInForm = (templateData.sections || [])
                .sort((a, b) => (a.order || 0) - (b.order || 0))
                .map((s, index) => ({ // Ensure each section has a unique temporary UI ID if no DB ID
                    uiId: s.id || `temp_${Date.now()}_${index}`, // Use DB id or generate temp
                    dbId: s.id || null, // Actual database ID
                    title: s.name, // API uses 'name'
                    placeholder: s.placeholder_text, // API uses 'placeholder_text'
                    required: s.is_required,
                    order: s.order || index, // Use existing order or assign based on array index
                    translations: s.translations || {} // Assuming translations might come with section
                }));
            this.renderSectionsUI();
            this.populateLanguageTabs(); // Re-populate based on current sections
            DOM.formSaveBtn.textContent = 'Update Template';
        },

        populateFormForDuplicate: function(templateData) {
            this.populateFormForEdit(templateData); // Start by populating as if editing
            DOM.templateFormTitle.textContent = 'Create New Template (Copy)';
            DOM.templateIdInput.value = ''; // Clear ID for new template
            templatesState.currentEditTemplateId = null;
            DOM.templateNameInput.value = `${templateData.name || 'Untitled'} (Copy)`;
            // Sections from populateFormForEdit are in currentSectionsInForm, but their dbId should be nullified
            templatesState.currentSectionsInForm.forEach(section => {
                section.dbId = null; // This will be a new section in the DB
                section.uiId = `temp_${Date.now()}_${section.order}`; // Ensure new UI ID
            });
            this.renderSectionsUI(); // Re-render with new UI IDs and no DB IDs
            DOM.formSaveBtn.textContent = 'Save Template';
        },

        renderSectionsUI: function() {
            DOM.templateSectionsContainer.innerHTML = ''; // Clear
            if (templatesState.currentSectionsInForm.length === 0) {
                DOM.templateSectionsContainer.innerHTML = '<p class="empty-sections-message">No sections added yet. Click "Add Section" to begin.</p>';
            } else {
                // Ensure sections are sorted by 'order' before rendering
                templatesState.currentSectionsInForm.sort((a,b) => a.order - b.order).forEach((section, index) => {
                    section.order = index; // Re-assign order based on current array position
                    const sectionElement = document.createElement('div');
                    sectionElement.className = 'template-section-item';
                    sectionElement.dataset.uiId = section.uiId; // Use UI ID for DOM manipulation
                    sectionElement.innerHTML = `
                        <div class="section-header">
                            <span class="drag-handle" title="Drag to reorder">⋮⋮</span>
                            <h4>${Utils.escapeHtml(section.title)} ${section.required ? '<span class="required" style="color:red;">*</span>' : ''}</h4>
                            <div class="section-actions">
                                <button type="button" class="section-edit-btn">Edit</button>
                                <button type="button" class="section-remove-btn">Remove</button>
                            </div>
                        </div>
                        <div class="section-content" style="font-size:0.9em; color:#666;">
                            Placeholder: ${Utils.escapeHtml(section.placeholder) || '<em>None</em>'}
                        </div>
                    `;
                    sectionElement.querySelector('.section-edit-btn').addEventListener('click', () => ModalManager.showSectionModal(section.uiId));
                    sectionElement.querySelector('.section-remove-btn').addEventListener('click', () => this.removeSection(section.uiId));
                    DOM.templateSectionsContainer.appendChild(sectionElement);
                });
            }
            this.updateLanguageTranslationPanels(); // Update translation panels based on current sections
            this.makeSectionsSortable();
        },
        
        makeSectionsSortable: function() {
            if (typeof Sortable !== 'undefined' && DOM.templateSectionsContainer) {
                new Sortable(DOM.templateSectionsContainer, {
                    animation: 150,
                    handle: '.drag-handle',
                    onEnd: (evt) => {
                        const itemEl = evt.item; // Dragged item
                        const oldIndex = evt.oldIndex;
                        const newIndex = evt.newIndex;

                        // Update the order in templatesState.currentSectionsInForm
                        const movedItem = templatesState.currentSectionsInForm.splice(oldIndex, 1)[0];
                        templatesState.currentSectionsInForm.splice(newIndex, 0, movedItem);
                        
                        // Re-assign order property based on new array positions
                        templatesState.currentSectionsInForm.forEach((section, index) => {
                            section.order = index;
                        });
                        this.renderSectionsUI(); // Re-render to reflect new order and update UI IDs if necessary
                        console.log("Sections reordered:", templatesState.currentSectionsInForm.map(s => ({title: s.title, order: s.order})));
                    }
                });
            } else {
                // console.warn("SortableJS not loaded or sections container not found. Drag-and-drop reordering disabled.");
            }
        },

        addOrUpdateSection: function(sectionDataFromModal) { // sectionDataFromModal: {title, placeholder, required, uiId (if editing), translations}
            if (sectionDataFromModal.uiId) { // Editing existing section
                const sectionIndex = templatesState.currentSectionsInForm.findIndex(s => s.uiId === sectionDataFromModal.uiId);
                if (sectionIndex > -1) {
                    templatesState.currentSectionsInForm[sectionIndex] = {
                        ...templatesState.currentSectionsInForm[sectionIndex], // Preserve dbId and order
                        title: sectionDataFromModal.title,
                        placeholder: sectionDataFromModal.placeholder,
                        required: sectionDataFromModal.required,
                        translations: sectionDataFromModal.translations || {}
                    };
                }
            } else { // Adding new section
                templatesState.currentSectionsInForm.push({
                    uiId: `temp_${Date.now()}_${templatesState.currentSectionsInForm.length}`,
                    dbId: null,
                    title: sectionDataFromModal.title,
                    placeholder: sectionDataFromModal.placeholder,
                    required: sectionDataFromModal.required,
                    order: templatesState.currentSectionsInForm.length, // Assign next order
                    translations: sectionDataFromModal.translations || {}
                });
            }
            this.renderSectionsUI();
        },

        removeSection: function(sectionUiId) {
            if (!confirm("Are you sure you want to remove this section from the template form?")) return;
            templatesState.currentSectionsInForm = templatesState.currentSectionsInForm.filter(s => s.uiId !== sectionUiId);
            // Re-assign order after removal
            templatesState.currentSectionsInForm.forEach((section, index) => section.order = index);
            this.renderSectionsUI();
        },
        
        populateLanguageTabs: function() {
            if (!DOM.formLanguageTabsContainer || !DOM.languageTranslationsContainer) return;
        
            // Clear existing non-English tabs and content panels
            DOM.formLanguageTabsContainer.querySelectorAll('.language-tab:not([data-lang="en"])').forEach(t => t.remove());
            DOM.languageTranslationsContainer.querySelectorAll('.translation-content:not([data-lang="en"])').forEach(c => c.remove());
        
            templatesState.languages.forEach(lang => {
                if (lang.code === 'en') return; // Skip English, it's the default
        
                const tab = document.createElement('div');
                tab.className = 'language-tab';
                tab.dataset.lang = lang.code;
                tab.textContent = lang.name;
                tab.addEventListener('click', function() {
                    DOM.formLanguageTabsContainer.querySelectorAll('.language-tab').forEach(lt => lt.classList.remove('active'));
                    this.classList.add('active');
                    DOM.languageTranslationsContainer.querySelectorAll('.translation-content').forEach(lc => lc.classList.remove('active'));
                    DOM.languageTranslationsContainer.querySelector(`.translation-content[data-lang="${lang.code}"]`)?.classList.add('active');
                });
                DOM.formLanguageTabsContainer.appendChild(tab);
        
                const contentPanel = document.createElement('div');
                contentPanel.className = 'translation-content';
                contentPanel.dataset.lang = lang.code;
                // Content for this panel will be built by updateLanguageTranslationPanels
                DOM.languageTranslationsContainer.appendChild(contentPanel);
            });
            // Ensure English tab is active by default
            DOM.formLanguageTabsContainer.querySelector('.language-tab[data-lang="en"]')?.classList.add('active');
            DOM.languageTranslationsContainer.querySelector('.translation-content[data-lang="en"]')?.classList.add('active');

            this.updateLanguageTranslationPanels(); // Populate content after tabs are created
        },

        updateLanguageTranslationPanels: function() {
            if (!DOM.languageTranslationsContainer) return;
        
            templatesState.languages.forEach(lang => {
                if (lang.code === 'en') return; // Skip English, translations are for other languages
        
                const panel = DOM.languageTranslationsContainer.querySelector(`.translation-content[data-lang="${lang.code}"]`);
                if (!panel) return;
        
                let panelHTML = `<div class="translation-list">`;
                if (templatesState.currentSectionsInForm.length === 0) {
                    panelHTML += '<p class="empty-translation-message">Add sections in English first, then their translations can be provided here.</p>';
                } else {
                    templatesState.currentSectionsInForm.forEach(section => {
                        const currentTranslation = section.translations && section.translations[lang.code] ? section.translations[lang.code].name : '';
                        // For placeholder translation, you'd add another input: section.translations[lang.code].placeholder_text
                        panelHTML += `
                            <div class="translation-item">
                                <label for="trans_${lang.code}_${section.uiId}_title" class="translation-original">
                                    Section "${Utils.escapeHtml(section.title)}" Title in ${Utils.escapeHtml(lang.name)}:
                                </label>
                                <input type="text" id="trans_${lang.code}_${section.uiId}_title" 
                                       class="form-control section-title-translation"
                                       data-section-ui-id="${section.uiId}" 
                                       data-lang-code="${lang.code}"
                                       value="${Utils.escapeHtml(currentTranslation)}"
                                       placeholder="Translate '${Utils.escapeHtml(section.title)}'">
                            </div>
                        `;
                        // Add similar input for placeholder_text translation if needed
                    });
                }
                panelHTML += `</div>`;
                panel.innerHTML = panelHTML;
            });
        },
        
        gatherTranslationsFromForm: function() {
            const translationsBySectionUiId = {}; // e.g. { "temp_123": { "es": {name:"...", placeholder:"..."}, "fr":{...} } }
        
            DOM.languageTranslationsContainer.querySelectorAll('.section-title-translation').forEach(input => {
                const uiId = input.dataset.sectionUiId;
                const langCode = input.dataset.langCode;
                const translatedTitle = input.value.trim();
        
                if (!translationsBySectionUiId[uiId]) {
                    translationsBySectionUiId[uiId] = {};
                }
                if (!translationsBySectionUiId[uiId][langCode]) {
                    translationsBySectionUiId[uiId][langCode] = {};
                }
                if (translatedTitle) { // Only store if a translation is provided
                    translationsBySectionUiId[uiId][langCode].name = translatedTitle;
                }
                // Add logic for placeholder translations if you have inputs for them
            });
            return translationsBySectionUiId;
        },

        prepareSavePayload: function() {
            const name = DOM.templateNameInput.value.trim();
            const modality = DOM.templateModalitySelect.value;
            const body_part = DOM.templateBodyPartSelect.value; // HTML name is body_part
            const description = DOM.templateDescriptionTextarea.value.trim();
            const is_active = DOM.templateIsActiveCheckbox.checked;

            if (!name || !modality || !body_part) {
                showToast('Template Name, Modality, and Body Part/Region are required.', 'error');
                return null;
            }
            if (templatesState.currentSectionsInForm.length === 0) {
                showToast('At least one section is required for the template.', 'error');
                return null;
            }
            
            const translationsFromForm = this.gatherTranslationsFromForm();

            const sectionsForAPI = templatesState.currentSectionsInForm.map(section => {
                // For the API, we need to structure translations as expected by backend if it supports it.
                // The project doc doesn't specify how MasterTemplateSection translations are stored/sent.
                // Assuming for now the backend handles translations separately or not at all for MasterTemplateSection.
                // If it does, this is where you'd format section.translations based on translationsFromForm.
                return {
                    id: section.dbId, // Send existing DB ID for updates, null/undefined for new
                    name: section.title,
                    placeholder_text: section.placeholder,
                    is_required: section.required,
                    order: section.order
                    // translations: section.translations // Or formatted translations
                };
            });
            
            // Validate section titles
            for (let i = 0; i < sectionsForAPI.length; i++) {
                if (!sectionsForAPI[i].name || sectionsForAPI[i].name.trim() === "") {
                    showToast(`Section at order ${sectionsForAPI[i].order + 1} has an empty title.`, 'error');
                    return null;
                }
            }

            return { name, modality, body_part, description, is_active, sections: sectionsForAPI };
        },

        handleSubmit: async function(event) {
            event.preventDefault();
            const payload = TemplateFormManager.prepareSavePayload();
            if (!payload) return;

            const isEditMode = !!templatesState.currentEditTemplateId;
            const actionText = isEditMode ? 'Updating' : 'Creating';
            showLoading(true, `${actionText} template...`);

            try {
                let response;
                if (isEditMode) {
                    response = await templatesApi.updateTemplate(templatesState.currentEditTemplateId, payload);
                } else {
                    response = await templatesApi.createTemplate(payload);
                }
                showToast(`Master Template ${actionText.toLowerCase().replace(/ing$/, 'ed')} successfully!`, 'success');
                TemplateFormManager.resetForm();
                switchTab('template-list'); // Switch to list and it will auto-refresh
            } catch (error) {
                console.error(`[AdminTemplates] Error saving template:`, error);
                let errorMsg = Utils.formatApiError(error);
                showToast(`Error: ${errorMsg}`, 'error', 5000); // Longer toast for detailed errors
            } finally {
                showLoading(false);
            }
        },
        handlePreview: function() {
            const formData = TemplateFormManager.prepareSavePayload(); // Get current form data
            if (!formData) {
                showToast("Please fill in required fields before previewing.", "warning");
                return;
            }
            // Simulate a template object for preview
            const templateToPreview = {
                name: formData.name,
                modality: formData.modality,
                body_part: formData.body_part, // Ensure this matches what generateMasterTemplatePreviewHTML expects
                description: formData.description,
                sections: formData.sections.map(s => ({ // Map to structure expected by preview
                    name: s.name, 
                    placeholder_text: s.placeholder_text, 
                    is_required: s.is_required,
                    order: s.order
                }))
            };
            ModalManager.showPreviewModal(templateToPreview);
        }
    };

    // --- Modal Management ---
    const ModalManager = {
        showSectionModal: function(sectionUiIdToEdit = null) {
            templatesState.currentEditSectionData = null; // Reset
            DOM.sectionModalEditIndex.value = ''; // For older logic if any, prefer uiId

            if (sectionUiIdToEdit) { // Editing existing section from the form
                const section = templatesState.currentSectionsInForm.find(s => s.uiId === sectionUiIdToEdit);
                if (section) {
                    templatesState.currentEditSectionData = {...section}; // Store a copy for editing
                    DOM.sectionModalTitle.textContent = 'Edit Section';
                    DOM.saveSectionBtn.textContent = 'Update Section';
                    DOM.sectionTitleInput.value = section.title;
                    DOM.sectionPlaceholderInput.value = section.placeholder;
                    DOM.sectionRequiredCheckbox.checked = section.required;
                    // TODO: Populate translation fields in modal if they exist
                } else {
                    showToast("Error: Could not find section to edit.", "error"); return;
                }
            } else { // Adding new section
                DOM.sectionModalTitle.textContent = 'Add New Section';
                DOM.saveSectionBtn.textContent = 'Add Section';
                DOM.sectionTitleInput.value = '';
                DOM.sectionPlaceholderInput.value = '';
                DOM.sectionRequiredCheckbox.checked = true;
                // TODO: Clear translation fields in modal
            }
            this.openModal('sectionModal');
            DOM.sectionTitleInput.focus();
        },

        handleSaveSection: function() {
            const title = DOM.sectionTitleInput.value.trim();
            if (!title) {
                showToast('Section title is required.', 'error'); DOM.sectionTitleInput.focus(); return;
            }
            const sectionData = {
                title: title,
                placeholder: DOM.sectionPlaceholderInput.value.trim(),
                required: DOM.sectionRequiredCheckbox.checked,
                uiId: templatesState.currentEditSectionData?.uiId, // Pass uiId if editing
                translations: templatesState.currentEditSectionData?.translations || {} // Preserve existing translations
                // TODO: Gather translations from modal inputs if any
            };
            TemplateFormManager.addOrUpdateSection(sectionData);
            this.closeModal('sectionModal');
        },
        
        showPreviewModalById: async function(templateId) { // For list view preview
            showLoading(true, 'Loading template preview...');
            try {
                const template = await templatesApi.getTemplateById(templateId);
                this.showPreviewModal(template); // Use the common previewer
            } catch (e) { showToast(`Error loading preview: ${e.message}`, "error"); }
            finally { showLoading(false); }
        },

        showPreviewModal: function(templateData) { // Common previewer for form and list
            if (!DOM.templatePreviewContainer || !DOM.templatePreviewModal) return;
            DOM.templatePreviewContainer.innerHTML = Utils.generateMasterTemplatePreviewHTML(templateData);
            this.openModal('templatePreviewModal');
        },

        showDeleteConfirmModal: function(templateId) {
            if (!DOM.deleteConfirmationModal) return;
            DOM.deleteConfirmationModal.dataset.templateId = templateId;
            DOM.deleteConfirmMessage.textContent = `Are you sure you want to delete Master Template ID ${templateId}? This action cannot be undone.`;
            this.openModal('deleteConfirmationModal');
        },
        
        openModal: function(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) modal.style.display = 'flex'; // Assuming modals use flex for centering
        },
        closeModal: function(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) modal.style.display = 'none';
        },
        closeAllModals: function() {
            document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
        }
    };
    
    // --- Global Utilities (already in admin.js, but can be scoped here too) ---
    function showLoading(isLoading, message = 'Loading...') {
        // Use global if available and not this one
        if (window.showLoading && window.showLoading !== showLoading) {
            window.showLoading(isLoading, message); return;
        }
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.querySelector('.loading-message').textContent = message;
            overlay.style.display = isLoading ? 'flex' : 'none';
        }
    }

    function showToast(message, type = 'info', duration = 3000) {
        if (window.showToast && window.showToast !== showToast) {
             window.showToast(message, type, duration); return;
        }
        const container = document.getElementById('toastContainer');
        if (!container) { console.warn("Toast container not found."); alert(`Toast (${type}): ${message}`); return; }
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), duration);
    }
    
    Utils.formatApiError = function(error) { // Helper to parse DRF errors
        if (!error) return "An unknown error occurred.";
        if (error.message && !error.data) return error.message; // Network error or simple JS error
        if (error.data) {
            if (typeof error.data.detail === 'string') return error.data.detail;
            if (Array.isArray(error.data)) return error.data.join('; ');
            if (typeof error.data === 'object') {
                return Object.entries(error.data)
                    .map(([key, value]) => {
                        let valStr = Array.isArray(value) ? value.join(', ') : String(value);
                        if (key === 'sections' && Array.isArray(value) && value.length > 0 && typeof value[0] === 'object') {
                            // Handle nested section errors
                            valStr = value.map((sectionErr, index) => {
                                let secMessages = [];
                                for (const secKey in sectionErr) {
                                    secMessages.push(`${secKey}: ${sectionErr[secKey].join(', ')}`);
                                }
                                return `Section ${index + 1}: ${secMessages.join('; ')}`;
                            }).join(' | ');
                        }
                        return `${key}: ${valStr}`;
                    })
                    .join('; ');
            }
        }
        return error.message || "An unexpected error occurred.";
    };

    Utils.renderPaginationControls = function(container, paginationState, onPageClick) {
        if (!container) return;
        container.innerHTML = ''; // Clear existing
    
        if (!paginationState || paginationState.totalPages <= 1) {
            container.style.display = 'none';
            return;
        }
        container.style.display = 'flex';
    
        const createButton = (text, page, isDisabled, isCurrent = false) => {
            const btn = document.createElement('button');
            if (isCurrent) {
                btn.className = 'pagination-page active';
                btn.disabled = true;
            } else {
                btn.className = page ? 'pagination-page' : 'pagination-btn';
                btn.disabled = isDisabled;
            }
            btn.textContent = text;
            if (page && !isDisabled && !isCurrent) {
                btn.addEventListener('click', () => onPageClick(page));
            }
            return btn;
        };
    
        // Previous Button
        container.appendChild(createButton('Previous', paginationState.currentPage - 1, !paginationState.prevUrl));
    
        // Page Numbers (simplified: show current, +/- 1, first, last)
        const pagesToShow = new Set();
        pagesToShow.add(1);
        pagesToShow.add(paginationState.totalPages);
        pagesToShow.add(paginationState.currentPage);
        if (paginationState.currentPage > 1) pagesToShow.add(paginationState.currentPage - 1);
        if (paginationState.currentPage < paginationState.totalPages) pagesToShow.add(paginationState.currentPage + 1);
    
        const sortedPages = Array.from(pagesToShow).sort((a,b) => a-b);
        
        let lastPageAdded = 0;
        sortedPages.forEach(pageNum => {
            if (pageNum > 0 && pageNum <= paginationState.totalPages) {
                if (pageNum > lastPageAdded + 1 && lastPageAdded !== 0) { // Add ellipsis if gap
                    const ellipsis = document.createElement('span');
                    ellipsis.className = 'pagination-ellipsis';
                    ellipsis.textContent = '...';
                    container.appendChild(ellipsis);
                }
                container.appendChild(createButton(pageNum, pageNum, false, pageNum === paginationState.currentPage));
                lastPageAdded = pageNum;
            }
        });
         if (lastPageAdded < paginationState.totalPages && !sortedPages.includes(paginationState.totalPages)) {
            if (paginationState.totalPages > lastPageAdded + 1) {
                 const ellipsis = document.createElement('span');
                 ellipsis.className = 'pagination-ellipsis';
                 ellipsis.textContent = '...';
                 container.appendChild(ellipsis);
            }
            container.appendChild(createButton(paginationState.totalPages, paginationState.totalPages, false, paginationState.totalPages === paginationState.currentPage));
        }
    
        // Next Button
        container.appendChild(createButton('Next', paginationState.currentPage + 1, !paginationState.nextUrl));
    };
    
    Utils.generateMasterTemplatePreviewHTML = function(template) { // For preview modal
        let sectionsHtml = '<h6>Sections:</h6>';
        if (template.sections && template.sections.length > 0) {
            const sortedSections = [...template.sections].sort((a, b) => (a.order || 0) - (b.order || 0));
            sectionsHtml += '<ul style="list-style:none; padding-left:0;">';
            sortedSections.forEach(section => {
                sectionsHtml += `<li style="padding: 5px 0; border-bottom: 1px solid #eee;">
                    <strong>${Utils.escapeHtml(section.name || section.title)}</strong> 
                    ${section.is_required || section.required ? '<span style="color:green; font-size:0.9em;">(Required)</span>' : ''}
                    <br><small style="color:#777;">Placeholder: ${Utils.escapeHtml(section.placeholder_text || section.placeholder) || '<em>None</em>'}</small>
                </li>`;
            });
            sectionsHtml += '</ul>';
        } else {
            sectionsHtml += '<p><em>No sections defined for this template.</em></p>';
        }
        return `
            <h4>${Utils.escapeHtml(template.name)}</h4>
            <p>
                <strong>Modality:</strong> ${Utils.escapeHtml(template.modality_display || template.modality)} | 
                <strong>Body Part:</strong> ${Utils.escapeHtml(template.body_part_display || template.body_part)}
            </p>
            <p><strong>Description:</strong> ${Utils.escapeHtml(template.description) || '<em>No description.</em>'}</p>
            <hr>
            ${sectionsHtml}
        `;
    };


})(); // End of IIFE
