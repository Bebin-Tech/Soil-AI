# Dataset provenance and scientific gate

No model is trained or deployed, and no prediction metrics are claimed. The user explicitly selected **verified public data only, with predictions unavailable until validation**. Application features for records, imports, access control and reports remain usable without a model.

The source register is `machine_learning/datasets/external/sources.json`. Never relabel a crop dataset as fertility data. Unknown nutrient units cannot be assumed to mean mg/kg or kg/ha. Rainfall needs an accumulation period. Total N, available N, elemental P and P2O5 are distinct measurements, as are different extraction procedures.

Sources reviewed:

- [Kaggle Crop Recommendation Dataset](https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset): primary page is not text-readable through this environment; licence, laboratory methods and compatibility remain unverified. The original target is crop, not fertility.
- [ISRIC SoilGrids](https://docs.isric.org/globaldata/soilgrids/): CC BY 4.0, global modelled soil properties. Its [official FAQ](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_04.html) advises against farm-level use. It cannot supply independent low/medium/high laboratory labels. The [unit dictionary](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html) documents scaling; do not apply those scales to laboratory inputs.
- [Feng et al., Mendeley Data V1](https://data.mendeley.com/datasets/c8bz2mf2j8/1), DOI 10.17632/c8bz2mf2j8.1: CC BY 4.0; soil chemistry from a repeated-plot field experiment in Guizhou, China. The public metadata API returned HTTP 403. The source register includes the exact manual download path. Its treatment labels are not fertility labels and regional transfer has not been established.

## Onboarding a public dataset

1. Download the original file from the publisher; preserve the original in `machine_learning/datasets/raw/` with a version and SHA-256 digest. Do not commit data whose redistribution licence is unclear.
2. Record source URL, licence, citation, geography, sampling time/depth, laboratory protocol, units and chemical basis. Preserve plot/farm/site IDs for grouped validation.
3. Record the independently defined target, reference and qualified reviewer. For fertility the target must be a valid lab/agronomic class. Include a dictionary of each feature with units, method and physical bounds.
4. Clean into a new version under `datasets/processed/`. Record every change. Do not automatically remove agronomically meaningful extremes or fill targets.
5. Run the audit below. Resolve missing values, duplicate rows, invalid units, target leakage and group independence. Compare regional and seasonal coverage to the intended deployment population.
6. Only a scientifically approved dataset should proceed to Phase 6 training. Use grouped held-out sites/seasons; fit preprocessing only on the training folds; report observed metrics and uncertainty. Include independent Indian regional evaluation. Approval and activation are separate operations.

```powershell
python machine_learning\preprocessing\audit.py --csv machine_learning\datasets\processed\your-version.csv --manifest machine_learning\datasets\external\your-manifest.json --output reports\dataset-audit.json
```

Exit code 2 means the audit found blockers; it still writes the report. It never reports a fabricated score or silently converts incompatible units.

## Data dictionary contract

A manifest is JSON with `name`, `version`, `source_url`, `licence`, `collection_region`, `collection_method`, `task` (`fertility` or `crops`), `target`, `target_definition`, `target_reviewed_by`, `target_reference_url`, `group_column`, `regional_validation` and `features`. Each feature maps to `{ "unit": "publisher-verified unit", "method": "publisher-verified method", "min": 0, "max": 100 }` with appropriate bounds. `regional_validation` must contain independently reviewed evidence and `status: "verified"`. An assertion in a JSON file is necessary metadata, not a substitute for scientific review.

## Application measurement dictionary

The API `/api/v1/soil-parameters` is the machine-readable dictionary. Each record stores its own unit and method. Accepted units are input validation options, not proof that a particular test method can be interpreted or converted. Numeric limits are broad physical sanity checks, never agronomic reference ranges. The current application does not assign nutrient deficiency thresholds, fertilizer dosages or universal soil-health scores.
