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

Re-run after updating any file in `docs/`, then commit and push `output/vnvc_mapping_report.html` to update the hosted site.

## Host online (GitHub Pages)

The repo includes a GitHub Actions workflow that publishes the report as a static site.

**One-time setup:**

1. Push this repo to GitHub (you already have `origin` → `TamriVN/Placement26`).
2. On GitHub: **Settings → Pages → Build and deployment → Source** → choose **GitHub Actions**.
3. Push to `main` (or run the workflow manually under **Actions → Deploy mapping report → Run workflow**).

Your report will be live at:

`https://tamrivn.github.io/Placement26/`

(After each push to `main`, the site updates automatically from `output/vnvc_mapping_report.html`.)

## Host on Render (alternative)

1. [render.com](https://render.com) → **New → Static Site** → connect this GitHub repo.
2. Settings:
   - **Build command:** *(leave empty)*
   - **Publish directory:** `output`
3. Add a **Redirect/Rewrite** rule so the root URL serves the report:
   - Source: `/`
   - Destination: `/vnvc_mapping_report.html`
   - Action: Rewrite

Or copy the report to `output/index.html` before pushing if you prefer a simpler Render setup.
