# Domain-Driven Design: Invoice Automation System

## Core Domain Problem
BuilderTrend needs to automate subcontractor invoice processing to drive payment feature adoption and revenue. Invoice formats vary wildly across small contracting businesses, requiring robust extraction and classification.

## Demo Strategy: Evolution Comparison
Show BuilderTrend three approaches to prove technical depth and business thinking:
1. **Traditional OCR (Baseline)** - Shows understanding of legacy systems
2. **Vision-Native AI (Modern)** - Shows state-of-the-art capabilities
3. **Full Pipeline** - Shows production-ready system design

## Bounded Contexts

### 1. Invoice Ingestion
**Responsibility**: Receive and store raw invoice documents
**Entities**:
- Invoice Document (PDF/Image)
- Upload Metadata (timestamp, source, builder_id)
  **Implementation**: File storage with metadata tracking

### 2. Document Intelligence (Multi-Strategy)
**Responsibility**: Extract structured data from unstructured invoices
**Entities**:
- Raw OCR Output (text, confidence scores, bounding boxes)
- Extracted Fields (vendor, amount, date, line items)
- Processing Method (traditional/vision-native)
  **Services**:
- **Traditional Path**: Tesseract OCR → Regex/Rule parsing
- **Vision Path**: Qwen2-VL direct image → JSON extraction
  **Design Pattern**: Strategy Pattern - swap extraction implementations

### 3. Entity Resolution
**Responsibility**: Match extracted vendor name to known subcontractors in builder's database
**Entities**:
- Subcontractor Profile (name, variations, contact)
- Match Candidate (similarity score, matched_id)
  **Services**:
- Fuzzy String Matcher using RapidFuzz (Levenshtein distance)
- Handles typos, abbreviations, name variations
  **Example**: "ABC Plumbing LLC" matches "A.B.C. Plumbing" at 92% similarity

### 4. Cost Code Classification
**Responsibility**: Assign invoice line items to builder's custom cost codes
**Entities**:
- Cost Code (code, label, description, builder_id)
- Line Item (description, amount, suggested_code, confidence)
  **Services**:
- Semantic Embeddings via Sentence-BERT (local model)
- Cosine similarity between line item descriptions and cost code labels
  **Example**: "Install copper piping" → Cost Code 15140 "Plumbing - Rough-in" (confidence: 0.89)

### 5. Review Workflow
**Responsibility**: Human-in-the-loop validation for low-confidence extractions
**Entities**:
- Review Queue (pending items sorted by confidence)
- Correction History (human edits for model improvement)
  **Business Rules**:
- Confidence < 85% → Requires review
- 3-way match failure → Requires review
- New vendor (no match) → Requires approval

## Aggregates

### Invoice Processing Aggregate
**Root**: ProcessedInvoice
**Components**:
- document_id
- processing_method (traditional/vision)
- extraction_result (fields + confidence)
- matched_subcontractor (id + score)
- classified_line_items (code + confidence)
- review_status (auto_approved/needs_review/approved/rejected)
- processing_metrics (time_ms, accuracy_estimate)

## Key Domain Rules
1. Multiple invoice formats must normalize to single schema
2. Vendor matching requires 85%+ similarity or manual review
3. Cost code suggestions below 80% confidence need human review
4. Each builder has isolated cost code namespace (multi-tenancy)
5. Processing method selection based on document quality/format

## Anti-Corruption Layer
- Local OCR engines (Tesseract, PaddleOCR)
- Local LLMs via Ollama (Qwen2-VL, Llama)
- Legacy BuilderTrend "Bills" feature integration points

## Value Proposition
- Reduce manual data entry time by 80%+
- Handle format variance without custom rules per vendor
- Increase payment feature adoption through automation
- Scale to handle diverse contractor ecosystem with confidence scoring

## Implementation Status

### Completed Features
1. **Invoice Upload & Storage** - `backend/routers/invoices.py`, `frontend/src/components/InvoiceUploadForm.tsx`
2. **Traditional OCR** - `backend/services/traditional_ocr_service.py`, Tesseract 5.5.2
3. **Vision AI** - `backend/services/vision_ai_service.py`, Qwen2.5vl:7b 7B via Ollama
4. **Vendor Matching** - `backend/services/vendor_matching_service.py`, RapidFuzz fuzzy matching
5. **Cost Classification** - `backend/services/cost_code_service.py`, Sentence-BERT embeddings
6. **Comparison Dashboard** - `backend/services/comparison_service.py`, `frontend/src/components/ComparisonDashboard.tsx`
7. **Review Workflow** - `backend/services/review_workflow_service.py`, `frontend/src/components/ReviewDashboard.tsx`

### Technical Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Python 3.12+
- **Frontend**: React, TypeScript, Vite
- **OCR**: Tesseract (traditional), Qwen2.5vl:7b (vision)
- **ML Models**: Sentence-BERT (all-MiniLM-L6-v2), RapidFuzz
- **Thresholds**: Extraction 70%, Vendor 85%, Cost Code 80%

### Database Schema
8 tables: `invoices`, `extracted_fields`, `subcontractors`, `vendor_matches`, `cost_codes`, `line_items`, `correction_history`, `processing_metrics`

See `backend/models.py` for full schema, `backend/schemas.py` for API contracts, `frontend/src/types/invoice.ts` for TypeScript types.