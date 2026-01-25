# 🚀 Agent 2 Quick Start Guide

**Status**: ✅ Agent 1 has completed TASK 1 - You are UNBLOCKED!

---

## 🎯 What's Ready For You

### Database Schema ✅
All 8 tables are created and ready:
- ✅ `invoices` - For storing uploaded invoices
- ✅ `extracted_fields` - **You'll use this for Vision AI results**
- ✅ `line_items` - **You'll use this for extracted line items**
- ✅ `cost_codes` - **16 test codes ready for classification**
- ✅ `subcontractors` - 8 test vendors for matching
- ✅ `vendor_matches` - For fuzzy matching results
- ✅ `processing_metrics` - **Log your processing times here**
- ✅ `correction_history` - For human corrections

### Seed Data ✅
Run this to populate test data:
```bash
cd backend
psql -d receiptor_db -f seed_data.sql
```

**Test Builder ID**: `00000000-0000-0000-0000-000000000001`

### API Endpoints ✅
Available now:
- `POST /api/invoices/upload` - Upload test invoices
- `GET /api/invoices/{id}` - Get invoice details
- `GET /api/invoices` - List all invoices

---

## 📋 Your Tasks (Can Start Immediately)

### TASK 2B: Vision-Native AI Path (Qwen2-VL)
**Priority**: HIGH (blocks TASK 3)

**What to Build**:
1. `backend/services/vision_ai_service.py`
   ```python
   import ollama
   
   class VisionAIService:
       def process(self, invoice_path: str) -> ExtractionResult:
           # Call ollama.chat() with qwen2-vl:7b
           # Parse JSON response
           # Return ExtractionResult
   ```

2. Add endpoint to `backend/routers/invoices.py`:
   ```python
   @router.post("/invoices/{invoice_id}/extract/vision")
   async def extract_vision(invoice_id: str):
       # Get file path from DB
       # Call VisionAIService.process()
       # Save to extracted_fields and line_items tables
       # Update invoice.status = 'extracted'
   ```

3. Frontend: `frontend/src/components/VisionAIProcessor.tsx`

**Database Tables You'll Write To**:
- `extracted_fields` (vendor_name, invoice_number, invoice_date, total_amount, confidence, raw_json)
- `line_items` (description, quantity, unit_price, amount)
- `processing_metrics` (method='vision', processing_time_ms)
- Update `invoices.status` to 'extracted'

**API Contract (MUST MATCH)**:
```typescript
interface ExtractionResult {
  invoice_id: string;
  processing_method: "vision";  // Set this to "vision"
  extraction_status: "success" | "partial" | "failed";
  fields: {
    vendor_name: string | null;
    invoice_number: string | null;
    invoice_date: string | null;  // ISO 8601
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
  raw_output?: any;
  created_at: string;
}
```

---

### TASK 5: Cost Code Classification (Sentence-BERT)
**Priority**: HIGH (blocks TASK 6)

**What to Build**:
1. `backend/services/cost_code_service.py`
   ```python
   from sentence_transformers import SentenceTransformer
   
   class CostCodeService:
       def __init__(self):
           self.model = SentenceTransformer('all-MiniLM-L6-v2')
       
       def classify(self, line_items: list, builder_id: str):
           # Get cost_codes from DB
           # Generate embeddings
           # Calculate cosine similarity
           # Return suggestions with confidence
   ```

2. Add endpoint to `backend/routers/invoices.py`:
   ```python
   @router.post("/invoices/{invoice_id}/classify-costs")
   async def classify_costs(invoice_id: str):
       # Get line_items from DB
       # Call CostCodeService.classify()
       # Update line_items.suggested_code and confidence
   ```

3. Frontend: `frontend/src/components/CostCodeClassifier.tsx`

**Test With Seed Data**:
```sql
-- Line item: "Install copper piping"
-- Should match: Cost Code '15140' - 'Plumbing - Rough-in'

-- Line item: "Install light fixtures"
-- Should match: Cost Code '16060' - 'Electrical - Fixtures'
```

---

### TASK 3: Comparison Dashboard
**Priority**: MEDIUM (can start UI mockups now)

**What to Build**:
1. `backend/services/comparison_service.py`
2. Add endpoint: `GET /invoices/{invoice_id}/comparison`
3. Frontend: `frontend/src/components/ComparisonDashboard.tsx`

