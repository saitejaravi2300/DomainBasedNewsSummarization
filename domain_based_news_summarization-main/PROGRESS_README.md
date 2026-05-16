# Project Progress and Detailed Roadmap

Last updated: 2026-04-13

## 1) Project Snapshot

This project is currently in a strong prototype stage with working end-to-end functionality:
- Backend digest generation, clustering, scoring, and user APIs are implemented.
- Frontend dashboard, saved trends, and custom-domain workflows are functional.
- A new ML workspace (`ml-lab/`) has been created to shift toward a trust-first NLP pipeline and model-assisted ranking.

Current maturity (practical):
- Product functionality: strong
- Data trust and consistency: improving, but still the top focus
- Demo-readiness: good with recent fixes, better after confidence/evidence UI is added

---

## 2) What Has Been Completed So Far

## 2.1 Backend digest quality and reliability

Implemented and improved:
- Text cleaning and normalization hardening for noisy feed content.
- Better summary/TLDR generation quality and deduplication logic.
- Improved timeline event cleaning.
- So-What generation quality improved from generic to more context-aware output.
- Domain-specific filtering and relevance gating refinements.

Stability and correctness upgrades:
- Silent fake fallback behavior was changed.
- By default, digest generation now returns an explicit service error when live data generation fails instead of showing misleading mock trends.
- Mock fallback can be enabled explicitly via `ALLOW_MOCK_FALLBACK=true` when needed for controlled demos.

Source/link trust upgrades:
- Source identity logic now prefers URL host-based identity to reduce duplicate-source inflation.
- Invalid article links are sanitized and excluded from clickable links in output.

---

## 2.2 Frontend behavior and UX fixes

Implemented and verified:
- Domain-switch stale content bug fixed.
- Per-domain + time-range digest state restore behavior added.
- Saved trends moved from mock behavior to persistent backend-backed behavior.
- Saved trends runtime crash on malformed item shape fixed with normalization/filtering.
- Custom domain deletion flow added (UI + API + backend).
- Source link rendering improved to avoid clickable broken links.
- API error surfacing improved so users see actionable backend failure details.

---

## 2.3 Persistence and API layer updates

Implemented:
- Saved trend persistence APIs: save/list/delete with auth checks.
- Custom domain persistence updates, including delete endpoint.
- Frontend API proxy routes aligned with backend behavior and error passthrough.

---

## 2.4 Validation and test runs completed

Validation methods used:
- Docker rebuild and runtime checks.
- API-level verification via scripts/terminal.
- Browser-level checks for major user journeys.

Verified outcomes:
- Domain switching no longer shows stale digest snapshots.
- Saved trends can be added/loaded/deleted against persistence layer.
- Custom domain delete endpoint works and updates UI correctly.

---

## 2.5 New ML foundation started (`ml-lab`)

Created and validated:
- `ml-lab/requirements.txt`
- `ml-lab/config/domain_keywords.json`
- `ml-lab/src/deduplicate.py`
- `ml-lab/src/baseline_pipeline.py`
- `ml-lab/src/train_relevance_classifier.py`
- `ml-lab/src/evaluate_baseline.py`
- `ml-lab/README.md`

Pipeline capabilities added:
- Baseline deterministic pipeline:
  - cleaning
  - keyword relevance filtering
  - deduplication
  - clustering
  - ranking
  - extractive summary
- Lightweight classifier training script:
  - TF-IDF + Logistic Regression
  - macro-F1 report output
- Baseline evaluator script:
  - trust metrics (link validity, unique publisher ratio, etc.)

Schema compatibility added:
- Baseline pipeline now supports top-level `jobs` dataset shape and maps job records into article-like text format for experimentation.

---

## 3) Most Recent Execution Results

Run status:
- Baseline pipeline execution: success
- Input dataset: `C:\Users\varun\Careerpath\Careerpath\data\datasets\management_jobs_dataset_v2.json`
- Summary result:
  - Input records: 96
  - After filter: 30
  - After dedup: 30
  - Trends: 5

Evaluation output:
- `total_trends`: 5
- `total_surface_articles`: 20
- `valid_link_ratio`: 0.0
- `avg_unique_publisher_ratio`: 0.240238...

Interpretation:
- These low trust-link/source metrics are expected for this specific dataset because it is a jobs/career catalog, not a real news feed with publisher URLs.

---

## 4) Current Known Gaps

1. No trained relevance model integrated in live backend path yet.
2. No confidence/evidence panel in frontend trend cards yet.
3. No explicit dataset mode separation in UI/reporting (jobs-like vs news-like).
4. Quality metrics dashboard is file-based only (not surfaced in product UI).
5. Near-duplicate detection can be further strengthened with semantic similarity pass.

