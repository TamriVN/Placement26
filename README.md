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

The workflow pushes `output/vnvc_mapping_report.html` to the **`gh-pages`** branch as `index.html`.

**One-time setup:**

1. Push this repo to GitHub and merge the workflow to `main`.
2. Run the workflow once: **Actions → Deploy mapping report → Run workflow**.
3. On GitHub: **Settings → Pages → Build and deployment**
   - **Source:** Deploy from a branch
   - **Branch:** `gh-pages` → `/ (root)` → **Save**
4. Wait 1–2 minutes. Site URL:

   `https://tamrivn.github.io/Placement26/`

After that, every push to `main` updates the site automatically.

**If you previously tried “GitHub Actions” as the Pages source and saw a 404 deploy error:** switch the Pages source to **Deploy from a branch → gh-pages** as above, then re-run the workflow.

**Private repo?** GitHub Pages on a private repo requires a paid GitHub plan. Make the repo public to use free Pages hosting.
