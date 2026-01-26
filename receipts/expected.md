# Test Invoice Expected Results - Source of Truth

This file contains the ground truth data for all test invoices. Use this for validation and comparison during testing.

---

## 📋 Test Invoice Specifications

### Invoice 1: ABC Plumbing LLC (High Quality)
**File:** `abc-plumbing.png`  
**Purpose:** Test successful extraction with high confidence scores  
**Quality:** High-resolution, clean, professional invoice

**Expected Extraction:**
```json
{
  "vendor_name": "ABC Plumbing LLC",
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-15",
  "total_amount": 5432.00,
  "line_items": [
    {
      "description": "Install copper piping - rough-in",
      "quantity": null,
      "unit_price": null,
      "total": 3200.00
    },
    {
      "description": "Install fixtures and faucets",
      "quantity": null,
      "unit_price": null,
      "total": 1800.00
    },
    {
      "description": "Materials and supplies",
      "quantity": null,
      "unit_price": null,
      "total": 432.00
    }
  ]
}
```

**Expected Results:**
- Traditional OCR Confidence: >85%
- Vision AI Confidence: >90%
- Vendor Match: 100% (exact match: "ABC Plumbing LLC")
- Cost Codes Expected: 15140 (Plumbing - Rough-in), 15410 (Plumbing Fixtures)
- Review Status: Auto-approved (high confidence)

---

### Invoice 2: Smith Electric Inc. (Complex Multi-Line)
**File:** `smith-electric.png`  
**Purpose:** Test cost code classification with many line items  
**Quality:** Professional, clean table layout

**Expected Extraction:**
```json
{
  "vendor_name": "Smith Electric Inc.",
  "invoice_number": "E-12345",
  "invoice_date": "2024-02-20",
  "total_amount": 12450.00,
  "line_items": [
    {
      "description": "Electrical panel installation",
      "quantity": null,
      "unit_price": null,
      "total": 4500.00
    },
    {
      "description": "Wire and conduit - 200 ft",
      "quantity": null,
      "unit_price": null,
      "total": 850.00
    },
    {
      "description": "Install outlets and switches",
      "quantity": null,
      "unit_price": null,
      "total": 1200.00
    },
    {
      "description": "LED lighting fixtures",
      "quantity": null,
      "unit_price": null,
      "total": 2100.00
    },
    {
      "description": "Install security system wiring",
      "quantity": null,
      "unit_price": null,
      "total": 1500.00
    },
    {
      "description": "HVAC thermostat wiring",
      "quantity": null,
      "unit_price": null,
      "total": 450.00
    },
    {
      "description": "Exterior lighting installation",
      "quantity": null,
      "unit_price": null,
      "total": 800.00
    },
    {
      "description": "Testing and inspection",
      "quantity": null,
      "unit_price": null,
      "total": 600.00
    },
    {
      "description": "Labor and materials",
      "quantity": null,
      "unit_price": null,
      "total": 450.00
    }
  ]
}
```

**Expected Results:**
- Traditional OCR Confidence: >80%
- Vision AI Confidence: >85%
- Vendor Match: 100% (exact match: "Smith Electric Inc.")
- Cost Codes Expected: 16050 (Electrical - Basic), 16500 (Lighting), 28130 (Security Systems)
- Review Status: Auto-approved or needs_review (if any cost code <80% confidence)

---

### Invoice 3: Johnson HVAC Services (Low Quality Scan)
**File:** `johnson-hvac.png`  
**Purpose:** Test low-confidence scenarios and review workflow  
**Quality:** Poor quality scan, faded text, slight rotation

