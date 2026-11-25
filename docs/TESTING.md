# AI Grama Sahayak — Testing & Verification Report

This document records the automated testing architecture, latest verified test metrics, and exact procedures to reproduce verification results for the AI Grama Sahayak Level 1 prototype.

---

## 1. Summary of Latest Verified Test Execution (Phase 6C.2)

All automated suites pass with zero failures and zero regressions:

| Test Suite | Tests Executed | Passed | Skipped | Failed | Execution Time |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend Integration Suite** (`backend/tests`) | 330 | 325 | 5 | 0 | ~43.1 s |
| **Root Regression Suite** (`tests`) | 65 | 65 | 0 | 0 | ~2.0 s |
| **Frontend Voice Unit Tests** (`voiceUtils.test.mjs`) | 10 | 10 | 0 | 0 | ~17 ms |
| **Frontend Privacy Unit Tests** (`savedQuestions.test.mjs`) | 8 | 8 | 0 | 0 | ~13 ms |
| **Consolidated Automated Executions** | **413** | **408** | **5** | **0** | **~45 s** |

> [!NOTE]
> The 19 physical acceptance regression tests in `backend/tests/test_physical_acceptance_phase6c.py` are executed as part of the `backend/tests` suite (325 passed total). They are not counted twice.
> The 5 skipped tests correspond to mock placeholder deprecations for components that are now fully integrated in the monolithic router.

### Static Analysis & Build Status
- **ESLint (`npm run lint`):** 0 errors, 0 warnings.
- **TypeScript & Next.js Build (`npm run build`):** Compiled successfully via Turbopack with zero errors. All routes prerendered cleanly.

---

## 2. Retrieval Evaluation Benchmark

The knowledge retrieval engine is benchmarked against `knowledge_base/evaluation_dataset.json`, comprising 24 hand-curated public service queries across all four target domains.

```
Total Evaluation Queries:         24
  - Positive Benchmark Queries:   22
  - Negative Benchmark Queries:    2
Hit Rate @ 1:                     100.0% (22/22)
Hit Rate @ 3:                     100.0% (22/22)
Mean Reciprocal Rank (MRR):       1.000
Negative Rejection Accuracy:      100.0% (2/2)
Cross-Domain Leakage Violations:  0
```

> [!IMPORTANT]
> **Scope Disclaimer:** These retrieval metrics validate the precision and domain boundaries of the retrieval engine against the 24 evaluation test cases in the benchmark dataset. They do not constitute universal factual correctness across arbitrary real-world queries.

---

## 3. How to Reproduce All Test Results

Run the following commands in Windows PowerShell from the repository root:

### 3.1 Run Backend Integration Tests
```powershell
backend\.venv\Scripts\python -m pytest -c backend/pytest.ini backend/tests -q -rs
```

### 3.2 Run Root Regression Tests
```powershell
backend\.venv\Scripts\python -m pytest tests -q -rs
```

### 3.3 Run Targeted Physical Acceptance Suite (Includes Telugu OCR)
```powershell
backend\.venv\Scripts\python -m pytest backend/tests/test_physical_acceptance_phase6c.py -v
```

### 3.4 Run Retrieval Quality Benchmark
```powershell
backend\.venv\Scripts\python -c "
import sys; sys.path.insert(0, 'backend')
from app.services.retrieval.evaluator import RetrievalEvaluator
evaluator = RetrievalEvaluator()
metrics = evaluator.run_evaluation()
import json
print(json.dumps({k: v for k, v in metrics.items() if k != 'detailed_results'}, indent=2))
"
```

### 3.5 Run Frontend Unit Tests
```powershell
node frontend/src/services/voiceUtils.test.mjs
node frontend/src/services/savedQuestions.test.mjs
```

### 3.6 Run Frontend Linter and Production Build
```powershell
npm --prefix frontend run lint
npm --prefix frontend run build
```
