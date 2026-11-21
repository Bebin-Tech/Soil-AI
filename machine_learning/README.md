# SoilAI scientific subsystem

The deterministic provenance/EDA audit is implemented in `preprocessing/audit.py`. Candidate public sources and download instructions are recorded under `datasets/external`. Raw and processed datasets are distinct and ignored by Git. No candidate currently meets the scientific and regional requirements for production training.

Training, model comparison, SHAP, nutrient regression, clustering and activation are **not implemented or claimed complete**. They are Phase 6 work gated by the approved dataset contract in `docs/dataset/README.md`. The serving API explicitly responds with `MODEL_NOT_VALIDATED` instead of fake predictions. There are no bundled pickled models or invented evaluation results.
