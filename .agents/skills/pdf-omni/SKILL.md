---
name: pdf-omni
description: "Process PDF files with full text extraction, OCR, and image analysis. Automatically switches to Nemotron 3 Nano Omni model for PDF/image processing. Supports text extraction, table parsing, form filling, OCR on scanned documents, and image analysis within PDFs."
allowed-tools: Bash(belt *), Python
---

# PDF-Omni Skill - Full PDF & Image Processing

## Model Switching Protocol

**CRITICAL**: When handling PDF or image files, ALWAYS switch to **Nemotron 3 Nano Omni** model for full multimodal capabilities.

### When to Switch Models
- PDF file upload detected
- Image file upload detected (.png, .jpg, .jpeg, .gif, .webp, .tiff)
- Scanned document processing
- Any file requiring OCR or visual analysis

### How to Switch
```
/model nemotron-3-nano-omni
```

## PDF Processing Capabilities

### Text Extraction
```python
from pypdf import PdfReader
import pdfplumber

# Basic text extraction
reader = PdfReader("document.pdf")
text = ""
for page in reader.pages:
    text += page.extract_text() + "\n"

# Advanced extraction with layout preservation
with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text(layout=True)
```

### Table Extraction
```python
import pdfplumber
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)
    
    if all_tables:
        combined = pd.concat(all_tables, ignore_index=True)
```

### OCR for Scanned PDFs
```python
import pytesseract
from pdf2image import convert_from_path

def ocr_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""
    for i, image in enumerate(images):
        text += f"--- Page {i+1} ---\n"
        text += pytesseract.image_to_string(image) + "\n"
    return text
```

### Image Extraction from PDFs
```python
from pdf2image import convert_from_path

images = convert_from_path("document.pdf")
for i, image in enumerate(images):
    image.save(f"page_{i+1}.jpg", "JPEG")
```

## Agent Configuration

### For All Agents (Orchestrator, Debugger, Architect, etc.)

Add this to each agent's system prompt or SOUL.md:

```markdown
## PDF/Image Processing Protocol

When a PDF or image file is uploaded:
1. IMMEDIATELY switch to Nemotron 3 Nano Omni model
2. Use the pdf-omni skill for processing
3. Extract all text, tables, and images
4. Return structured data with page references

Model switch command: `/model nemotron-3-nano-omni`
```

### Orchestrator Agent Update
Add to `.agents/orchestrator.agent.md`:

```markdown
### PDF/Image Handling
- Detect PDF/image uploads in user messages
- Auto-switch to Nemotron 3 Nano Omni for multimodal processing
- Delegate to pdf-omni skill for extraction
- Aggregate results from multiple documents
```

### Memory Engineer Update
Add to `.agents/memory-engineer.agent.md`:

```markdown
### Document Processing
- Store extracted PDF content in Tier 2 (SQLite FTS5)
- Index tables and key information for retrieval
- Maintain source references (page numbers, document names)
```

## Quick Commands

```bash
# Extract text from PDF
belt app run infsh/pdf-extractor --input '{"file": "doc.pdf"}'

# OCR scanned PDF
belt app run infsh/ocr-processor --input '{"file": "scanned.pdf"}'

# Extract tables to CSV
belt app run infsh/table-extractor --input '{"file": "report.pdf", "format": "csv"}'
```

## File Type Support

| Format | Text | Tables | Images | OCR |
|--------|------|--------|--------|-----|
| PDF | ✅ | ✅ | ✅ | ✅ |
| PNG | ✅ | ✅ | ✅ | ✅ |
| JPG | ✅ | ✅ | ✅ | ✅ |
| JPEG | ✅ | ✅ | ✅ | ✅ |
| GIF | ✅ | ✅ | ✅ | ✅ |
| WEBP | ✅ | ✅ | ✅ | ✅ |
| TIFF | ✅ | ✅ | ✅ | ✅ |

## Error Handling

- **Password protected**: Use `reader.decrypt(password)`
- **Corrupted PDF**: Try `pdfplumber` as fallback
- **Scanned only**: Auto-trigger OCR
- **Large files**: Process in chunks

## Integration with Existing Skills

This skill works alongside:
- `python-executor` - For custom processing scripts
- `pandas-pro` - For table analysis
- `research-agent` - For document research workflows