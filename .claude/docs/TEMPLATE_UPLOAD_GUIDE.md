# 📄 Template File Upload Guide

## 🎯 Overview

The Template File Upload feature allows admins to quickly populate expert report sections by uploading pre-written template .txt files. This eliminates tedious copy/paste and reduces case creation time from **30-45 minutes to 5-10 minutes**.

---

## ✅ What This Feature Does

**Before (Manual):**
1. Open template .txt file
2. Copy "Liver:" section
3. Switch to browser
4. Paste into Liver textarea
5. Repeat for 8+ sections
6. Manually type key concepts with semicolons

**After (Automated):**
1. Click "Choose File"
2. Select template .txt file
3. Click "Parse & Fill Sections"
4. All sections auto-populated!
5. Key concepts auto-extracted!
6. Quick edits for this specific case
7. Save

**Time Saved: 20-30 minutes per case (80% reduction!)**

---

## 📋 How to Use

### Step 1: Create a Case with Master Template

1. Go to **Admin Dashboard** → **Add/Edit Case**
2. Fill in basic case info (title, subspecialty, modality, etc.)
3. Select a **Master Report Template** (e.g., "Abdomen US Template")
4. Save the case as a draft

### Step 2: Add Language Version

1. Scroll to **Expert-Filled Template Languages** section
2. Click **"+ Add Language Version"**
3. Select language (e.g., English)
4. Click **"Edit Content"** button

### Step 3: Upload Template File

1. You'll see a **blue box** at the top with upload controls:
   ```
   🚀 Quick Start: Upload Template File
   [Choose File] [📄 Parse & Fill Sections]
   ```
2. Click **"Choose File"** and select your .txt template
3. Click **"📄 Parse & Fill Sections"**
4. Watch the magic happen! ✨

### Step 4: Review and Edit

- Sections will **flash green** when populated
- Key concepts (if any) will **flash yellow** when auto-extracted
- Toast notification: "✅ Auto-populated 8 section(s) from template!"
- Edit any sections to match THIS specific case
- Click **"Save English Content"**

---

## 📝 Template File Format

### Required Structure

Your .txt template file MUST have:

1. **FINDINGS:** header (anything before this is ignored)
2. **Anatomical subsections** under FINDINGS (e.g., `Liver:`, `Spleen:`)
3. **IMPRESSION:** header at the end

### Example Template File

```
CLINICAL HISTORY:
[This section is ignored]

TECHNIQUE:
[This section is also ignored]

FINDINGS:

Liver: The liver is normal in size, contour, signal and enhancement pattern. There is no focal liver lesion. There is no fatty infiltration.

Biliary: No intra or extrahepatic biliary ductal dilation. Normal fluid filled gallbladder, without stones.

Spleen: Homogeneous signal, with normal enhancement pattern. No splenomegaly.

Pancreas: Normal in size, signal and enhancement pattern. No pancreatic duct dilatation.

Kidneys: Both kidneys are normal in size and echotexture. No solid masses or calculi. No urinary tract dilatation.

Vessels: Normal course and caliber.

IMPRESSION:
Normal abdominal ultrasound.
```

### What Gets Parsed:

✅ **Parsed** (used to populate textareas):
- `Liver:` → Liver textarea
- `Biliary:` → Biliary textarea
- `Spleen:` → Spleen textarea
- `Pancreas:` → Pancreas textarea
- `Kidneys:` → Kidneys textarea
- `Vessels:` → Vessels textarea
- `IMPRESSION:` → Impression textarea

❌ **Ignored** (skipped):
- `CLINICAL HISTORY:` (before FINDINGS)
- `TECHNIQUE:` (before FINDINGS)

---

## 🔍 Fuzzy Matching

The parser uses intelligent fuzzy matching to handle variations:

| Template File | Master Template Section | ✅ Match? |
|---------------|-------------------------|-----------|
| `Liver:` | `Liver` | ✅ Yes |
| `Biliary:` | `Biliary System` | ✅ Yes |
| `Kidneys:` | `Kidney` | ✅ Yes |
| `Vessels:` | `Vasculature` | ✅ Yes |
| `Soft Tissues:` | `Soft Tissue` | ✅ Yes |

**Case-insensitive and handles plurals/variations automatically!**

---

## 🤖 Auto-Generated Key Concepts

The parser can automatically extract key concepts from your findings text.

**Example:**

**Input (Findings text):**
```
Liver: 4.3 cm hemorrhagic mass with associated caliectasis.
No lymphadenopathy.
```

**Auto-extracted Key Concepts:**
```
liver;measurements present;mass;hemorrhage
```

**You can edit these or leave empty if not needed.**

---

## ⚠️ Troubleshooting

### Error: "Could not find FINDINGS: section"

**Cause**: Your template doesn't have a line that says `FINDINGS:` (case-insensitive)

**Fix**: Add a line with exactly `FINDINGS:` before your anatomical sections

### Error: "Could not find IMPRESSION: section"

**Cause**: Your template doesn't have a line that says `IMPRESSION:`

