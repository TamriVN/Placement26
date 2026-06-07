#!/usr/bin/env python3
"""Generate interactive HTML visualization from docs/ → vnvc_fhir_model.json."""

from __future__ import annotations

import colorsys
import json
from pathlib import Path

from fhir_links import enrich_fhir_links, is_fhir_resource

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "output" / "vnvc_fhir_model.json"
OUTPUT_PATH = ROOT / "output" / "vnvc_mapping_report.html"

RESOURCE_COLORS = {
    "Patient": "#4e79a7",
    "Immunization": "#59a14f",
    "AdverseEvent": "#e15759",
    "AllergyIntolerance": "#f28e2b",
    "Condition": "#b07aa1",
    "CarePlan": "#76b7b2",
    "Encounter": "#edc948",
    "Location": "#af7aa1",
    "MedicationAdministration": "#ff9da7",
    "Procedure": "#9c755f",
    "Observation": "#bab0ac",
    "RegulatedAuthorization": "#86bcb6",
    "Bundle": "#d37295",
    "MeasureReport": "#8cd17d",
    "Unmapped / Gap": "#666666",
}

# Root ring uses a neutral low-saturation tone; resources = full saturation; elements = muted variants.
SUNBURST_ROOT_COLOR = "#3a4658"
SUNBURST_LAYER_SATURATION = {
    0: 0.12,  # root
    1: 1.0,   # FHIR resource (inner ring)
    2: 0.55,  # FHIR element (outer ring) — base; further adjusted per sibling index
}


def _hex_to_hls(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)


def _hls_to_hex(hue: float, lightness: float, saturation: float) -> str:
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def _sunburst_color(base_hex: str, layer: int, sibling_index: int = 0, sibling_count: int = 1) -> str:
    """Same hue per FHIR resource; saturation/lightness vary by sunburst layer."""
    hue, light, sat = _hex_to_hls(base_hex)
    layer_sat = SUNBURST_LAYER_SATURATION.get(layer, 0.5)

    if layer == 0:
        return _hls_to_hex(hue, 0.28, layer_sat)

    if layer == 1:
        return _hls_to_hex(hue, max(0.32, min(0.52, light)), max(0.75, min(1.0, sat * layer_sat)))

    # Layer 2+: same hue as parent resource; desaturate and lighten toward the rim
    t = sibling_index / max(sibling_count - 1, 1)
    elem_sat = max(0.22, min(0.72, sat * layer_sat - t * 0.18))
    elem_light = max(0.38, min(0.72, light + 0.1 + t * 0.14))
    return _hls_to_hex(hue, elem_light, elem_sat)


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _fhir_resource_link(resource: str, color: str) -> str:
    if not is_fhir_resource(resource):
        return f'<span class="badge" style="background:{color}">{_esc(resource)}</span>'
    links = enrich_fhir_links(resource, "")
    return (
        f'<a class="fhir-link badge" style="background:{color}" '
        f'href="{links["resource_page"]}" target="_blank" rel="noopener" '
        f'title="Open {_esc(resource)} structure on hl7.org/FHIR/R5">{_esc(resource)} ↗</a>'
    )


def _fhir_element_link(rec: dict) -> str:
    fhir = rec["fhir"]
    element = fhir.get("element") or "—"
    if rec["unmapped"] or not element or element == "—":
        return f"<code>{_esc(element)}</code>"

    links = fhir.get("links") or enrich_fhir_links(fhir["resource"], fhir["element"])
    path = links.get("element_path") or element
    defn = _esc(fhir.get("definition") or f"Open {path} on hl7.org/FHIR/R5")
    return (
        f'<a class="fhir-link" href="{links["element_definition"]}" target="_blank" rel="noopener" '
        f'title="{defn}"><code>{_esc(path)}</code> ↗</a>'
    )


