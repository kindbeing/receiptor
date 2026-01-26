# Agent Task Coordination

> **Last Updated**: 2026-01-25

## 🤝 COORDINATION RULES

1. **Update This Document**: Mark tasks `TODO` → `IN_PROGRESS` → `DONE` with timestamps
2. **Check Dependencies**: Verify dependencies before starting
3. **Respect Ownership**: Coordinate before modifying other agent's files
4. **Build Failures**: Fix immediately if caused by your changes
5. **API Contracts**: See `backend/schemas.py`, `frontend/src/types/invoice.ts` - do not change without agreement
6. **Commit Messages**: Prefix with `[AGENT-1]` or `[AGENT-2]`

### Communication Protocol
- **Blocked**: Add `⚠️ BLOCKED: reason`
- **Question**: Add `❓ QUESTION: details`
- **Change Request**: Add `🔄 CHANGE_REQUEST: description`

## 📋 API CONTRACTS

**Schemas**: See `backend/schemas.py` (Pydantic), `frontend/src/types/invoice.ts` (TypeScript)

**Key Interfaces**:
- `ExtractionResult` - Extraction output format (traditional/vision)
- `InvoiceStatus` - State machine: uploaded → processing → extracted → matched → classified → needs_review/approved/rejected
- `VendorMatchResult` - Fuzzy matching output with confidence scores
- `CorrectionHistory` - Audit trail for human corrections

## 📊 TASK STATUS
- `TODO` - Not started
- `IN_PROGRESS` - Working (add agent + time)
- `DONE` - Complete (add timestamp)
- `BLOCKED` - Waiting on dependency

## ✅ COMPLETED TASKS (2026-01-25)

**Agent 1** (Completed 2026-01-25):
1. ✅ **SETUP** - Dependencies: pytesseract, pdf2image, pillow, rapidfuzz, sentence-transformers, Tesseract 5.5.2
2. ✅ **TASK 1: Invoice Upload & Storage** - `backend/routers/invoices.py`, `frontend/src/components/InvoiceUploadForm.tsx`, 8 database tables
3. ✅ **TASK 2A: Traditional OCR** - `backend/services/traditional_ocr_service.py`, `frontend/src/components/TraditionalOCRProcessor.tsx`
4. ✅ **TASK 4: Vendor Matching** - `backend/services/vendor_matching_service.py`, RapidFuzz fuzzy matching, 85% threshold
5. ✅ **TASK 6: Review Workflow** - `backend/services/review_workflow_service.py`, `frontend/src/components/ReviewDashboard.tsx`, correction tracking

**Agent 2** (Completed 2026-01-25):
1. ✅ **SETUP** - Ollama, Qwen2.5-VL 7B model
2. ✅ **TASK 2B: Vision AI** - `backend/services/vision_ai_service.py`, `frontend/src/components/VisionAIProcessor.tsx`
3. ✅ **TASK 5: Cost Code Classification** - `backend/services/cost_code_service.py`, Sentence-BERT embeddings, 80% threshold
4. ✅ **TASK 3: Comparison Dashboard** - `backend/services/comparison_service.py`, `frontend/src/components/ComparisonDashboard.tsx`

**File References**:
- Backend services: `backend/services/` (7 services)
- Backend routes: `backend/routers/invoices.py` (13 endpoints)
- Frontend components: `frontend/src/components/` (8 components)
- Database: `backend/models.py` (8 tables), `backend/schemas.py` (Pydantic)
- Types: `frontend/src/types/invoice.ts` (TypeScript interfaces)

## 🔮 FUTURE TASKS

### Bug Fixes - 2026-01-25 (Agent 1)

**Issues Fixed:**
1. ✅ Vision AI UUID validation error - invoice_id now uses placeholder UUID
2. ✅ Traditional OCR date extraction - Added YYYY-MM-DD format support
3. ✅ Traditional OCR line item parsing - Multi-pattern approach with special character handling
4. ✅ Expected results file reformatted as source of truth

**Files Modified:**
- `backend/services/vision_ai_service.py`
- `backend/services/traditional_ocr_service.py`
- `receipts/expected.md` (created/reformatted)

**Test Invoices Ready:**
- All 5 test invoices in `/receipts` directory
- `expected.md` contains ground truth for validation
- Ready for end-to-end pipeline testing

**Expected Test Results:**
- Invoice 1 (ABC Plumbing): >90% confidence, all 3 line items extracted
- Invoice 2 (Smith Electric): >85% confidence, 9 line items for cost code testing
- Invoice 3 (Johnson HVAC): 50-85% confidence, triggers needs_review
- Invoice 4 (Martinez Roofing): 80-90% vendor match, fuzzy matching test
- Invoice 5 (Mike's Drywall): 40-75% confidence, partial extraction edge case

**Next Steps for Testing:**
1. Upload all 5 invoices
2. Run Traditional OCR + Vision AI extraction on each
3. Verify vendor matching with fuzzy scores
4. Test cost code classification
5. Validate Review Workflow for low-confidence invoices
6. Test correction tracking and approval flow