**Fix**: Add a line with exactly `IMPRESSION:` at the end

### Warning: "No matching sections found"

**Cause**: Section names in your .txt file don't match Master Template section names

**Example Problem:**
- Template file has: `Hepatobiliary:`
- Master Template has: `Liver`
- **Not matched** (fuzzy matching has limits)

**Fix**: Either:
1. Rename sections in your .txt file to match Master Template exactly, OR
2. Manually copy/paste content for unmatched sections

### Some sections not populated

**Expected behavior!** The parser only populates sections it can match.

**Example:**
- Your Master Template has: `Liver`, `Spleen`, `Pancreas`, `Adrenals`
- Your .txt file has: `Liver:`, `Spleen:`, `Pancreas:`
- **Result**: Liver, Spleen, Pancreas auto-filled; Adrenals stays empty (you type manually)

---

## 💡 Tips & Best Practices

### 1. Create Reusable Templates

Save your common template files:
```
templates/
├── abdomen_us_template.txt
├── brain_mri_template.txt
├── chest_xray_template.txt
└── knee_mri_template.txt
```

### 2. Use Consistent Section Names

Make sure your Master Template section names match your .txt file section names as closely as possible.

**Good Example:**
- Master Template: `Liver`, `Biliary`, `Spleen`
- Template File: `Liver:`, `Biliary:`, `Spleen:`
- **Perfect match!**

**Bad Example:**
- Master Template: `Hepatic System`, `Renal System`
- Template File: `Liver:`, `Kidneys:`
- **Won't match** (too different)

### 3. Keep Templates Clean

- Remove patient-specific info before saving as template
- Use generic phrases like "normal" or "visualized portions are normal"
- Update templates when you find better wording

### 4. Test Your Templates

Before creating 20 cases:
1. Upload your template file once
2. Check which sections get populated
3. Adjust section names if needed
4. Save the working template for reuse

---

## 📊 Supported Template Formats

### ✅ Supported

- `.txt` files (plain text)
- UTF-8 encoding
- Windows line endings (`\r\n`)
- Unix line endings (`\n`)
- Subsections with inline content: `Liver: Normal.`
- Subsections with content on next line:
  ```
  Liver:
  The liver is normal.
  ```

### ❌ Not Supported (Yet)

- `.doc` or `.docx` files (Word documents) - **Save as .txt first**
- `.pdf` files
- Rich formatting (bold, italic, etc.) - all formatting is stripped
- Tables or complex layouts

---

## 🔧 Technical Details

### Parsing Logic

1. **Ignore Pre-FINDINGS Content**: Everything before `FINDINGS:` is skipped
2. **Detect FINDINGS Header**: Finds line matching `/^FINDINGS:?\s*$/i`
3. **Extract Subsections**: Detects lines matching `/^([A-Z][A-Za-z\s/]+):\s*(.*)$/`
4. **Collect Content**: Groups text under each subsection until next subsection
5. **Detect IMPRESSION Header**: Finds line matching `/^IMPRESSION:?\s*$/i`
6. **Extract Impression Content**: Everything after IMPRESSION header
7. **Fuzzy Match**: Matches parsed sections to Master Template sections
8. **Populate Textareas**: Fills in matched sections with content

### NO AI API Costs!

This feature uses **pure JavaScript rule-based parsing**. No AI API calls, no additional costs!

---

## 🐛 Known Limitations

1. **Case-Sensitive Matching**: Section names are somewhat flexible but very different names won't match
2. **Single Level Only**: Nested subsections (e.g., `Liver → Right Lobe`) not supported
3. **Plain Text Only**: Must be .txt format (convert Word docs to .txt first)
4. **No Multi-Language Support**: Parser expects English section headers

---

## 📞 Need Help?

If you encounter issues:

1. **Check template format**: Make sure you have `FINDINGS:` and `IMPRESSION:` headers
2. **View browser console**: Open DevTools (F12) and check for error messages
3. **Check section names**: Ensure template file sections roughly match Master Template
4. **Manual fallback**: You can always type content manually if parser fails

---

## 🔄 Version History

**v1.0 (2025-01-12)**:
- Initial release
- Supports .txt file parsing
- Fuzzy section matching
- Auto key concept extraction
- Visual feedback (green/yellow flashes)

---

## 🎓 Example Walkthrough

Let's say you want to create 10 Abdomen US cases:

### Old Way (300-450 minutes total):
1. Create case #1
2. Copy/paste 8 sections manually (30-45 min)
3. Repeat 10 times
4. **Total: 300-450 minutes (5-7.5 hours!)**

### New Way (50-100 minutes total):
1. Create `abdomen_us_template.txt` once
2. For each case:
   - Create case with Master Template
   - Add English version
   - Upload `abdomen_us_template.txt`
   - Click "Parse & Fill"
   - Edit specific findings (5-10 min)
   - Save
3. **Total: 50-100 minutes (1-1.5 hours!)**

**Time Saved: 4-6 hours for 10 cases!**

---

**Happy case creating! 🚀**
