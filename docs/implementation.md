# SoilAI implementation and verification record

The repository is a functioning agricultural records application under development. It is not the completed twelve-phase enterprise platform. The user explicitly authorized keeping predictions unavailable until verified public data and models are validated. After reaching that scientific gate, independent dashboard/report/deployment work continued. No phase requiring ML is described as complete.

## Phase 1 - setup and startup

Created the full requested directory structure; React 19/TypeScript/Vite/Tailwind configuration; FastAPI application; environment templates; Windows setup/start scripts; Docker build files and Nginx proxy. Installed Python and Node dependencies. Both dev servers returned HTTP 200. TypeScript and production builds passed. Local development uses frontend 5173, backend 8000 and PostgreSQL 5433 (5432 was already occupied).

## Phase 2 - database and authentication

Implemented 24 application tables plus Alembic, foreign keys, indexes, uniqueness/check constraints, immutable version-0001 PostgreSQL schema snapshot, registration, login, Argon2 hashes, access JWTs tied to revocable sessions, refresh rotation with row locks and replay revocation, logout, profile, session listing/revocation, forgot/reset password and role enforcement. Registration always assigns FARMER. Administrator bootstrap is interactive, with no default password. Migrations applied to PostgreSQL 17. Authentication tests passed on SQLite and PostgreSQL. Reset tests cover one-use tokens and session revocation. SMTP delivery requires configuration and remains unverified against a mail server.

## Phase 3 - farm and soil records

Implemented farm creation/editing/soft deletion, multiple fields, field API editing, farm-scoped permissions, sample creation/editing/history, drafts, all nine primary and eight optional parameters, per-measurement units/methods, future-date and numeric/type checks, field/farm membership checks, and officer reviews. React pages connect to these APIs. Farmers see their own records; officers see assigned farms and can add remarks without editing measurements. Validation/isolation tests passed on SQLite and PostgreSQL. Browser QA registered an account, created a farm and submitted all nine measurements through React to PostgreSQL in a disposable schema.

## Phase 4 - CSV and Excel imports

Implemented UTF-8 CSV and single-sheet XLSX upload, header detection, preview, canonical-column mapping, explicit units/methods (shared or per row), missing/invalid value checks, duplicate detection within a file and database, error CSV, history, confirmation and atomic database import. Files are limited to 5 MiB, 5,000 rows and 100 columns; decompressed workbook limits protect against expansion attacks. Validation is repeated under a row lock before confirmation. Race conflicts roll back the entire import. API tests cover successful import, invalid headers, missing units, unsupported extensions, oversized files, duplicate records, re-confirmation and XLSX content checks. All 11 tests through this phase passed on SQLite and PostgreSQL. Bulk prediction processing is unavailable under the scientific gate.

## Phase 5 - public data and preprocessing (partial)

Reviewed original public source pages and wrote a source register with licence, geography, target, limitations and exact manual-download instructions. Mendeley's public metadata API returned HTTP 403; Kaggle's primary page was not text-readable. ISRIC's own documentation advises against farm-level use of SoilGrids. No compatible public dataset with independently valid fertility labels, known laboratory methods/units and Indian regional evaluation has been accepted.

Implemented a deterministic CSV/provenance audit producing SHA-256, data dictionary checks, missing values, duplicates, class balance, numeric bounds, summary statistics, IQR outlier counts, target leakage checks and group/region gates. A test verifies rejection of unknown units and crop labels used as fertility targets. Actual public-dataset cleaning and EDA cannot be marked complete without an accepted downloaded dataset.

## Phase 6 - training (not implemented)

No models have been trained or persisted. Model comparison, tuning, cross-validation, SHAP, nutrient regression, clustering and monitoring are pending. No performance metrics are fabricated. `machine_learning/README.md` and the dataset guide state the gate and requirements.

## Phase 7 - model serving and interpretation (not complete)

Authenticated fertility/crop availability routes check sample ownership and completeness, then return HTTP 503 with `MODEL_NOT_VALIDATED`. Missing crop climate/season/irrigation context returns HTTP 422. These are explicit availability guards, not working prediction endpoints. No universal soil-health score or unsupported agronomic ranges are computed. Actual inference, explanations and verified nutrient interpretations remain pending.

## Phase 8 - crop and fertilizer engines (not implemented)

No unsupported crops or fertilizer dosages are recommended. Crop/fertilizer result tables and authorized retrieval APIs exist, but the engines require validated scientific data and agronomic guidance. The project does not claim these acceptance criteria.

## Phase 9 - dashboards and administration (partial)

