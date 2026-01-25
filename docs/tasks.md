# Invoice Automation System - Agent Task Coordination

> **LIVING DOCUMENT**: Agents MUST update status markers after completing each task.
> **Last Updated**: 2026-01-25

---

## 🤝 COORDINATION RULES (READ FIRST)

### For Both Agents
1. **Update This Document**: When you start a task, change status from `TODO` to `IN_PROGRESS`. When complete, change to `DONE` and add completion timestamp.
2. **Check Dependencies**: Before starting, verify all "Depends On" tasks are `DONE`.
3. **Respect Ownership**: Do NOT modify files owned by the other agent unless coordinating.
4. **Build Failures**:
   - If tests/build fail AFTER your changes → Fix immediately
   - If tests/build fail BEFORE your changes → Wait patiently, add note in document, notify other agent
5. **API Contracts**: Defined below. Do NOT change without mutual agreement.
6. **Commit Messages**: Prefix with `[AGENT-1]` or `[AGENT-2]` so we can track who did what.

### Communication Protocol
- **Blocked?** Add `⚠️ BLOCKED: reason` to your task status
- **Question?** Add `❓ QUESTION: your question` to task notes
- **Change Request?** Add `🔄 CHANGE_REQUEST: description` if you need the other agent to modify something

---

## 📋 API CONTRACTS (DO NOT CHANGE WITHOUT AGREEMENT)

### Extraction Result Schema (Used by both agents)
```typescript
interface ExtractionResult {
  invoice_id: string;
  processing_method: "traditional" | "vision";
  extraction_status: "success" | "partial" | "failed";
  fields: {
    vendor_name: string | null;
    invoice_number: string | null;
    invoice_date: string | null;  // ISO 8601 format
    total_amount: number | null;
  };
  line_items: Array<{
    description: string;
    quantity: number | null;
    unit_price: number | null;
    total: number;
  }>;
  confidence: number;  // 0.0 to 1.0
  processing_time_ms: number;
  raw_output?: any;  // For debugging
  created_at: string;  // ISO 8601
}
```

### Database Status Values
```python
InvoiceStatus = Literal[
    "uploaded",           # Initial state after TASK 1
    "processing",         # During extraction
    "extracted",          # After TASK 2A or 2B
    "matched",            # After TASK 4
    "classified",         # After TASK 5
    "needs_review",       # Low confidence (<85%)
    "approved",           # Human approved
    "rejected"            # Human rejected
]
```

---

## 📊 TASK STATUS LEGEND
- `TODO` - Not started
- `IN_PROGRESS` - Currently being worked on (add agent name + start time)
- `DONE` - Completed (add completion timestamp)
- `BLOCKED` - Waiting on dependency or other agent

---

## PHASE 0: FOUNDATION

### SETUP: Environment Preparation
**Status**: `DONE` ✅ (Agent 1 part complete)  
**Owner**: Agent 1 (lead), Agent 2 (assist)  
**Completed**: 2026-01-25 (Agent 1)

#### Agent 1 Tasks: ✅ COMPLETE
- [x] Added dependencies to `backend/pyproject.toml`: pytesseract, pdf2image, pillow, rapidfuzz, sentence-transformers, python-multipart, aiofiles
- [x] Installed via `uv sync`
- [x] Installed system dependencies: `brew install tesseract poppler`
- [x] Verified: tesseract 5.5.2 installed at `/opt/homebrew/bin/tesseract`
- [x] Verified: All Python imports successful

#### Agent 2 Tasks: TODO
```bash
# Ollama setup (can run in parallel)
brew install ollama
ollama pull qwen2-vl:7b
ollama pull llama3.1:8b  # backup option

# Verify Ollama is running
ollama list
```

#### Verification:
- [x] Agent 1: `pytesseract --version` works ✅
- [ ] Agent 2: `ollama list` shows qwen2-vl:7b
- [ ] Both: `npm run dev` (frontend) and backend server start without errors

**Notes**:
- Agent 1: Using `uv` package manager (project standard)
- Agent 1: Dependencies added to pyproject.toml for proper version management

---

## PHASE 1: CORE INFRASTRUCTURE

### TASK 1: Invoice Upload & Storage + Complete Database Schema
**Status**: `DONE` ✅  
**Owner**: Agent 1  
**Completed**: 2026-01-25

#### Implemented:
- [x] Migration `20260125_complete_invoice_schema.py` - All 8 tables created
- [x] `backend/models.py` - SQLAlchemy models with relationships
- [x] `backend/schemas.py` - Pydantic schemas (ExtractionResult API contract)
- [x] `backend/services/invoice_storage_service.py` - File upload handling
- [x] `backend/routers/invoices.py` - Upload, get, list, delete endpoints
- [x] `backend/seed_data.sql` - 8 subcontractors + 16 cost codes
- [x] `frontend/src/components/InvoiceUploadForm.tsx` - Drag & drop UI
- [x] `frontend/src/types/invoice.ts` - TypeScript types
- [x] `frontend/src/services/invoiceApi.ts` - API client
- [x] Test builder_id: `00000000-0000-0000-0000-000000000001`