def _fhir_spec_links(rec: dict) -> str:
    if rec["unmapped"]:
        return "—"
    links = rec["fhir"].get("links") or enrich_fhir_links(rec["fhir"]["resource"], rec["fhir"]["element"])
    chips = []
    if links.get("resource_page"):
        chips.append(
            f'<a class="fhir-link link-chip" href="{links["resource_page"]}" '
            f'target="_blank" rel="noopener">Structure</a>'
        )
    if links.get("definitions_page"):
        chips.append(
            f'<a class="fhir-link link-chip" href="{links["definitions_page"]}" '
            f'target="_blank" rel="noopener">Element table</a>'
        )
    if links.get("element_definition") and rec["fhir"].get("element"):
        chips.append(
            f'<a class="fhir-link link-chip" href="{links["element_definition"]}" '
            f'target="_blank" rel="noopener">This field</a>'
        )
    return " ".join(chips) if chips else "—"


def build_resource_cards(fhir_spec: dict) -> str:
    cards = []
    for res, links in sorted(fhir_spec.get("resources", {}).items()):
        color = RESOURCE_COLORS.get(res, "#999")
        cards.append(
            f"""<div class="resource-card">
          <div class="resource-card-accent" style="background:{color}"></div>
          <a class="fhir-link resource-name" href="{links['resource_page']}" target="_blank" rel="noopener">{_esc(res)} ↗</a>
          <p class="resource-card-desc">FHIR R5 — click for resource design, profiles &amp; examples</p>
          <div class="resource-card-links">
            <a class="fhir-link link-chip" href="{links['resource_page']}" target="_blank" rel="noopener">Overview</a>
            <a class="fhir-link link-chip" href="{links['definitions_page']}" target="_blank" rel="noopener">Definitions table</a>
          </div>
        </div>"""
        )
    return "".join(cards)


def build_sankey_data(records: list[dict]) -> dict:
    """Build nodes/links for form → FHIR resource flow."""
    nodes: list[dict] = []
    links: list[dict] = []
    node_index: dict[str, int] = {}

    def add_node(name: str, group: str) -> int:
        key = f"{group}::{name}"
        if key not in node_index:
            node_index[key] = len(nodes)
            nodes.append({"name": name, "group": group})
        return node_index[key]

    resource_urls = {
        res: enrich_fhir_links(res, "")["definitions_page"]
        for res in {r["fhir"]["resource"] for r in records if not r["unmapped"] and is_fhir_resource(r["fhir"]["resource"])}
    }

    for rec in records:
        if rec["unmapped"]:
            target = add_node("Unmapped / Gap", "fhir")
        else:
            target = add_node(rec["fhir"]["resource"], "fhir")

        if not rec["forms"]:
            src = add_node("Cross-form concept", "form")
            links.append({"source": src, "target": target, "value": 1})
            continue

        for form in rec["forms"]:
            src = add_node(form["form_label"], "form")
            links.append({"source": src, "target": target, "value": 1})

    # Aggregate duplicate links
    aggregated: dict[tuple[int, int], int] = {}
    for link in links:
        key = (link["source"], link["target"])
        aggregated[key] = aggregated.get(key, 0) + link["value"]

    return {
        "nodes": nodes,
        "links": [{"source": s, "target": t, "value": v} for (s, t), v in aggregated.items()],
        "resource_urls": resource_urls,
    }


