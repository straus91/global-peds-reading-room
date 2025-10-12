// frontend/js/template-parser.js
/**
 * Template Parser for Expert Report Templates
 * Parses radiology report template text files and extracts sections
 * NO AI API calls - pure rule-based logic
 */

class TemplateParser {
    constructor() {
        // Common radiology section headers to ignore (before FINDINGS)
        this.ignoredSections = [
            /^(CLINICAL\s+HISTORY|INDICATION|REASON\s+FOR\s+EXAM):?\s*$/im,
            /^(TECHNIQUE|PROTOCOL|METHOD):?\s*$/im,
            /^(COMPARISON|PRIOR\s+STUDIES?):?\s*$/im,
        ];

        // Main section headers
        this.findingsPattern = /^FINDINGS:?\s*$/im;
        this.impressionPattern = /^IMPRESSION:?\s*$/im;

        // Subsection patterns (anatomical sections under FINDINGS)
        // Matches patterns like "Liver:", "LIVER:", "Liver :", etc.
        this.subsectionPattern = /^([A-Z][A-Za-z\s/]+):\s*(.*)$/;
    }

    /**
     * Parse template text into section objects
     * @param {string} templateText - Raw text from uploaded file
     * @returns {Array} - [{sectionName: 'Liver', content: '...'}, ...]
     */
    parseTemplate(templateText) {
        if (!templateText || typeof templateText !== 'string') {
            throw new Error('Invalid template text');
        }

        console.log('[TemplateParser] Starting parse...');

        // Find where FINDINGS: starts
        const findingsMatch = templateText.match(this.findingsPattern);
        if (!findingsMatch) {
            throw new Error('Could not find "FINDINGS:" section in template. Make sure your template includes a FINDINGS: header.');
        }

        const findingsStartIndex = findingsMatch.index + findingsMatch[0].length;

        // Find where IMPRESSION: starts
        const impressionMatch = templateText.match(this.impressionPattern);
        if (!impressionMatch) {
            throw new Error('Could not find "IMPRESSION:" section in template. Make sure your template includes an IMPRESSION: header.');
        }

        const impressionStartIndex = impressionMatch.index;

        // Extract FINDINGS section text (between FINDINGS: and IMPRESSION:)
        const findingsText = templateText.substring(findingsStartIndex, impressionStartIndex).trim();

        // Extract IMPRESSION section text (everything after IMPRESSION:)
        const impressionText = templateText.substring(impressionMatch.index + impressionMatch[0].length).trim();

        console.log('[TemplateParser] Findings text length:', findingsText.length);
        console.log('[TemplateParser] Impression text length:', impressionText.length);

        // Parse anatomical subsections from FINDINGS
        const sections = this.parseFindingsSubsections(findingsText);

        // Add IMPRESSION section
        sections.push({
            sectionName: 'Impression',
            content: impressionText
        });

        console.log('[TemplateParser] Parsed sections:', sections.map(s => s.sectionName));

        return sections;
    }

    /**
     * Parse anatomical subsections from FINDINGS text
     * @param {string} findingsText - Text between FINDINGS: and IMPRESSION:
     * @returns {Array} - [{sectionName: 'Liver', content: '...'}, ...]
     */
    parseFindingsSubsections(findingsText) {
        const lines = findingsText.split('\n');
        const sections = [];
        let currentSection = null;
        let currentContent = [];

        for (let line of lines) {
            const trimmedLine = line.trim();

            // Skip empty lines
            if (trimmedLine === '') {
                continue;
            }

            // Check if line is a subsection header
            const subsectionMatch = trimmedLine.match(this.subsectionPattern);

            if (subsectionMatch) {
                // Save previous section if exists
                if (currentSection) {
                    sections.push({
                        sectionName: currentSection,
                        content: currentContent.join('\n').trim()
                    });
                }

                // Start new section
                currentSection = subsectionMatch[1].trim();

                // Some lines have content after the colon (e.g., "Liver: Normal.")
                const inlineContent = subsectionMatch[2].trim();
                currentContent = inlineContent ? [inlineContent] : [];

            } else if (currentSection) {
                // Add line to current section content
                currentContent.push(trimmedLine);
            }
            // If no currentSection yet, skip the line (shouldn't happen if FINDINGS: is clean)
        }

        // Save last section
        if (currentSection) {
            sections.push({
                sectionName: currentSection,
                content: currentContent.join('\n').trim()
            });
        }

        return sections;
    }