**Agent 2 UNBLOCKED** - Can start TASK 2B, 5, 3

---

## PHASE 2: EXTRACTION ENGINES (PARALLEL)

### TASK 2A: Traditional OCR Path
**Status**: `DONE` ✅  
**Owner**: Agent 1  
**Completed**: 2026-01-25

#### Deliverables: ✅ ALL COMPLETE
1. **Backend Service** ✅:
   - `backend/services/traditional_ocr_service.py`
   - Implements full OCR pipeline: PDF→Image→Tesseract→Regex parsing
   - Confidence scoring based on field extraction success
   - Handles both PDF and image files
   - Extracts: vendor_name, invoice_number, invoice_date, total_amount, line_items

2. **Backend Endpoint** ✅:
   - Added to `backend/routers/invoices.py`:
   - `POST /api/invoices/{invoice_id}/extract/traditional`
   - Saves to: extracted_fields, line_items, processing_metrics tables
   - Updates invoice.status = 'extracted'
   - Error handling with rollback to 'uploaded' state

3. **Frontend Component** ✅:
   - `frontend/src/components/TraditionalOCRProcessor.tsx`
   - `frontend/src/components/TraditionalOCRProcessor.css`
   - Displays extracted fields with confidence color-coding
   - Shows line items in table format
   - Raw OCR text preview (first 500 chars)
   - Processing time display
   - Re-extract button

4. **Frontend Integration** ✅:
   - Updated `frontend/src/App.tsx` with split-pane layout
   - Invoice list on left, processor on right
   - Click-to-select invoice for processing
   - Auto-selects newly uploaded invoices
   - Status badges with color coding
   - Updated `frontend/src/services/invoiceApi.ts` with extraction methods

#### Verification:
- [x] Endpoint accepts invoice_id and returns ExtractionResult
- [x] Works with PDF and image files (pdf2image + pytesseract)
- [x] Saves results to database correctly
- [x] Frontend displays extraction results with confidence scores
- [x] Processing time logged to processing_metrics
- [x] No linter errors