def build_resource_sunburst(records: list[dict]) -> dict:
    """Resource → element hierarchy for mapped concepts."""
    tree: dict = {}
    for rec in records:
        if rec["unmapped"]:
            continue
        res = rec["fhir"]["resource"]
        elem = rec["fhir"]["element"] or "(root)"
        tree.setdefault(res, {})
        tree[res].setdefault(elem, [])
        tree[res][elem].append(rec["concept"] or rec["forms"][0]["field"] if rec["forms"] else "—")

    children = []
    for res, elements in sorted(tree.items()):
        elem_children = []
        res_links = enrich_fhir_links(res, "")
        base_color = RESOURCE_COLORS.get(res, "#8b949e")
        elem_items = sorted(elements.items())

        for i, (elem, concepts) in enumerate(elem_items):
            elem_url = (
                enrich_fhir_links(res, elem)["element_definition"]
                if elem != "(root)"
                else res_links["definitions_page"]
            )
            elem_children.append(
                {
                    "name": elem,
                    "value": len(concepts),
                    "concepts": concepts,
                    "url": elem_url,
                    "itemStyle": {
                        "color": _sunburst_color(base_color, layer=2, sibling_index=i, sibling_count=len(elem_items))
                    },
                }
            )
        children.append(
            {
                "name": res,
                "children": elem_children,
                "url": res_links["resource_page"],
                "itemStyle": {"color": _sunburst_color(base_color, layer=1)},
            }
        )
    return {
        "name": "FHIR Resources",
        "children": children,
        "itemStyle": {"color": _sunburst_color(SUNBURST_ROOT_COLOR, layer=0)},
    }


def build_layered_flow_data(matrix: dict[str, dict[str, int]]) -> dict:
    """Two-column form→FHIR graph from Mapped_dataset matrix (docs-derived only)."""
    forms = sorted(matrix.keys())
    resources = sorted({res for counts in matrix.values() for res in counts})

    form_step = max(520 / max(len(forms), 1), 48)
    res_step = max(520 / max(len(resources), 1), 36)

    nodes = []
    for i, form in enumerate(forms):
        short = form if len(form) <= 48 else form[:45] + "…"
        nodes.append(
            {"id": form, "name": short, "fullName": form, "x": 40, "y": 30 + i * form_step, "category": 0}
        )
    for i, res in enumerate(resources):
        nodes.append({"id": res, "name": res, "fullName": res, "x": 560, "y": 30 + i * res_step, "category": 1})

    links = []
    for form, counts in matrix.items():
        for res, count in counts.items():
            if count > 0:
                links.append({"source": form, "target": res, "value": count})

    return {
        "nodes": nodes,
        "links": links,
        "categories": [{"name": "VNVC Forms (from docs)"}, {"name": "FHIR Resources (from Mapped_dataset)"}],
    }


def build_matrix_html(matrix: dict[str, dict[str, int]]) -> str:
    """Heatmap table: form rows × FHIR resource columns, cell = mapped field count."""
    forms = sorted(matrix.keys())
    resources = sorted({res for counts in matrix.values() for res in counts})
    if not forms or not resources:
        return "<p>No form→FHIR relationships found in Mapped_dataset.xlsx.</p>"

    max_count = max((c for counts in matrix.values() for c in counts.values()), default=1)

    def cell_color(count: int) -> str:
        if count == 0:
            return "transparent"
        intensity = min(0.15 + (count / max_count) * 0.55, 0.7)
        return f"rgba(88, 166, 255, {intensity:.2f})"

    header = "".join(f"<th>{_esc(r)}</th>" for r in resources)
    body_rows = []
    for form in forms:
        cells = []
        row_total = 0
        for res in resources:
            count = matrix.get(form, {}).get(res, 0)
            row_total += count
            label = str(count) if count else "·"
            cells.append(
                f'<td class="matrix-cell" style="background:{cell_color(count)}" '
                f'title="{_esc(form)} → {_esc(res)}: {count} mapped field(s)">{label}</td>'
            )
        body_rows.append(
            f'<tr><td class="matrix-form" title="{_esc(form)}">{_esc(form)}</td>{"".join(cells)}'
            f'<td class="matrix-total">{row_total}</td></tr>'
        )

    col_totals = []
    for res in resources:
        total = sum(matrix.get(f, {}).get(res, 0) for f in forms)
        col_totals.append(f"<td class='matrix-total'>{total}</td>")

    return f"""<table class="matrix-table">
      <thead><tr><th>VNVC Form ↓ / FHIR Resource →</th>{header}<th>Total</th></tr></thead>
      <tbody>{"".join(body_rows)}</tbody>
      <tfoot><tr><th>Total</th>{"".join(col_totals)}<td></td></tr></tfoot>
    </table>"""