    /**
     * Fuzzy match parsed section name to master template section name
     * @param {string} parsedSectionName - e.g., "Liver" from template file
     * @param {string} masterSectionName - e.g., "Liver" or "Liver System" from Master Template
     * @returns {boolean}
     */
    fuzzyMatch(parsedSectionName, masterSectionName) {
        const normalize = (str) => str.toLowerCase()
            .replace(/[^a-z0-9]/g, '') // Remove all non-alphanumeric
            .trim();

        const parsedNorm = normalize(parsedSectionName);
        const masterNorm = normalize(masterSectionName);

        // Exact match
        if (parsedNorm === masterNorm) {
            return true;
        }

        // Partial match (e.g., "liver" in "liversystem" or vice versa)
        if (masterNorm.includes(parsedNorm) || parsedNorm.includes(masterNorm)) {
            return true;
        }

        // Special cases
        const specialMatches = {
            'biliary': ['biliarysystem', 'bile', 'gallbladder', 'biliarytree'],
            'kidneys': ['kidney', 'renal'],
            'vessels': ['vessel', 'vasculature', 'aorta', 'ivc'],
            'bones': ['bone', 'osseous', 'skeleton'],
            'softtissues': ['softtissue', 'tissue'],
            'lymphnodes': ['lymphnode', 'nodes'],
        };

        for (let [key, aliases] of Object.entries(specialMatches)) {
            if (parsedNorm.includes(key) || key.includes(parsedNorm)) {
                if (aliases.some(alias => masterNorm.includes(alias) || alias.includes(masterNorm))) {
                    return true;
                }
            }
        }

        return false;
    }

    /**
     * Extract key concepts from findings text (simple heuristic)
     * Useful for auto-generating key_concepts_text field
     * @param {string} findingsText
     * @returns {string} - Semicolon-separated key phrases
     */
    extractKeyConceptsFromText(findingsText) {
        if (!findingsText || findingsText.trim().length === 0) {
            return '';
        }

        const concepts = [];

        // Strategy 1: Extract organ names mentioned
        const organs = ['liver', 'spleen', 'pancreas', 'kidney', 'gallbladder', 'heart', 'lung', 'aorta'];
        for (let organ of organs) {
            const regex = new RegExp(`\\b${organ}[s]?\\b`, 'gi');
            if (regex.test(findingsText)) {
                // Check for "normal" or "abnormal" context
                const normalRegex = new RegExp(`${organ}[s]?[^.]*?normal`, 'gi');
                if (normalRegex.test(findingsText)) {
                    concepts.push(`${organ} normal`);
                } else {
                    concepts.push(organ);
                }
            }
        }

        // Strategy 2: Extract measurements (e.g., "3.2 cm", "10 mm")
        const measurementRegex = /\d+\.?\d*\s*(cm|mm|x)/gi;
        const measurements = findingsText.match(measurementRegex);
        if (measurements && measurements.length > 0) {
            concepts.push('measurements present');
        }

        // Strategy 3: Look for pathology keywords
        const pathologyKeywords = [
            'mass', 'lesion', 'nodule', 'cyst', 'tumor', 'fracture', 'effusion',
            'hemorrhage', 'edema', 'inflammation', 'abscess', 'stone', 'calcification'
        ];
        for (let keyword of pathologyKeywords) {
            const regex = new RegExp(`\\b${keyword}[s]?\\b`, 'gi');
            if (regex.test(findingsText)) {
                concepts.push(keyword);
            }
        }

        // Remove duplicates and return
        const uniqueConcepts = [...new Set(concepts)];
        return uniqueConcepts.slice(0, 10).join(';'); // Limit to 10 concepts
    }

    /**
     * Validate template file structure before parsing
     * @param {string} templateText
     * @returns {Object} - {valid: boolean, errors: []}
     */
    validateTemplate(templateText) {
        const errors = [];

        if (!templateText || templateText.trim().length === 0) {
            errors.push('Template file is empty');
            return { valid: false, errors };
        }

        // Check for FINDINGS section
        if (!this.findingsPattern.test(templateText)) {
            errors.push('Missing "FINDINGS:" section header');
        }

        // Check for IMPRESSION section
        if (!this.impressionPattern.test(templateText)) {
            errors.push('Missing "IMPRESSION:" section header');
        }

        // Check for at least one anatomical subsection
        const hasSubsections = templateText.split('\n').some(line => {
            const trimmed = line.trim();
            return this.subsectionPattern.test(trimmed) &&
                   !this.findingsPattern.test(trimmed) &&
                   !this.impressionPattern.test(trimmed);
        });

        if (!hasSubsections) {
            errors.push('No anatomical subsections found under FINDINGS (e.g., "Liver:", "Spleen:")');
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }
}

// Export for use in admin-case-edit.js
window.TemplateParser = TemplateParser;

console.log('[TemplateParser] Template parser loaded and ready.');