**Completion Timestamp**: 2026-01-25  
**Notes**:
- **Regex Patterns**: Vendor (first 3 lines, LLC/Inc detection), Total (multiple patterns), Date (flexible formats), Invoice # (various prefixes)
- **Confidence Algorithm**: Weighted scoring (Vendor 25%, Total 25%, Invoice# 15%, Date 15%, Line Items 20%)
- **Line Item Parsing**: Two-pass approach (detailed pattern, then simple fallback)
- **UI/UX**: Color-coded confidence (green >85%, yellow 70-85%, red <70%)
- **Architecture**: Matches API contract for interoperability with Vision AI path

---

### TASK 2B: Vision-Native AI Path
**Status**: `IN_PROGRESS` (Agent 2, started 2026-01-25)  
**Owner**: Agent 2  
**Depends On**: TASK 1 ✅  
**Blocks**: TASK 3  
**Can Run in Parallel With**: TASK 2A

#### Implemented:
- [x] `backend/services/vision_ai_service.py` - Qwen2-VL integration with JSON parsing
- [x] `backend/routers/invoices.py` - POST `/invoices/{invoice_id}/extract/vision` endpoint
- [x] `backend/tests/test_vision_extraction.py` - Integration tests
- [x] `backend/pyproject.toml` - Added ollama dependency
- [x] Database writes to: extracted_fields, line_items, processing_metrics
- [x] Graceful error handling for malformed LLM responses
- [ ] Frontend component (pending)

#### Verification:
- [x] Endpoint accepts invoice_id and returns ExtractionResult
- [x] JSON parsing handles malformed LLM responses gracefully
- [x] Saves results to database correctly
- [x] Processing time logged to processing_metrics
- [ ] Ollama service running verification (requires user setup)
- [ ] Frontend displays extraction results (pending)

**Notes**:
- Prompt extracts: vendor_name, invoice_number, invoice_date, total_amount, line_items, confidence
- JSON extraction handles markdown code blocks and extra text
- Returns confidence 0.0-1.0, status: success/partial/failed based on confidence threshold

---

## PHASE 3: INTELLIGENCE LAYER (PARALLEL)

### TASK 4: Fuzzy Vendor Matching
**Status**: `TODO`  
**Owner**: Agent 1  
**Depends On**: TASK 2A (DONE) OR TASK 2B (DONE) - need extracted vendor names  
**Blocks**: TASK 6  
**Can Run in Parallel With**: TASK 5

#### Deliverables:
1. **Backend Service** (Agent 1 owns):
   - `backend/services/vendor_matching_service.py`
   ```python
   from rapidfuzz import fuzz, process
   
   class VendorMatchingService:
       def match(self, extracted_vendor: str, builder_id: str) -> list[MatchCandidate]:
           """
           Returns top 3 matches with scores.
           Threshold: 70+ to show, 85+ for auto-approve, 90+ for high confidence
           """
           pass
   ```

2. **Backend Endpoint** (Agent 1 creates):
   - Add to `backend/routers/invoices.py`:
   ```python
   @router.post("/invoices/{invoice_id}/match-vendor")
   async def match_vendor(invoice_id: str):
       # 1. Get extracted_fields.vendor_name from DB
       # 2. Call VendorMatchingService.match()
       # 3. Save top match to vendor_matches table
       # 4. Update invoice.status = 'matched'
       # 5. Return match results with scores
       pass
   ```

3. **Frontend Component** (Agent 1 creates):
   - `frontend/src/components/VendorMatcher.tsx`
   - Display extracted vendor name
   - Show top 3 matches with similarity scores
   - Color-code: Green (>90%), Yellow (85-90%), Red (<85%)
   - Allow manual selection or "Add New Vendor" button

#### Verification:
- [ ] Fuzzy matching handles typos ("ABC Plumbing" matches "A.B.C. Plumbing LLC")
- [ ] Scores calculated correctly (0-100)
- [ ] Top 3 results returned sorted by score
- [ ] Manual selection saves to vendor_matches
- [ ] Low scores flag invoice for review (status = 'needs_review')

**Completion Timestamp**: _Agent 1 adds when done_  
**Notes**:
_Agent 1: Add matching algorithm details, threshold tuning, etc._

---

### TASK 5: Cost Code Classification
**Status**: `TODO`  
**Owner**: Agent 2  
**Depends On**: TASK 2A (DONE) OR TASK 2B (DONE) - need line items  
**Blocks**: TASK 6  
**Can Run in Parallel With**: TASK 4

#### Deliverables:
1. **Backend Service** (Agent 2 owns):
   - `backend/services/cost_code_service.py`
   ```python
   from sentence_transformers import SentenceTransformer
   import numpy as np
   
   class CostCodeService:
       def __init__(self):
           self.model = SentenceTransformer('all-MiniLM-L6-v2')
       
       def classify(self, line_items: list[dict], builder_id: str) -> list[ClassificationResult]:
           """
           Returns suggested cost code + confidence for each line item.
           Threshold: <80% confidence requires review
           """
           pass
   ```

2. **Backend Endpoint** (Agent 2 creates):
   - Add to `backend/routers/invoices.py`:
   ```python
   @router.post("/invoices/{invoice_id}/classify-costs")
   async def classify_costs(invoice_id: str):
       # 1. Get line_items from DB
       # 2. Get cost_codes for builder from DB
       # 3. Call CostCodeService.classify()
       # 4. Update line_items with suggested_code and confidence
       # 5. Update invoice.status = 'classified'
       # 6. Flag for review if any confidence < 80%
       # 7. Return classification results
       pass
   ```

3. **Frontend Component** (Agent 2 creates):
   - `frontend/src/components/CostCodeClassifier.tsx`
   - Display line items with descriptions
   - Show suggested cost code with confidence bar
   - Dropdown to override with full cost code list
   - Flag items <80% confidence in yellow

#### Verification:
- [ ] Sentence-BERT model loads successfully (~100MB download)
- [ ] Cosine similarity calculated correctly
- [ ] Suggested codes make semantic sense
- [ ] Confidence scores in range 0.0-1.0
- [ ] Low confidence items flagged for review
- [ ] Manual overrides saved to confirmed_code

**Completion Timestamp**: _Agent 2 adds when done_  
**Notes**:
_Agent 2: Add model performance, embedding cache strategy, etc._

---

## PHASE 4: INTEGRATION & REVIEW (PARALLEL)

### TASK 3: Comparison Dashboard
**Status**: `TODO`  
**Owner**: Agent 2  
**Depends On**: TASK 2A (DONE) AND TASK 2B (DONE)  
**Blocks**: None  
**Can Run in Parallel With**: TASK 6

#### Deliverables:
1. **Backend Service** (Agent 2 owns):
   - `backend/services/comparison_service.py`
   ```python
   class ComparisonService:
       def compare(self, invoice_id: str) -> ComparisonResult:
           """
           Fetch results from both extraction methods.
           Calculate: accuracy, field-by-field diff, processing time diff
           """
           pass
   ```

2. **Backend Endpoint** (Agent 2 creates):
   - Add to `backend/routers/invoices.py`:
   ```python
   @router.get("/invoices/{invoice_id}/comparison")
   async def get_comparison(invoice_id: str):
       # 1. Get extracted_fields for both methods
       # 2. Get processing_metrics for both
       # 3. Call ComparisonService.compare()
       # 4. Return side-by-side results
       pass
   ```

3. **Frontend Component** (Agent 2 creates):
   - `frontend/src/components/ComparisonDashboard.tsx`
   - Side-by-side layout: Traditional OCR | Vision AI
   - Metrics cards: Processing time, confidence, field accuracy
   - Visual diff of extracted fields (highlight mismatches)
   - Chart: Accuracy comparison using recharts

#### Verification:
- [ ] Both extraction results display correctly
- [ ] Field-by-field diff shows mismatches
- [ ] Processing time comparison accurate
- [ ] Chart displays comparison metrics
- [ ] Handles case where only one method has run

**Completion Timestamp**: _Agent 2 adds when done_  
**Notes**:
_Agent 2: Add comparison insights, visualization choices, etc._

---

### TASK 6: Review Workflow Dashboard
**Status**: `TODO`  
**Owner**: Agent 1  
**Depends On**: TASK 4 (DONE) AND TASK 5 (DONE)  
**Blocks**: None  
**Can Run in Parallel With**: TASK 3

#### Deliverables:
1. **Backend Service** (Agent 1 owns):
   - `backend/services/review_workflow_service.py`
   ```python
   class ReviewWorkflowService:
       def update_status(self, invoice_id: str, new_status: str, corrections: dict):
           """
           Update invoice status, apply corrections, log to correction_history
           """
           pass
   ```

2. **Backend Endpoints** (Agent 1 creates):
   - Add to `backend/routers/invoices.py`:
   ```python
   @router.get("/invoices")
   async def list_invoices(status: str = None):
       # Filter by status: needs_review, approved, etc.
       pass
   
   @router.patch("/invoices/{invoice_id}/status")
   async def update_status(invoice_id: str, status: str):
       # Update invoice status (approved/rejected)
       pass
   
   @router.post("/invoices/{invoice_id}/corrections")
   async def save_corrections(invoice_id: str, corrections: dict):
       # Save human corrections to correction_history
       # Update extracted_fields with corrected values
       pass
   ```

3. **Frontend Component** (Agent 1 creates):
   - `frontend/src/components/ReviewDashboard.tsx`
   - Split view: Invoice image | Extracted data form
   - Filter dropdown: All | Needs Review | Approved | Rejected
   - Inline editing for all fields
   - Highlight low-confidence fields (<85%) in yellow
   - Buttons: "Approve", "Reject", "Save Corrections"

#### Verification:
- [ ] List invoices filtered by status
- [ ] Load invoice image and extracted data
- [ ] Inline editing works for all fields
- [ ] Corrections saved to correction_history
- [ ] Status updates propagate correctly
- [ ] Low-confidence fields highlighted

**Completion Timestamp**: _Agent 1 adds when done_  
**Notes**:
_Agent 1: Add review UI/UX decisions, validation rules, etc._

---

## 🎯 PROJECT COMPLETION CHECKLIST

### End-to-End Testing (Both Agents)
- [ ] Upload invoice → Extract (Traditional) → Match Vendor → Classify Costs → Review → Approve
- [ ] Upload invoice → Extract (Vision) → Match Vendor → Classify Costs → Review → Approve
- [ ] Comparison dashboard shows both methods
- [ ] Low-confidence invoices flagged correctly
- [ ] Corrections saved and applied

### Documentation (Both Agents)
- [ ] Agent 1: Document traditional OCR accuracy and limitations
- [ ] Agent 2: Document vision AI prompt engineering and results
- [ ] Both: Create demo script with test invoices

### Demo Preparation (Both Agents)
- [ ] Prepare 3 test invoices: simple, complex, low-quality
- [ ] Run both extraction methods on all 3
- [ ] Document comparison results
- [ ] Practice demo walkthrough (5-7 minutes)

---

## 📝 AGENT NOTES & COMMUNICATION

### Agent 1 Notes:
- 2026-01-25 10:00: ✅ TASK 1 DONE - Agent 2 unblocked
- 2026-01-25 11:30: ✅ SETUP DONE (Agent 1 part) - Dependencies installed via uv
- 2026-01-25 12:45: ✅ TASK 2A DONE - Traditional OCR fully implemented and integrated
- Next: TASK 4 (Vendor Matching) - waiting for TASK 2A/2B to be tested
- Next: TASK 6 (Review Workflow) - waiting for TASK 4 + TASK 5

---

### Agent 2 Notes:
- 2026-01-25: TASK 2B backend implementation complete (service + endpoint + tests)
- Next: Frontend component for Vision AI, then TASK 5 (Cost Code Classification)

---

## 🔄 CHANGE LOG
- **2026-01-25**: Document created with full task breakdown and coordination rules
