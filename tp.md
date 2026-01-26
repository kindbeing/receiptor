# Technical Alternatives & Improvements for Invoice Automation

> **Priority**: Reliability > Accuracy > Efficiency > Cost  
> **Date**: 2026-01-26  
> **Context**: BuilderTrend interview demo - proving production readiness

---

## 1. EXTRACTION RELIABILITY

### Problem
- Invoices vary wildly: handwritten, poor scans, unusual layouts, multiple languages
- Extraction failures or low confidence → manual review queue → operational bottleneck
- False positives (high confidence but wrong data) are worse than false negatives

### Current Solution
- **Hybrid approach**: Tesseract OCR (fast path) + Qwen2.5vl:7b (fallback)
- Confidence-based routing: >85% passes, <85% triggers Vision AI
- **Performance**: 3-462ms (OCR) vs 21s (Vision)
- **Reliability**: OCR fails on 30% of invoices, Vision handles 95%+

### Alternatives

#### A. Commercial Document AI APIs
- **AWS Textract**: [TBD]
- **Azure Document Intelligence**: [TBD]
- **Google Document AI**: [TBD]
- **Pros**: [TBD]
- **Cons**: [TBD]

#### B. Smaller/Faster Vision Models
- **llama3.2-vision:11b**: [TBD]
- **qwen2.5vl:3b**: [TBD]
- **minicpm-v:8b**: [TBD]
- **Pros**: [TBD]
- **Cons**: [TBD]

#### C. Fine-Tuned Document Models
- **Donut**: [TBD]
- **LayoutLMv3**: [TBD]
- **Pros**: [TBD]
- **Cons**: [TBD]

#### D. Multi-Model Ensemble
- Run 2-3 models, vote on results
- **Pros**: [TBD]
- **Cons**: [TBD]

### Recommendation
[TBD]

---

## 2. VALIDATION & CORRECTNESS

### Problem
- How do we know extraction is correct vs. just "confident"?
- Current system compares OCR vs Vision (agreement ≠ correctness)
- No ground truth validation in production
- Cannot measure actual accuracy on real invoices

### Current Solution
- **Comparison Service**: Cross-validates Traditional OCR vs Vision AI results
- Field match rate calculation
- Confidence scoring from models
- **Weakness**: Two wrong answers can agree with high confidence

### Alternatives

#### A. Ground Truth Testing Framework
- Test against `/receipts/expected.md` (known correct values)
- **Pros**: [TBD]
- **Cons**: [TBD]

#### B. Multi-Model Consensus
- Run 3+ models, majority vote or median
- **Pros**: [TBD]
- **Cons**: [TBD]

#### C. Business Logic Validation
- Check invoice total = sum(line_items)
- Date sanity checks (not in future, not >2 years old)
- Amount reasonableness (not $0.00, not $9,999,999)
- **Pros**: [TBD]
- **Cons**: [TBD]

#### D. Human-in-the-Loop Sampling
- Random 5% audit by humans
- Track accuracy over time
- **Pros**: [TBD]
- **Cons**: [TBD]

#### E. Confidence Calibration
- Map model confidence to actual accuracy
- Adjust thresholds based on historical performance
- **Pros**: [TBD]
- **Cons**: [TBD]

### Recommendation
[TBD]

---

## 3. VENDOR MATCHING ACCURACY

### Problem
- Vendor names have variations: "ABC Plumbing LLC" vs "A.B.C. Plumbing" vs "ABC Plumbing & Heating"
- Typos, abbreviations, legal entity changes
- False positives: "Smith Electric" matches "Smith Plumbing" at 70%
- Threshold too strict = miss valid matches, too loose = wrong matches

### Current Solution
- **RapidFuzz** with Levenshtein distance (`fuzz.ratio`)
- Thresholds: >90% high confidence, 85-90% auto-approve, 70-85% review, <70% reject
- **Accuracy**: Good on exact/close matches, struggles with structural differences

### Alternatives

#### A. Semantic Similarity (Embeddings)
- Use Sentence-BERT to encode vendor names
- Cosine similarity instead of string distance
- **Pros**: [TBD]
- **Cons**: [TBD]

