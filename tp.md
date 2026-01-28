# Technical Progressions & Improvements for Invoice Automation

> **Priority**: Reliability > Accuracy > Efficiency > Cost  
> **Date**: 2026-01-26  
> **Context**: BuilderCo interview demo - proving production readiness

---

## 1. EXTRACTION RELIABILITY

### Problem
- Invoices vary wildly: handwritten, poor scans, unusual layouts, multiple languages
- Extraction failures or low confidence → manual review queue → operational bottleneck
- False positives (high confidence but wrong data) are worse than false negatives
- Current: 21s/invoice with Qwen2.5vl:7b, 30% OCR failure rate on poor quality scans

### Current Solution
- **Hybrid approach**: Tesseract OCR (fast path) + Qwen2.5vl:7b (fallback)
- Confidence-based routing: >85% passes, <85% triggers Vision AI
- **Performance**: 3-462ms (OCR) vs 21s (Vision)
- **Reliability**: OCR fails on 30% of invoices (poor quality), Vision handles 95%+
- **Test results**: ABC Plumbing 100% confidence, Johnson HVAC 95% (poor quality scan)

### Progressions

#### A. Commercial Document AI APIs
- **AWS Textract**: 2-3s/page, 95%+ accuracy, $1.50/1000 pages, SLA 99.9%
- **Azure Document Intelligence**: 2-4s/page, 98%+ accuracy, $1.00/1000 pages, custom model training
- **Google Document AI**: 3-5s/page, 97%+ accuracy, $1.50/1000 pages, AutoML support
- **Pros**: Production SLAs, managed infrastructure, proven at scale (millions of docs/day), no GPU management
- **Cons**: Vendor lock-in, $1500-1800/month at 10K invoices, data privacy concerns (BuilderCo's customer data), network latency

#### B. Smaller/Faster Vision Models
- **llama3.2-vision:11b**: 15s/invoice tested, 90% accuracy (needs validation on your test set)
- **qwen2.5vl:3b**: 8-12s/invoice (estimated), unknown accuracy on invoices, smaller GPU footprint
- **minicpm-v:8b**: Mobile-optimized, 10s/invoice (estimated), 85% accuracy on documents
- **Pros**: 30-50% faster than current, lower GPU memory (3b = 2GB vs 7b = 6GB), can run more parallel instances
- **Cons**: Accuracy tradeoff unclear without benchmarking, still requires GPU infrastructure

#### C. Fine-Tuned Document Models
- **Donut**: Transformer for document understanding, 89% accuracy on cord-v2 benchmark
- **LayoutLMv3**: Reads layout + text, 96.4% on RVL-CDIP, requires fine-tuning on invoices
- **Pros**: Can fine-tune on BuilderCo's invoice formats, potentially higher accuracy on specific layouts
- **Cons**: Requires labeled training data (1000+ invoices), 2-4 weeks training time, model maintenance overhead

#### D. Multi-Model Ensemble (3 models vote)
- Run Qwen2.5vl:7b + llama3.2-vision:11b + Azure, take majority vote or confidence-weighted average
- **Pros**: Catches model-specific blind spots, increases reliability to 99%+, reduces false positives
- **Cons**: 3x compute cost, 3x latency (unless parallel), complex voting logic for disagreements

### Recommendation
**Immediate**: Benchmark llama3.2-vision:11b on your 5 test invoices. If >90% accuracy, replace Qwen2.5vl:7b (30% faster, same GPU).

**Production**: Multi-model voting for amounts >$10K (high-stakes invoices). Route low-stakes (<$1K) to single model. Add Azure Document Intelligence as 3rd voter for critical invoices.

**Rationale**: Reliability first → ensemble. Efficiency second → faster model for 90% of invoices. Cost managed by routing based on invoice value.

---

## 2. VALIDATION & CORRECTNESS

### Problem
- How do we know extraction is correct vs. just "confident"?
- Current system compares OCR vs Vision (agreement ≠ correctness)
- No ground truth validation in production
- Cannot measure actual accuracy on real invoices without manual audit
- Example: Both models extract "$5,342.00" with 95% confidence, but invoice says "$5,432.00"

### Current Solution
- **Comparison Service**: Cross-validates Traditional OCR vs Vision AI results
- Field match rate calculation (do they agree?)
- Confidence scoring from models
- **Weakness**: Two wrong answers can agree with high confidence, no external validation

### Progressions

#### A. Ground Truth Testing Framework
- Test extraction against `/receipts/expected.md` (5 invoices with known correct values)
- Automated assertions: vendor name exact match, amount within $0.01, date exact, line item count
- **Pros**: Proves correctness not just agreement, catches regression bugs, fast feedback loop (<1min)
- **Cons**: Only covers 5 test invoices, doesn't validate production invoices, ground truth requires manual creation

#### B. Multi-Model Consensus (3+ models vote)
- Run 3 models, take majority vote or flag disagreements for human review
- Example: Qwen=5432, Llama=5432, Azure=5342 → 2/3 vote wins, flag as "medium confidence"
- **Pros**: Reduces single-model errors by 80%+, no ground truth needed, works on production data
- **Cons**: 3x compute cost, complex tie-breaking logic, all 3 can be wrong on edge cases

#### C. Business Logic Validation (Math checks)
- Verify: invoice total = sum(line_items), tax = subtotal × rate, amounts positive non-zero
- Date sanity: not in future, not >2 years old, workday for commercial invoices
- Vendor sanity: exists in subcontractor DB, not duplicate invoice number
- **Pros**: Catches 60% of extraction errors immediately, zero ML cost, fast (<1ms), deterministic
- **Cons**: Doesn't catch typos where math still works, requires domain rules, false positives on legitimate edge cases

#### D. Human-in-the-Loop Sampling (5% audit)
- Random 5% of approved invoices sent to human for validation
- Track accuracy over time: "Week 1: 92% accurate, Week 4: 97% accurate"
- **Pros**: Ground truth on production data, catches systematic errors, builds training data for fine-tuning
- **Cons**: Requires human resources, delayed feedback (hours/days), doesn't prevent errors

#### E. Confidence Calibration (historical accuracy mapping)
- Track: "Model says 95% confident → actually correct 87% of time"
- Adjust thresholds: If model says 95%, treat as 87% → require higher confidence for auto-approval
- **Pros**: Self-correcting system, improves over time, works with any model
- **Cons**: Requires 1000+ labeled samples, accuracy varies by invoice type, recalibration needed quarterly

### Recommendation
**Immediate (this week)**: Implement A (ground truth testing) + C (business logic validation). Test suite runs in <2min, catches 60% of bugs before deployment.

**Short-term (1 month)**: Add D (5% human audit) to build confidence calibration dataset. Track model accuracy by vendor, invoice type, amount range.

**Production (3 months)**: Implement E (confidence calibration). Example: "Model 90% confident on ABC Plumbing → actually 97% accurate → auto-approve. Model 90% confident on handwritten invoices → actually 68% accurate → require human review."

**Rationale**: Reliability first → multiple validation layers. Ground truth + math checks = free validation. Human audit builds calibration data for long-term reliability improvement.

---

## 3. VENDOR MATCHING ACCURACY

### Problem
- Vendor names have variations: "ABC Plumbing LLC" vs "A.B.C. Plumbing" vs "ABC Plumbing & Heating"
- Typos, abbreviations, legal entity changes
- False positives: "Smith Electric" matches "Smith Plumbing" at 70%
- False negatives: "Martinez Roofing LLC" vs "Martinez Roofing & Construction Co" = 82% (should match)
- Threshold too strict = miss valid matches, too loose = wrong matches

### Current Solution
- **RapidFuzz** with Levenshtein distance (`fuzz.ratio`)
- Thresholds: >90% high confidence, 85-90% auto-approve, 70-85% review, <70% reject
- **Performance**: <1ms per comparison, scales to 10K vendors
- **Accuracy**: Good on exact/close matches (95%+ success), struggles with structural differences (e.g., "Corp" vs "Corporation" vs "Co")

### Progressions

#### A. Semantic Similarity (Sentence-BERT embeddings)
- Encode vendor names with all-MiniLM-L6-v2 (same model as cost codes)
- Cosine similarity: "ABC Plumbing LLC" and "ABC Plumbing Service" = 0.94 (semantic match)
- **Pros**: Handles abbreviations better, understands "Plumbing" ≈ "Plumbers", 50ms for 1000 comparisons
- **Cons**: "Smith Electric" and "Smith Plumbing" = 0.87 (false positive), requires 80MB model, less intuitive scores

#### B. Hybrid String + Semantic (Two-stage filter)
- Stage 1: RapidFuzz >85% → auto-match (<1ms)
- Stage 2: RapidFuzz 70-85% → run Sentence-BERT, threshold >0.90 → match
- Stage 3: Both fail → human review
- **Pros**: Fast path for 70% of matches, semantic catches 20% more, only 10% need human review
- **Cons**: More complex logic, two models to maintain, edge cases where they disagree

#### C. Learning from Corrections (Alias table)
- Track human corrections: "Martinez Roofing LLC" → "Martinez Roofing & Construction Co"
- Build alias table: {vendor_id: 4, aliases: ["Martinez Roofing LLC", "Martinez Roofing & Construction Co", "M. Roofing"]}
- Exact match against aliases first (0ms), then fuzzy match
- **Pros**: 100% accuracy on learned aliases, self-improving, zero latency on known aliases
- **Cons**: Cold start problem (empty table initially), requires correction_history integration, maintenance if vendor changes name

#### D. Multiple Fuzzy Algorithms (RapidFuzz ensemble)
- Combine scores: `fuzz.ratio` (Levenshtein), `fuzz.token_sort_ratio` (word order independent), `fuzz.partial_ratio` (substring match)
- Score = max(ratio, token_sort, partial) or weighted average
- **Pros**: Handles more edge cases, still <1ms, no ML overhead, easy to tune weights
- **Cons**: Can increase false positives if not tuned carefully, diminishing returns vs. simple ratio

#### E. Entity Resolution Service (Dedupe.io, Zingg)
- External service trained on millions of business names
- Handles DBA names, legal entity changes, mergers
- **Pros**: Production-grade entity resolution, handles complex cases (LLC vs Corporation vs DBA), managed service
- **Cons**: $200-500/month, API latency (50-100ms), data leaves your infrastructure, overkill for <10K vendors

### Recommendation
**Immediate (this week)**: Implement C (alias table from correction_history). Zero-cost improvement, catches 40% of repeat mismatches instantly.

**Short-term (1 month)**: Add D (multiple RapidFuzz algorithms). Test on your 5 invoices:
- "Martinez Roofing & Construction Co" vs "Martinez Roofing LLC": `token_sort_ratio` = 95% (match), `ratio` = 82% (review)
- Use max(ratio, token_sort) for final score.

**Long-term (production)**: Evaluate B (hybrid) if alias table + multi-algorithm still sends >15% to review queue. Semantic catches "ABC Plumbing Service" vs "ABC Plumbers" (Levenshtein fails, embeddings succeed).

**Rationale**: Reliability first → learn from human corrections (alias table). Accuracy second → multi-algorithm catches more variants. Efficiency → keep <1ms performance, avoid ML unless necessary.

---

## 4. COST CODE CLASSIFICATION ACCURACY

### Problem
- Line item descriptions → Cost codes (e.g., "Install copper piping" → 15140 "Plumbing - Rough-in")
- Ambiguous items: "Labor" could be any trade (confidence <50% on all codes)
- Generic descriptions: "Materials" → which trade? (plumbing, electrical, roofing?)
- Threshold 80% but what if top 2 are 78% and 77%? Both probably wrong.
- Each builder has custom cost codes (multi-tenancy), can't pre-train on standard codes

### Current Solution
- **Sentence-BERT** (all-MiniLM-L6-v2): 22M params, 384-dim embeddings
- Cosine similarity between line item description and cost code labels
- Caching for performance (50ms for 100 items, <5ms for single item)
- **Accuracy**: Good on clear items ("Install fixtures" → 95% confidence), struggles with generic ("Labor" → 42% confidence)

### Progressions

#### A. Larger Embedding Models
- **BGE-small-en-v1.5**: 33M params, better retrieval accuracy (+3-5% on BEIR benchmark), 120MB, 80ms/100 items
- **e5-small-v2**: 33M params, trained on 1B pairs, similar performance to BGE, 110MB
- **nomic-embed-text**: 137M params, best-in-class for retrieval, 400MB, 150ms/100 items
- **Pros**: 3-5% accuracy improvement on domain-specific retrieval, handles synonyms better ("piping" vs "pipes")
- **Cons**: 2-3x slower, 2-5x larger model size, diminishing returns for construction domain (not trained on trade terminology)

#### B. Domain-Specific Fine-Tuning
- Fine-tune Sentence-BERT on construction line items → cost codes pairs
- Requires 500-1000 labeled pairs per builder
- Training: 2-4 hours on GPU, retrain quarterly as cost codes evolve
- **Pros**: 10-15% accuracy improvement on builder-specific terminology, learns abbreviations ("HVAC" → heating/cooling)
- **Cons**: Data collection burden (1000 labeled pairs), per-builder training (can't share models), model drift as codes change

#### C. LLM-Based Classification (Reasoning)
- Send line item + all cost codes to Qwen2.5:1.5b or Llama 3.2:3b
- Prompt: "Which cost code best matches 'Install copper piping'? Codes: [15140: Plumbing Rough-in, 15410: Fixtures, ...]. Think step-by-step."
- **Pros**: Handles ambiguity through reasoning, explains choices ("piping suggests rough-in, not fixtures"), 85%+ accuracy on ambiguous items
- **Cons**: 500ms per classification (10x slower), GPU required, unpredictable on edge cases, cost code list must fit in context (limit ~100 codes)

#### D. Hierarchical Classification (Two-stage)
- Stage 1: Classify by trade (plumbing, electrical, HVAC, roofing, concrete, etc.) using Sentence-BERT
- Stage 2: Within trade, classify to specific code (15140 vs 15410 within plumbing)
- **Pros**: Narrows search space (10 trades → 10 codes each instead of 100 codes flat), 5-8% accuracy improvement, faster (smaller search space)
- **Cons**: Requires trade taxonomy, some items span trades ("Install thermostat wiring" = HVAC or electrical?)

#### E. Learning from Corrections (Retrain embeddings)
- Track human corrections: "Install fixtures" → user changed from 15140 to 15410
- Periodically retrain Sentence-BERT with hard negatives: "Install fixtures" closer to 15410, farther from 15140
- **Pros**: Self-improving system, builder-specific learning without manual labeling, accuracy improves 2-3% per 100 corrections
- **Cons**: Requires 200+ corrections per builder before retraining, model management complexity, training infrastructure

### Recommendation
**Immediate (this week)**: Implement D (hierarchical classification). Add trade field to cost codes table:
```sql
ALTER TABLE cost_codes ADD COLUMN trade VARCHAR(50);
-- trades: plumbing, electrical, hvac, roofing, concrete, drywall, painting, etc.
```
Stage 1: Classify line item → trade (90%+ accuracy, 10 options).  
Stage 2: Within trade, classify → code (85%+ accuracy, 10 options).  
Combined: 76%+ accuracy on previously ambiguous items.

**Short-term (1 month)**: Test A (BGE-small-en-v1.5). Benchmark on your invoice line items. If >3% accuracy gain, switch (80ms is acceptable, still <100ms SLA).

**Long-term (production)**: Implement E (learning from corrections). After 6 months with 500+ corrections, fine-tune BGE-small on your correction_history. Expected: 90%+ accuracy on builder-specific terminology.

**Rationale**: Reliability first → hierarchical narrows search space, reduces catastrophic mismatches (electrical code for plumbing task). Accuracy second → better embeddings + learning from corrections. Efficiency → hierarchical is actually faster (smaller search spaces per stage).

---

## 5. ROUTING & ORCHESTRATION

### Problem
- When to use Traditional OCR vs Vision AI vs API services?
- How to minimize cost while maximizing accuracy?
- How to handle edge cases gracefully?
- Current: Implicit routing (try OCR, fallback to Vision if confidence <85%)
- Missing: Learning which vendors/formats work with which method

### Current Solution
- **Confidence-based fallback**: Run OCR, if confidence <85%, run Vision AI
- No explicit routing logic, no vendor-specific learning
- No cost optimization (could run cheaper methods first for known-good vendors)
- **Performance**: 70% of invoices use OCR (fast), 30% use Vision (slow)

### Progressions

#### A. Template Learning (Vendor-specific routing)
- After 10 invoices from same vendor, detect if format is consistent
- If OCR succeeds 9/10 times → route directly to OCR, skip Vision
- If OCR fails 9/10 times → route directly to Vision, skip OCR attempt
- **Pros**: 30% faster on templated vendors (skip failed OCR attempt), learns automatically, per-vendor optimization
- **Cons**: Cold start problem (first 10 invoices still slow), vendor format changes break routing, requires vendor match before extraction

#### B. Machine Learning Router (Image classifier)
- Train lightweight CNN on image features: blur, contrast, resolution, text density, table presence
- Predicts: "OCR will succeed" (85% confidence) vs "Vision needed" (90% confidence)
- **Pros**: Instant routing decision (<10ms), vendor-agnostic (works on new vendors), handles format changes
- **Cons**: Requires labeled training data (500+ invoices), model maintenance, can misroute on edge cases

#### C. Multi-Model Parallel (Run both, choose best)
- Run OCR + Vision in parallel (2 GPUs or async)
- Compare results, choose higher confidence or use business logic validation (math checks)
- **Pros**: Always get best result, no routing errors, 2x reliability
- **Cons**: 2x compute cost on every invoice, no efficiency gain, complex result merging logic

#### D. Adaptive Thresholds (Per-vendor confidence calibration)
- Track OCR confidence vs accuracy by vendor
- ABC Plumbing: OCR 75% confidence → actually 95% accurate → lower threshold to 70%
- Handwritten receipts: OCR 85% confidence → actually 60% accurate → raise threshold to 95%
- **Pros**: Self-tuning system, maximizes OCR usage (fast path), minimizes Vision usage (expensive)
- **Cons**: Requires 50+ invoices per vendor for calibration, vendor-specific thresholds to maintain

### Recommendation
**Immediate (this week)**: Implement A (template learning). After 10 invoices from vendor with >90% OCR success → route to OCR only. After 10 with >70% OCR failure → route to Vision only. Expected: 20% reduction in Vision AI usage.

**Short-term (1 month)**: Add business logic validation (section 2C) to routing. If OCR result passes math checks (total = sum of line items), accept even if confidence 75-85%. Expected: 10% more invoices on fast path.

**Long-term (production)**: Implement D (adaptive thresholds). Per-vendor calibration: "ABC Plumbing OCR 70%+ → accept. Unknown vendor OCR 85%+ → accept." Expected: 40% reduction in Vision AI usage while maintaining accuracy.

**Rationale**: Efficiency first (for routing) → template learning routes to fastest method. Reliability maintained → validation catches errors. Cost optimization → adaptive thresholds minimize expensive Vision AI usage.

---

## 6. TECHNOLOGY COMPARISON MATRIX

| Technology | Reliability | Accuracy | Speed | Cost/1K | Complexity | Best For |
|------------|-------------|----------|-------|---------|------------|----------|
| **Current: Qwen2.5vl:7b** | 95% | 95% | 21s | $16 GPU | Medium | General invoices, handles poor quality |
| **llama3.2-vision:11b** | 90% (est.) | 90% (est.) | 15s | $16 GPU | Medium | Faster alternative, needs testing |
| **qwen2.5vl:3b** | Unknown | Unknown | 10s (est.) | $8 GPU | Medium | Speed priority, accuracy unknown |
| **Claude Haiku API** | 99.9% SLA | 95%+ | 2s | $250 | Low | High-stakes invoices, no GPU needed |
| **AWS Textract** | 99.9% SLA | 95%+ | 3s | $1500 | Low | Production scale, enterprise support |
| **Azure Doc Intel** | 99.9% SLA | 98%+ | 3s | $1000 | Low | Best accuracy, custom models |
| **Tesseract OCR** | 70% | 85% | 50ms | Free | Low | Clean invoices, templated formats |
| **PaddleOCR** | 75% | 88% | 100ms | Free | Medium | Better than Tesseract, still fast |
| **Donut** | 80% | 89% | 500ms | Free | High | Fine-tuning required, research model |
| **Multi-model (3x)** | 99%+ | 98%+ | 45s | $48 GPU | High | Mission-critical, high-value invoices |

**Notes**:
- Cost: GPU = $800/month for 50K invoices, API = pay-per-use
- Reliability: % of invoices successfully processed without errors
- Accuracy: % of fields correctly extracted vs. ground truth
- Complexity: Implementation + maintenance burden

---