**Can Start Now**: Build UI skeleton and charts (using recharts)

---

## 🔧 Setup Checklist

Before you start coding:

```bash
# 1. Install Ollama (if not done)
brew install ollama
ollama pull qwen2-vl:7b
ollama list  # Verify model downloaded

# 2. Start Ollama service (in background terminal)
ollama serve

# 3. Install Python packages
cd backend
pip install ollama sentence-transformers

# 4. Run database migration
alembic upgrade head

# 5. Load seed data
psql -d receiptor_db -U root -h localhost -p 5432 -f seed_data.sql
# Password: password

# 6. Verify seed data
psql -d receiptor_db -U root -h localhost -p 5432
# Run: SELECT COUNT(*) FROM cost_codes;  -- Should return 16
# Run: SELECT COUNT(*) FROM subcontractors;  -- Should return 8
```

---

## 📝 How to Test Your Work

### 1. Upload a test invoice (use Agent 1's endpoint)
```bash
curl -X POST http://localhost:8000/api/invoices/upload \
  -F "file=@test_invoice.pdf" \
  -F "builder_id=00000000-0000-0000-0000-000000000001"

# Response: {"id": "some-uuid-here", ...}
```

### 2. Call your Vision AI endpoint
```bash
curl -X POST http://localhost:8000/api/invoices/{invoice_id}/extract/vision

# Should return ExtractionResult JSON
```

### 3. Verify database writes
```sql
-- Check extracted_fields
SELECT * FROM extracted_fields WHERE invoice_id = 'your-invoice-id';

-- Check line_items
SELECT * FROM line_items WHERE invoice_id = 'your-invoice-id';

-- Check processing_metrics
SELECT * FROM processing_metrics WHERE invoice_id = 'your-invoice-id';
```

---

## 🤝 Coordination with Agent 1

### Files You'll Create (No Conflicts)
- `backend/services/vision_ai_service.py` ✅
- `backend/services/cost_code_service.py` ✅
- `backend/services/comparison_service.py` ✅
- `frontend/src/components/VisionAIProcessor.tsx` ✅
- `frontend/src/components/CostCodeClassifier.tsx` ✅
- `frontend/src/components/ComparisonDashboard.tsx` ✅

### Shared File (Coordination Required)
- `backend/routers/invoices.py` ⚠️
  - Agent 1 has created the file with upload/get/list/delete endpoints
  - **You'll ADD new endpoints**: `/extract/vision`, `/classify-costs`, `/comparison`
  - **Update tasks.md** when you start editing this file

### When You're Done
1. Update `docs/tasks.md`:
   - Change status from `TODO` to `DONE`
   - Add completion timestamp
   - Add implementation notes
2. Add notes to "Agent 2 Notes" section at bottom
3. No need to notify Agent 1 (they'll see your updates in tasks.md)

---

## 🎯 Success Criteria

### TASK 2B Complete When:
- [x] Ollama qwen2-vl returns structured JSON from invoice image
- [x] Extraction result saved to `extracted_fields` table
- [x] Line items saved to `line_items` table
- [x] Processing time logged to `processing_metrics`
- [x] Frontend displays results with confidence scores
- [x] Handles malformed LLM responses gracefully

### TASK 5 Complete When:
- [x] Sentence-BERT model loads successfully
- [x] Cost code suggestions make semantic sense
- [x] Confidence scores calculated (0.0-1.0)
- [x] Low confidence items flagged (<0.80)
- [x] Frontend shows suggested codes with confidence bars

### TASK 3 Complete When:
- [x] Side-by-side comparison of Traditional vs Vision methods
- [x] Processing time comparison chart
- [x] Field-by-field accuracy diff
- [x] Works even when only one method has run

---

## 📞 Need Help?

- **Database Schema**: See `backend/models.py`
- **API Contracts**: See `docs/tasks.md` lines 30-67
- **Seed Data**: See `backend/seed_data.sql`
- **Example Endpoints**: See `backend/routers/invoices.py`

---

## 🚀 Ready to Start!

You have everything you need. Good luck, Agent 2! 🎉

**Pro Tip**: Start with TASK 2B first, as it unblocks TASK 3. TASK 5 can run in parallel.