Implemented database-derived farm/sample/submission/analysis counts, recent samples, measurement history, fertility distribution from stored predictions, activity and quick actions. The chart separates incompatible units and laboratory methods. Zero/unavailable states reflect actual empty records. Administrator pages/API provide user roles/activation, officer assignment, system counts, model registry readout and audit logs. Permission changes revoke user sessions. Officer farm visibility and review controls are tested. Dataset management, controlled background training jobs, production-model approval/activation, prediction monitoring and configurable permission/settings management remain pending.

## Phase 10 - languages and reports (partial)

Separate i18next English/Tamil JSON dictionaries cover standard navigation, form labels, dashboard/report labels and common actions. Language switching retains unsaved form values (automated test). Some dynamic server validation messages, laboratory metadata and administrative wording remain English; complete bilingual acceptance is not claimed.

Implemented authenticated PDF and Excel laboratory-record snapshots, download ownership checks, printing, model-availability limitations, dosage disclaimer and officer remarks. Both English and Tamil PDF generation and Tamil XLSX export pass API/access-control checks. A merged OFL-licensed Noto font preserves Tamil shaping and Latin punctuation. Visual review rendered and inspected English/Tamil fixtures; missing Latin glyphs and mixed-font spacing were corrected. Reports are clearly laboratory records and cannot include unavailable predictions or charts of model results. A dedicated report-history page is implemented. Reports include a measured-pH scale chart with an explicit statement that it is not a fertility classification. Charts of model results remain unavailable.

## Phase 11 - verification/security (partial)

Latest local SQLite suite: 18 passed. Frontend suite: 3 passed on patched Vitest 5.1.1, covering login, visible errors and English/Tamil switching without unsaved-data loss. TypeScript and production builds pass. Original phase-4 PostgreSQL suite: 11 passed. The expanded suite passed all 18 tests against PostgreSQL as well (95 seconds). A later field-area safeguard added one regression test; five targeted records/report tests then passed. All 19 distinct backend tests have been exercised successfully across these runs.

Browser QA verified registration, PostgreSQL farm creation, full soil submission, saved record rendering, Tamil navigation/results, report generation/download, real dashboard count changes and logout. It used a disposable schema and was removed afterward; production farms remained zero. The normal dev API was restored. PDF inspection covered both scripts and page transitions. npm audit reported zero vulnerabilities after upgrading the test tooling.

Implemented request validation, parameterized ORM access, role/resource authorization, password/session security, process-local authentication throttling, CORS, Nginx file limits/security headers, audit records and secret validation. Public deployment still needs HTTPS ingress, shared gateway limiting, storage quotas/retention, robust SMTP delivery monitoring, load testing and operational security review. The current sessionStorage token design is documented; hardened public hosting should use an HttpOnly-cookie BFF.

## Phase 12 - deployment (partial)

Docker Compose includes PostgreSQL, the FastAPI backend and Nginx/React frontend. Both container images built successfully and all three services started. The frontend at http://localhost:8080 returned HTTP 200 and the proxied /api/v1/health/ready endpoint returned ready against PostgreSQL. A local locked Linux wheel cache avoided unusually slow Docker Desktop downloads; the cache is optional and ignored by Git. Windows commands, environment preservation, migration and administrator bootstrap are documented. The cloud operations guide describes TLS, secrets, database/storage persistence and backup/restore. No public cloud deployment, provider DNS/HTTPS setup, production load benchmark or restore drill has been performed.

## Remaining acceptance work

The largest dependency is scientifically suitable public data. Resolve Phase 5 before Phase 6 training, then implement Phases 7-8 against observed model outputs and verified regional agronomy. Remaining independent work includes complete localization of dynamic notifications, advanced dataset/admin/model job workflows, field editing UI, exhaustive UI/browser automation, performance/load testing, and production hardening/deployment. Existing functionality is usable and tested, while these requirements remain open.

## Final runtime verification

- Normal Docker application: http://localhost:8080 (Nginx + React + FastAPI + PostgreSQL).
- HTTP 200 for the application and a ready response for the database readiness endpoint.
- Frozen migration 0001 also exercised in the isolated browser QA schema.
- 18-test full suites passed on SQLite and PostgreSQL; five records/report regression tests passed after the last safeguard/chart change (19 distinct backend tests total).
- Three frontend tests passed on patched Vitest 5.1.1. Latest TypeScript and Docker production build passed.
- npm audit returned zero known vulnerabilities after updating Vitest.
- English/Tamil PDF pages were re-rendered and visually reviewed after the final chart change.
- Disposable browser QA records were removed; the application database retained zero seeded test farms.
- Local Vite/Uvicorn preview processes were shut down after verification; the Docker application remains running.