**Expected Extraction:**
```json
{
  "vendor_name": "Johnson HVAC Services",
  "invoice_number": "JH-2024-789",
  "invoice_date": "2024-01-18",
  "total_amount": 3850.00,
  "line_items": [
    {
      "description": "Furnace repair and parts",
      "quantity": null,
      "unit_price": null,
      "total": 1200.00
    },
    {
      "description": "Duct cleaning service",
      "quantity": null,
      "unit_price": null,
      "total": 950.00
    },
    {
      "description": "Thermostat replacement",
      "quantity": null,
      "unit_price": null,
      "total": 450.00
    },
    {
      "description": "Service call fee",
      "quantity": null,
      "unit_price": null,
      "total": 1250.00
    }
  ]
}
```

**Expected Results:**
- Traditional OCR Confidence: 0% (complete failure on poor quality)
- Vision AI Confidence: 95% (handles poor quality excellently)
- Vendor Match: 100% (exact match "Johnson HVAC Services")
- Cost Codes (Installation-only): 17-50% → **needs_review** (semantic mismatch demo)
- Cost Codes (With Repair): 80-95% → auto-approved (23020, 23030, 23040, 00100)
- Review Status: **needs_review** (low confidence triggers manual review correctly)

---

### Invoice 4: Martinez Roofing & Construction Co (Vendor Variation)
**File:** `martinez-roofing.png`  
**Purpose:** Test fuzzy matching with vendor name variations  
**Quality:** Good quality, standard invoice

**Expected Extraction:**
```json
{
  "vendor_name": "Martinez Roofing & Construction Co",
  "invoice_number": "MR-456",
  "invoice_date": "2024-03-05",
  "total_amount": 18750.00,
  "line_items": [
    {
      "description": "Tear off existing shingles",
      "quantity": null,
      "unit_price": null,
      "total": 3200.00
    },
    {
      "description": "Install new architectural shingles",
      "quantity": null,
      "unit_price": null,
      "total": 9500.00
    },
    {
      "description": "Replace flashing and underlayment",
      "quantity": null,
      "unit_price": null,
      "total": 2800.00
    },
    {
      "description": "Gutter installation",
      "quantity": null,
      "unit_price": null,
      "total": 2050.00
    },
    {
      "description": "Cleanup and disposal",
      "quantity": null,
      "unit_price": null,
      "total": 1200.00
    }
  ]
}
```

**Expected Results:**
- Traditional OCR Confidence: >85%
- Vision AI Confidence: >90%
- Vendor Match: 80-90% (fuzzy match: "Martinez Roofing LLC" vs "Martinez Roofing & Construction Co")
- Cost Codes Expected: 07310 (Roofing - Shingles), 07620 (Flashing)
- Review Status: **needs_review** (vendor match <90% requires confirmation)

---

### Invoice 5: Mike's Drywall (Handwritten - Edge Case)
**File:** `mike-drywall.png`  
**Purpose:** Test missing fields and partial extraction  
**Quality:** Handwritten receipt, phone photo

**Expected Extraction:**
```json
{
  "vendor_name": "Mike's Drywall",
  "invoice_number": "0042",
  "invoice_date": "2024-03-12",
  "total_amount": 2100.00,
  "line_items": [
    {
      "description": "Drywall repair - living room",
      "quantity": null,
      "unit_price": null,
      "total": 1400.00
    },
    {
      "description": "Paint + labor",
      "quantity": null,
      "unit_price": null,
      "total": 700.00
    }
  ]
}
```

**Expected Results:**
- Traditional OCR Confidence: 40-60% (handwritten is challenging)
- Vision AI Confidence: 60-75% (better at handwriting but still difficult)
- Vendor Match: 85-95% (fuzzy match: "Mike's Drywall" vs "Mike's Drywall Service")
- Cost Codes Expected: 09260 (Gypsum Board), 09910 (Painting)
- Review Status: **needs_review** (low confidence, partial extraction)

---

## 📊 Database Reference - Subcontractors

These subcontractors exist in the test database (from `seed_data.sql`):