#### B. Hybrid String + Semantic
- RapidFuzz first (fast), embeddings for borderline cases
- **Pros**: [TBD]
- **Cons**: [TBD]

#### C. Learning from Corrections
- Track human corrections in `correction_history`
- Build vendor alias table automatically
- **Pros**: [TBD]
- **Cons**: [TBD]

#### D. Multiple Fuzzy Algorithms
- Combine `fuzz.ratio`, `fuzz.token_sort_ratio`, `fuzz.partial_ratio`
- **Pros**: [TBD]
- **Cons**: [TBD]

#### E. Entity Resolution Service
- External service (e.g., Dedupe.io, Zingg)
- **Pros**: [TBD]
- **Cons**: [TBD]

### Recommendation
[TBD]

---

## 4. COST CODE CLASSIFICATION ACCURACY

### Problem
- Line item descriptions → Cost codes (e.g., "Install copper piping" → 15140 "Plumbing - Rough-in")
- Ambiguous items: "Labor" could be any trade
- Threshold 80% but what if top 2 are 78% and 77%? Both wrong.
- Each builder has custom cost codes (multi-tenancy)

### Current Solution
- **Sentence-BERT** (all-MiniLM-L6-v2): 22M params, 384-dim embeddings
- Cosine similarity between line item description and cost code labels
- Caching for performance (50ms for 100 items)
- **Accuracy**: Good on clear items, struggles with generic descriptions

### Alternatives

#### A. Larger Embedding Models
- **BGE-small-en-v1.5**: [TBD]
- **e5-small-v2**: [TBD]
- **nomic-embed-text**: [TBD]
- **Pros**: [TBD]
- **Cons**: [TBD]

#### B. Domain-Specific Fine-Tuning
- Fine-tune Sentence-BERT on construction line items → cost codes
- **Pros**: [TBD]
- **Cons**: [TBD]

#### C. LLM-Based Classification
- Send line item + cost code list to Qwen/Llama for reasoning
- **Pros**: [TBD]
- **Cons**: [TBD]

#### D. Hierarchical Classification
- First classify by trade (plumbing/electrical/etc.), then specific code
- **Pros**: [TBD]
- **Cons**: [TBD]

#### E. Learning from Corrections
- Track human corrections, re-weight embeddings
- Active learning loop
- **Pros**: [TBD]
- **Cons**: [TBD]

### Recommendation
[TBD]

---

## 5. ROUTING & ORCHESTRATION

### Problem
- When to use Traditional OCR vs Vision AI vs API services?
- How to minimize cost while maximizing accuracy?
- How to handle edge cases gracefully?

### Current Solution
- **Quality-based routing**: Image quality check → confidence-based fallback
- Implicit: Try OCR, if confidence <85%, use Vision
- **Missing**: Learning which vendors/formats work with which method

### Alternatives

#### A. Template Learning
- After 10 invoices from same vendor, detect if it's templated
- Route templated invoices directly to OCR
- **Pros**: [TBD]
- **Cons**: [TBD]

#### B. Machine Learning Router
- Train classifier on image features → predict best extraction method
- **Pros**: [TBD]
- **Cons**: [TBD]

#### C. Multi-Model Parallel
- Run OCR + Vision in parallel, choose best result
- **Pros**: [TBD]
- **Cons**: [TBD]

#### D. Adaptive Thresholds
- Per-vendor confidence thresholds based on historical accuracy
- **Pros**: [TBD]
- **Cons**: [TBD]

### Recommendation
[TBD]

---

## 6. IMPLEMENTATION ROADMAP

### Immediate (This Week)
- [TBD]

### Short-Term (Next Month)
- [TBD]

### Production (3-6 Months)
- [TBD]

---

## 7. TECHNOLOGY COMPARISON MATRIX

| Technology | Reliability | Accuracy | Speed | Cost | Complexity | Best For |
|------------|-------------|----------|-------|------|------------|----------|
| **Current: Qwen2.5vl:7b** | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| llama3.2-vision:11b | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| Claude Haiku API | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| AWS Textract | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| Azure Doc Intelligence | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |

---

## NOTES FOR BUILDERTREND INTERVIEW

### What Makes This Production-Ready
- [TBD]

### Where We'd Invest Next
- [TBD]

### Red Flags We're Avoiding
- [TBD]