---

## 5) Detailed Plan (What We Are Planning To Do)

## Phase A: Trust-first data pipeline hardening (Immediate)

Goals:
- Ensure each trend is explainable and source-grounded.

Tasks:
1. Add dataset mode support (`jobs`, `news`) in pipeline outputs and evaluation logic.
2. Add stricter dedup strategy:
   - normalized URL identity
   - title hash identity
   - optional semantic near-duplicate threshold
3. Add per-trend trust features:
   - unique publisher count
   - duplicate ratio
   - valid-link ratio
   - average relevance score
4. Emit a structured `trend_confidence` score in pipeline output.

Deliverables:
- Updated baseline output schema with trust fields.
- Updated evaluator with mode-aware thresholds.

Success criteria:
- No source-count inflation for duplicate/same-host stories.
- Deterministic confidence scoring reproducible across runs.

---

## Phase B: Lightweight relevance model training (High priority)

Goals:
- Improve domain relevance precision before clustering.

Tasks:
1. Build labeled training set from available records (domain labels).
2. Train baseline classifier using existing script.
3. Record macro-F1, per-class precision/recall, confusion matrix.
4. Calibrate confidence threshold for inclusion in digest generation.
5. Save model artifact and metadata version (`artifacts/relevance_model.joblib`).

Deliverables:
- Versioned model + evaluation report.
- Threshold recommendation for production inference.

Success criteria:
- Macro F1 >= 0.75 (initial target)
- False-positive reduction in irrelevant cluster inclusion.

---

## Phase C: Backend integration of model scoring

Goals:
- Use trained relevance model in article filtering path.

Tasks:
1. Add model loader on backend startup.
2. Score each candidate article with model probability.
3. Blend lexical + model relevance into final rank score.
4. Add fallback behavior when model artifact unavailable.
5. Add telemetry fields in digest response:
   - `relevance_model_version`
   - `avg_model_confidence`

Deliverables:
- Backend digest path with model-assisted ranking.
- Backward-compatible API response.

Success criteria:
- Better relevance consistency across custom domains.
- Reduced repeated irrelevant trend output.

---

## Phase D: Frontend redesign around confidence and evidence

Goals:
- Make trust visible and demo-safe.

Tasks:
1. Add confidence badge per trend (High/Medium/Low).
2. Add evidence row per trend:
   - unique sources
   - total articles
   - duplicate ratio
   - link validity
3. Add warning chips:
   - low-source confidence
   - possible duplicates
   - insufficient evidence
4. Add expandable “Why this trend?” section listing top signals.

Deliverables:
- Updated trend card UI and dashboard summary strip.

Success criteria:
- Users can immediately identify weak trends.
- Demo reviewers can audit trend trust without backend logs.

---

## Phase E: Evaluation and benchmarking layer

Goals:
- Quantify progress in a repeatable way.

Tasks:
1. Add benchmark script that compares baseline vs model-assisted outputs.
2. Track KPI table over runs:
   - relevance precision proxy
   - duplicate ratio
   - source diversity
   - confidence distribution
3. Store run artifacts per experiment ID.

Deliverables:
- `artifacts/benchmarks/*.json`
- simple experiment log markdown.

Success criteria:
- Clear measurable improvement from baseline to model-assisted pipeline.

---

## 6) Immediate Next Actions (Recommended Order)

1. Implement dataset mode separation in `ml-lab` outputs and evaluator.
2. Generate first labeled set from existing domain field and train v1 relevance model.
3. Integrate v1 model into backend digest scoring behind a feature flag.
4. Add confidence/evidence badges in frontend trend cards.
5. Run one complete end-to-end comparison demo with before/after metrics.

---

## 7) Command Reference

From `ml-lab` directory:

```powershell
python src\baseline_pipeline.py --input "C:\Users\varun\Careerpath\Careerpath\data\datasets\management_jobs_dataset_v2.json" --domain finance --top-k 20 --output artifacts\baseline_output.json
python src\evaluate_baseline.py --input artifacts\baseline_output.json --output artifacts\metrics.json
python src\train_relevance_classifier.py --input "path\to\labeled_news.json" --text-fields title description content --label-field domain --output-dir artifacts
```

---

## 8) Notes for Presentation

When presenting to faculty:
- Emphasize that the roadmap is trust-first, not just model-first.
- Show measurable metrics before and after model integration.
- Explain why source evidence and confidence transparency were prioritized.
- Clarify dataset differences (jobs dataset vs live news dataset) when interpreting metrics.