| ID | Name | Contact Info |
|---|---|---|
| 1 | ABC Plumbing LLC | (555) 123-4567, contact@abcplumbing.com |
| 2 | Smith Electric Inc. | (555) 234-5678, info@smithelectric.com |
| 3 | Johnson HVAC Services | (555) 345-6789, service@johnsonhvac.com |
| 4 | Martinez Roofing LLC | (555) 456-7890, jobs@martinezroofing.com |
| 5 | Perfect Paint Co. | (555) 567-8901, paint@perfectpaint.com |
| 6 | Green Landscaping Services | (555) 678-9012, green@landscape.com |
| 7 | Quality Concrete Works | (555) 789-0123, concrete@quality.com |
| 8 | Mike's Drywall Service | (555) 890-1234, mike@drywall.com |

---

## 🎯 Test Objectives & Validation

### Extraction Quality
- **Invoice 1**: Should extract all fields correctly (>90% confidence)
- **Invoice 2**: Should handle 9 line items and classify them correctly
- **Invoice 3**: Should trigger `needs_review` status due to low quality
- **Invoice 4**: Should test fuzzy matching (80-90% match score)
- **Invoice 5**: Should handle partial extraction gracefully

### Vendor Matching
- **Exact matches**: Invoices 1, 2, 3 (should be 100% or near-100%)
- **Fuzzy matches**: Invoices 4, 5 (should be 80-95%)
- **Match threshold**: >85% for auto-approval, <85% requires review

### Cost Code Classification
- Test semantic similarity across different trade types
- Expected confidence: >80% for common items, <80% for ambiguous items
- Low confidence should trigger `needs_review` status

### Review Workflow
- Invoices 3, 4, 5 should all land in the Review Queue
- Should allow inline editing of all fields
- Should save corrections to correction_history table
- Should allow approve/reject actions

---

## 🔄 Testing Workflow

1. **Upload** → Upload all 5 invoices via InvoiceUploadForm
2. **Extract** → Run both Traditional OCR and Vision AI on each
3. **Compare** → View ComparisonDashboard to see side-by-side results
4. **Match** → Run vendor matching (should find candidates for all)
5. **Classify** → Run cost code classification on line items
6. **Review** → Check Review Queue for invoices needing attention (3, 4, 5)
7. **Correct** → Make corrections via InvoiceReviewForm
8. **Approve** → Approve invoices that pass validation

---

## 📝 Notes for Agent 2

When consolidating tasks.md, please note:
- All 5 test invoices are in `/receipts` directory
- This file (`expected.md`) is the **single source of truth** for validation
- Bug fixes completed: Vision AI UUID, Traditional OCR date/line items
- Ready for end-to-end testing of the complete pipeline

---

## 🧪 ACTUAL TEST RESULTS (2026-01-26)

| Invoice | Trad OCR | Vision AI | Vendor | Cost Code | Status |
|---------|----------|-----------|--------|-----------|--------|
| **ABC Plumbing** | ✅ 100% (3ms) | ✅ 100% | ✅ 100% | ⏳ Pending | Perfect both methods |
| **Johnson HVAC** | ❌ 0% (462ms) | ✅ 95% (21s) | ✅ 100% | ⚠️ 17-50% | **Needs Review** (low confidence) |
| Smith Electric | ⏳ | ⏳ | ⏳ | ⏳ | Not tested |
| Martinez Roofing | ⏳ | ⏳ | ⏳ | ⏳ | Not tested |
| Mike's Drywall | ⏳ | ⏳ | ⏳ | ⏳ | Not tested |

**Johnson HVAC Details:**
- Vendor: 100% match to "Johnson HVAC Services" (exact)
- Cost Codes (Installation-only): 23000 (32%), 23010 (50%), 23000 (37%), 07010 (17%) - all below 80%
- Status: `needs_review` (correct behavior)
- **Demo Gold #1**: OCR 0% failure vs Vision AI 95% success on poor quality scan
- **Demo Gold #2**: Low confidence correctly shows semantic mismatch ("repair" ≠ "install")
- After adding repair cost codes (23020, 23030, 23040, 00100), expect 80-95% confidence
