# VNVC AEFI → FHIR Mapping Report

Generates an interactive HTML report from the VNVC form mapping spreadsheets in `docs/`.

## Prerequisites

- Python 3.9+
- Spreadsheet files placed in `docs/` (this folder is gitignored):

  - `Mapped_dataset.xlsx`
  - `Initial_Extraction_of_Variables_from_VNVC_forms.xlsx`
  - `VNVC_Data_Dictionary.xlsx`

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
./scripts/run_all.sh
```

Or step by step:

```bash
python3 scripts/extract_mapping.py      # docs/*.xlsx → output/vnvc_fhir_model.json
python3 scripts/visualize_mapping.py    # → output/vnvc_mapping_report.html
```

## View the report

Open `output/vnvc_mapping_report.html` in your browser:

```bash
open output/vnvc_mapping_report.html
```

Re-run after updating any file in `docs/`.