def render_html(model: dict) -> str:
    records = model["mapping_records"]
    stats = model["stats"]
    fhir_spec = model.get("fhir_spec", {})
    matrix = model.get("form_fhir_matrix", {})
    source_files = model.get("source_files", [])
    form_titles = model.get("form_titles", {})
    sankey = build_sankey_data(records)
    sunburst = build_resource_sunburst(records)
    layered_flow = build_layered_flow_data(matrix)
    matrix_html = build_matrix_html(matrix)
    resource_cards = build_resource_cards(fhir_spec)
    fhir_base = fhir_spec.get("base_url", "https://hl7.org/fhir/R5")

    source_list = "".join(f"<li><code>{_esc(f)}</code></li>" for f in source_files)
    form_title_list = "".join(
        f"<li><code>{_esc(k)}</code>: {_esc(v)}</li>" for k, v in sorted(form_titles.items())
    )

    # Table rows
    table_rows = []
    for rec in sorted(records, key=lambda r: (r["unmapped"], r["fhir"]["resource"], r["concept"])):
        forms_str = ", ".join(f"{f['form_label'].split(':')[0]}: {f['field']}" for f in rec["forms"]) or "—"
        status = "gap" if rec["unmapped"] else "mapped"
        resource_name = rec["fhir"]["resource"] if not rec["unmapped"] else "⚠ Unmapped"
        color = RESOURCE_COLORS.get(rec["fhir"]["resource"], "#999")
        resource_cell = (
            _fhir_resource_link(rec["fhir"]["resource"], color)
            if not rec["unmapped"]
            else f'<span class="badge" style="background:#666">{_esc(resource_name)}</span>'
        )
        defn_preview = _esc(rec["fhir"].get("definition") or "—")
        table_rows.append(
            f"""<tr class="{status}" data-resource="{_esc(rec['fhir']['resource'])}" data-form="{_esc(forms_str)}">
              <td>{_esc(rec['concept'] or '—')}</td>
              <td class="forms">{_esc(forms_str)}</td>
              <td>{resource_cell}</td>
              <td>{_fhir_element_link(rec)}</td>
              <td class="definition">{defn_preview}</td>
              <td>{_fhir_spec_links(rec)}</td>
              <td>{_esc(rec['vnvc_data_type'])}</td>
              <td>{_esc(rec['terminology'] or '—')}</td>
            </tr>"""
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VNVC AEFI → FHIR Mapping Report</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
  <style>
    :root {{
      --bg: #0f1419;
      --surface: #1a2332;
      --border: #2d3a4f;
      --text: #e6edf3;
      --muted: #8b949e;
      --accent: #58a6ff;
      --success: #3fb950;
      --warn: #d29922;
      --danger: #f85149;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 2rem;
    }}
    h1 {{ font-size: 1.75rem; margin-bottom: 0.25rem; }}
    h2 {{ font-size: 1.25rem; margin: 2rem 0 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }}
    .subtitle {{ color: var(--muted); margin-bottom: 2rem; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
      text-align: center;
    }}
    .card .num {{ font-size: 2rem; font-weight: 700; color: var(--accent); }}
    .card .label {{ font-size: 0.85rem; color: var(--muted); }}
    .chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }}
    .chart-box {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
      min-height: 420px;
    }}
    .chart {{ width: 100%; height: 380px; }}
    .mermaid-wrap {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.5rem;
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.875rem;
      background: var(--surface);
      border-radius: 8px;
      overflow: hidden;
    }}
    th, td {{ padding: 0.6rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }}
    th {{ background: #243044; color: var(--muted); font-weight: 600; position: sticky; top: 0; }}
    tr.gap {{ background: rgba(248, 81, 73, 0.08); }}
    tr:hover {{ background: rgba(88, 166, 255, 0.06); }}
    .badge {{
      display: inline-block;
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      color: #fff;
    }}
    .priority {{
      display: inline-block;
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      color: #000;
    }}
    code {{ font-size: 0.8rem; color: var(--accent); }}
    a.fhir-link {{ color: var(--accent); text-decoration: none; }}
    a.fhir-link:hover {{ text-decoration: underline; }}
    a.fhir-link code {{ color: inherit; }}
    a.fhir-link.badge {{ color: #fff; text-decoration: none; }}
    a.fhir-link.badge:hover {{ opacity: 0.9; text-decoration: none; }}
    .link-chip {{
      display: inline-block;
      padding: 0.15rem 0.45rem;
      margin: 0.1rem 0.15rem 0.1rem 0;
      border: 1px solid var(--border);
      border-radius: 4px;
      font-size: 0.72rem;
      background: #243044;
    }}
    .link-chip:hover {{ background: #2d4a6f; }}
    .definition {{ font-size: 0.78rem; color: var(--muted); max-width: 220px; }}
    .resource-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 0.75rem;
      margin-bottom: 1.5rem;
    }}
    .resource-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.85rem 1rem;
      position: relative;
      overflow: hidden;
    }}
    .resource-card-accent {{
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
    }}
    .resource-name {{ font-weight: 700; font-size: 0.95rem; display: inline-block; margin-bottom: 0.35rem; }}
    .resource-card-desc {{ font-size: 0.75rem; color: var(--muted); margin-bottom: 0.5rem; }}
    .resource-card-links {{ display: flex; flex-wrap: wrap; gap: 0.25rem; }}
    .spec-banner {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.75rem 1rem;
      margin-bottom: 1.5rem;
      font-size: 0.875rem;
      color: var(--muted);
    }}
    .spec-banner a {{ font-weight: 600; }}
    .source-banner {{
      background: #1e2d1e;
      border: 1px solid #3d5a3d;
      border-radius: 8px;
      padding: 0.75rem 1rem;
      margin-bottom: 1rem;
      font-size: 0.85rem;
    }}
    .source-banner ul {{ margin: 0.5rem 0 0 1.25rem; color: var(--muted); }}
    .workflow-toggle {{ display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }}
    .workflow-toggle button {{
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.45rem 0.9rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.875rem;
    }}
    .workflow-toggle button.active {{ background: var(--accent); border-color: var(--accent); color: #0f1419; font-weight: 600; }}
    .workflow-panel {{ display: none; }}
    .workflow-panel.active {{ display: block; }}
    .matrix-table {{ font-size: 0.78rem; }}
    .matrix-table th, .matrix-table td {{ text-align: center; padding: 0.45rem 0.35rem; }}
    .matrix-form {{ text-align: left !important; max-width: 220px; font-size: 0.72rem; color: var(--muted); }}
    .matrix-cell {{ font-weight: 600; min-width: 2rem; }}
    .matrix-total {{ font-weight: 700; color: var(--accent); background: #243044 !important; }}
    .matrix-table thead th {{ font-size: 0.7rem; writing-mode: vertical-rl; transform: rotate(180deg); height: 120px; }}
    .matrix-table thead th:first-child, .matrix-table tfoot th:first-child {{ writing-mode: horizontal-tb; transform: none; height: auto; }}
    #layered-flow {{ width: 100%; height: 620px; }}
    .forms {{ font-size: 0.8rem; color: var(--muted); max-width: 280px; }}
    .filters {{ display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1rem; }}
    .filters input, .filters select {{
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.5rem 0.75rem;
      border-radius: 6px;
      font-size: 0.875rem;
    }}
    .table-wrap {{ max-height: 600px; overflow: auto; border: 1px solid var(--border); border-radius: 8px; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0; }}
    .legend-item {{ display: flex; align-items: center; gap: 0.35rem; font-size: 0.8rem; }}
    .legend-dot {{ width: 12px; height: 12px; border-radius: 2px; }}
    @media (max-width: 900px) {{ .chart-row {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <h1>VNVC AEFI Follow-Up → FHIR Mapping</h1>
  <p class="subtitle">Report generated exclusively from <code>docs/</code> spreadsheets — no external mapping data added</p>

  <div class="source-banner">
    <strong>Data sources</strong> (all content below is derived from these files only):
    <ul>{source_list}</ul>
    <details style="margin-top:0.5rem;color:var(--muted)">
      <summary>Form titles (cell A1 from Initial_Extraction…)</summary>
      <ul>{form_title_list}</ul>
    </details>
  </div>

  <div class="spec-banner">
    FHIR spec base: <a class="fhir-link" href="{fhir_base}/" target="_blank" rel="noopener">{fhir_base}/ ↗</a>
    — hl7.org links are appended to resources/elements listed in <code>Mapped_dataset.xlsx</code>
  </div>

  <div class="cards">
    <div class="card"><div class="num">{stats['total_concepts']}</div><div class="label">Total Concepts</div></div>
    <div class="card"><div class="num" style="color:var(--success)">{stats['mapped']}</div><div class="label">FHIR Mapped</div></div>
    <div class="card"><div class="num" style="color:var(--danger)">{stats['unmapped']}</div><div class="label">Mapping Gaps</div></div>
    <div class="card"><div class="num">{len(stats['by_resource'])}</div><div class="label">FHIR Resources</div></div>
    <div class="card"><div class="num">{sum(stats['form_variable_counts'].values())}</div><div class="label">Form Variables</div></div>
  </div>

  <h2>FHIR R5 Resource Reference</h2>
  <p class="subtitle" style="margin-top:-1rem;margin-bottom:1rem">Quick links to official resource design &amp; element definition tables used in this mapping</p>
  <div class="resource-grid">{resource_cards}</div>

  <h2>Form → FHIR Integration Workflow</h2>
  <p class="subtitle" style="margin-top:-1rem;margin-bottom:1rem">
    Derived from <code>Mapped_dataset.xlsx</code> — each cell/link count = number of mapped fields
  </p>
  <div class="workflow-toggle">
    <button type="button" class="active" data-view="matrix">Matrix map (recommended)</button>
    <button type="button" data-view="layered">Layered flow chart</button>
  </div>
  <div id="view-matrix" class="workflow-panel active chart-box">
    <p style="font-size:0.85rem;color:var(--muted);margin-bottom:0.75rem">
      Rows = VNVC forms · Columns = FHIR resources · Numbers = mapped field count from docs
    </p>
    <div class="table-wrap" style="max-height:none">{matrix_html}</div>
  </div>
  <div id="view-layered" class="workflow-panel chart-box">
    <p style="font-size:0.85rem;color:var(--muted);margin-bottom:0.5rem">
      Left = forms · Right = FHIR resources · Line thickness = mapped field count · Click a resource node to open its spec
    </p>
    <div id="layered-flow"></div>
  </div>

  <h2>Form → FHIR Resource Flow (detail)</h2>
  <p class="subtitle" style="margin-top:-1rem;margin-bottom:1rem">Click a FHIR resource node in the Sankey or pie chart to open its definitions table</p>
  <div class="chart-row">
    <div class="chart-box"><div id="sankey" class="chart"></div></div>
    <div class="chart-box"><div id="resource-pie" class="chart"></div></div>
  </div>

  <h2>FHIR Resource → Element Hierarchy</h2>
  <p class="subtitle" style="margin-top:-1rem;margin-bottom:1rem">
    Inner ring = FHIR resource (full saturation) · Outer ring = elements (same hue, lower saturation) · Click a segment to open hl7.org
  </p>
  <div class="chart-box"><div id="sunburst" class="chart" style="height:500px"></div></div>

  <h2>Field-Level Mapping</h2>
  <div class="legend">
    {''.join(f'<div class="legend-item"><div class="legend-dot" style="background:{c}"></div><a class="fhir-link" href="{enrich_fhir_links(r, "")["resource_page"]}" target="_blank" rel="noopener">{_esc(r)}</a></div>' for r,c in RESOURCE_COLORS.items() if r in stats['by_resource'])}
  </div>
  <div class="filters">
    <input type="text" id="search" placeholder="Search concept, field, resource…">
    <select id="resource-filter"><option value="">All FHIR resources</option>
      {''.join(f'<option value="{_esc(r)}">{_esc(r)}</option>' for r in sorted(stats['by_resource']))}
      <option value="Unmapped">Unmapped / Gap</option>
    </select>
    <select id="form-filter"><option value="">All forms</option>
      {''.join(f'<option value="{_esc(l.split(":")[0])}">{_esc(l)}</option>' for l in stats['by_form'])}
    </select>
  </div>
  <div class="table-wrap">
    <table id="mapping-table">
      <thead><tr>
        <th>Concept</th><th>VNVC Form Fields</th><th>FHIR Resource</th><th>FHIR Element</th>
        <th>Official Definition</th><th>hl7.org Links</th><th>VNVC Type</th><th>Terminology</th>
      </tr></thead>
      <tbody>{''.join(table_rows)}</tbody>
    </table>
  </div>

  <script>
    const sankeyData = {json.dumps(sankey)};
    const sunburstData = {json.dumps(sunburst)};
    const layeredFlowData = {json.dumps(layered_flow)};
    const resourceCounts = {json.dumps(stats['by_resource'])};
    const resourceColors = {json.dumps(RESOURCE_COLORS)};
    const resourceUrls = {json.dumps(sankey.get('resource_urls', {}))};

    // Workflow view toggle
    document.querySelectorAll('.workflow-toggle button').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.workflow-toggle button').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.workflow-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('view-' + btn.dataset.view).classList.add('active');
        if (btn.dataset.view === 'layered') layeredChart.resize();
      }});
    }});

    function openResourceUrl(name) {{
      const url = resourceUrls[name];
      if (url) window.open(url, '_blank', 'noopener');
    }}

    // Sankey
    const sankeyChart = echarts.init(document.getElementById('sankey'));
    sankeyChart.setOption({{
      tooltip: {{ trigger: 'item' }},
      series: [{{
        type: 'sankey',
        layout: 'none',
        emphasis: {{ focus: 'adjacency' }},
        data: sankeyData.nodes.map(n => ({{
          name: n.name,
          itemStyle: {{ color: n.group === 'form' ? '#58a6ff' : (resourceColors[n.name] || '#8b949e') }}
        }})),
        links: sankeyData.links,
        lineStyle: {{ color: 'gradient', curveness: 0.5, opacity: 0.4 }},
        label: {{ color: '#e6edf3', fontSize: 11 }}
      }}]
    }});
    sankeyChart.on('click', params => {{
      if (params.dataType === 'node') openResourceUrl(params.name);
    }});

    // Layered flow (clean bipartite graph from docs matrix)
    const layeredChart = echarts.init(document.getElementById('layered-flow'));
    layeredChart.setOption({{
      tooltip: {{
        formatter: p => {{
          if (p.dataType === 'edge') return p.data.source + ' → ' + p.data.target + ': ' + p.data.value + ' field(s)';
          const full = p.data.fullName || p.data.name;
          return full + (p.data.category === 1 ? '<br><em>Click to open FHIR spec</em>' : '');
        }}
      }},
      legend: {{ data: layeredFlowData.categories.map(c => c.name), textStyle: {{ color: '#e6edf3' }}, bottom: 0 }},
      series: [{{
        type: 'graph',
        layout: 'none',
        roam: true,
        draggable: true,
        categories: layeredFlowData.categories,
        data: layeredFlowData.nodes.map(n => ({{
          ...n,
          symbolSize: n.category === 0 ? 12 : 28,
          itemStyle: {{ color: n.category === 0 ? '#58a6ff' : (resourceColors[n.name] || '#8b949e') }},
          label: {{ show: true, color: '#e6edf3', fontSize: n.category === 0 ? 10 : 11, position: n.category === 0 ? 'right' : 'left' }}
        }})),
        links: layeredFlowData.links.map(l => ({{
          ...l,
          lineStyle: {{ width: Math.max(1, Math.sqrt(l.value)), curveness: 0.25, opacity: 0.45, color: '#58a6ff' }}
        }})),
        emphasis: {{ focus: 'adjacency', lineStyle: {{ width: 6, opacity: 0.85 }} }}
      }}]
    }});
    layeredChart.on('click', params => {{
      if (params.dataType === 'node' && params.data.category === 1) openResourceUrl(params.data.name);
    }});

    // Pie
    const pieChart = echarts.init(document.getElementById('resource-pie'));
    pieChart.setOption({{
      title: {{ text: 'Concepts by FHIR Resource (click to open spec)', left: 'center', textStyle: {{ color: '#e6edf3', fontSize: 14 }} }},
      tooltip: {{ trigger: 'item' }},
      series: [{{
        type: 'pie', radius: ['35%', '65%'],
        data: Object.entries(resourceCounts).map(([name, value]) => ({{
          name, value, itemStyle: {{ color: resourceColors[name] || '#999' }}
        }})),
        label: {{ color: '#e6edf3' }}
      }}]
    }});
    pieChart.on('click', params => openResourceUrl(params.name));

    // Sunburst — walk tree to find URL for clicked segment
    function findSunburstUrl(node, targetName) {{
      if (node.name === targetName && node.url) return node.url;
      if (node.children) {{
        for (const child of node.children) {{
          const found = findSunburstUrl(child, targetName);
          if (found) return found;
        }}
      }}
      return null;
    }}

    const sunChart = echarts.init(document.getElementById('sunburst'));
    sunChart.setOption({{
      title: {{ text: 'Click a segment to open hl7.org definition', left: 'center', textStyle: {{ color: '#8b949e', fontSize: 12 }} }},
      tooltip: {{
        formatter: p => {{
          if (p.data.concepts) return p.data.concepts.join('<br>') + '<br><em>Click to open definition</em>';
          return p.name + (p.value ? ': ' + p.value + ' fields' : '') + '<br><em>Click to open definition</em>';
        }}
      }},
      series: [{{
        type: 'sunburst', radius: ['12%', '90%'],
        data: [sunburstData],
        label: {{ color: '#e6edf3', fontSize: 10 }},
        itemStyle: {{ borderWidth: 1.5, borderColor: '#0f1419' }},
        levels: [
          {{}},
          {{ r0: '12%', r: '48%', label: {{ fontSize: 11, fontWeight: 'bold' }} }},
          {{ r0: '48%', r: '90%', label: {{ fontSize: 9 }} }}
        ]
      }}]
    }});
    sunChart.on('click', params => {{
      const url = findSunburstUrl(sunburstData, params.name);
      if (url) window.open(url, '_blank', 'noopener');
    }});

    window.addEventListener('resize', () => {{
      sankeyChart.resize(); pieChart.resize(); sunChart.resize(); layeredChart.resize();
    }});

    // Table filters
    const search = document.getElementById('search');
    const resFilter = document.getElementById('resource-filter');
    const formFilter = document.getElementById('form-filter');
    const rows = document.querySelectorAll('#mapping-table tbody tr');

    function filterTable() {{
      const q = search.value.toLowerCase();
      const res = resFilter.value;
      const form = formFilter.value;
      rows.forEach(row => {{
        const text = row.textContent.toLowerCase();
        const matchQ = !q || text.includes(q);
        const matchR = !res || (res === 'Unmapped' ? row.classList.contains('gap') : row.dataset.resource === res);
        const matchF = !form || row.dataset.form.includes(form);
        row.style.display = matchQ && matchR && matchF ? '' : 'none';
      }});
    }}
    search.addEventListener('input', filterTable);
    resFilter.addEventListener('change', filterTable);
    formFilter.addEventListener('change', filterTable);
  </script>
</body>
</html>"""


def main() -> None:
    if not MODEL_PATH.exists():
        raise SystemExit(f"Run extract_mapping.py first. Missing {MODEL_PATH}")

    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    html = render_html(model)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
