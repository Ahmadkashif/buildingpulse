"""Server-rendered HTML report template (PDF source).

Pure-Python renderer — no Jinja, no external assets. CSS is inlined in a
``<style>`` block so WeasyPrint can produce a self-contained PDF without
fetching anything off-disk or off-network.

Layout mirrors the result page (`frontend/src/app/forecasting/report/[id]/page.tsx`):

    Sponsor strip
    Headline (property type + generated_at)
    KPIs (Predicted EUI / Peer percentile / LL97 status)
    Peer cohort comparison (p25 / median / you / p75)
    Fine timeline (year-by-year through 2034)
    Building profile

Determinism is part of the contract: snapshot tests pin the byte-exact
output against a fixture, so every value rendered here is sorted, fixed
precision, and locale-free.
"""

from __future__ import annotations

from html import escape

from app.schemas import (
    AgeBand,
    Borough,
    PredictionResponse,
    PropertyType,
)

__all__ = ["render_report_html"]


_PROPERTY_TYPE_LABELS: dict[PropertyType, str] = {
    "multifamily-housing": "Multifamily Housing",
    "office": "Office",
    "hotel": "Hotel",
    "retail": "Retail",
    "hospital": "Hospital",
    "mixed-use": "Mixed Use",
}

_BOROUGH_LABELS: dict[Borough, str] = {
    "manhattan": "Manhattan",
    "brooklyn": "Brooklyn",
    "queens": "Queens",
    "bronx": "Bronx",
    "staten-island": "Staten Island",
}

_AGE_BAND_LABELS: dict[AgeBand, str] = {
    "pre-1950": "Pre-1950",
    "1950-1979": "1950-1979",
    "1980-1999": "1980-1999",
    "2000-plus": "2000+",
}


_CSS = """\
@page { size: Letter; margin: 0.6in; }
* { box-sizing: border-box; }
body {
  font-family: 'Helvetica', 'Arial', sans-serif;
  color: #1a1a1a;
  font-size: 10pt;
  line-height: 1.4;
  margin: 0;
}
h1, h2, h3 { margin: 0 0 6pt 0; font-weight: 600; }
h1 { font-size: 18pt; }
h2 { font-size: 13pt; border-bottom: 1pt solid #d0d0d0; padding-bottom: 3pt; margin-top: 14pt; }
h3 { font-size: 11pt; }
.sponsor-strip {
  background: #0f3a5f;
  color: #ffffff;
  padding: 6pt 10pt;
  font-size: 9pt;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.header { padding: 10pt 0 6pt 0; }
.header .meta { color: #555; font-size: 9pt; }
.kpis { display: table; width: 100%; border-spacing: 6pt 0; margin: 8pt 0; }
.kpi {
  display: table-cell;
  width: 33.33%;
  border: 1pt solid #d0d0d0;
  border-radius: 6pt;
  padding: 8pt 10pt;
  vertical-align: top;
}
.kpi .label { font-size: 9pt; color: #555; text-transform: uppercase; letter-spacing: 0.04em; }
.kpi .value { font-size: 16pt; font-weight: 700; margin-top: 4pt; }
.kpi .caption { font-size: 9pt; color: #555; margin-top: 4pt; }
.kpi--at-risk .value { color: #b32f2f; }
.kpi--compliant .value { color: #1e6f3a; }
table.data { width: 100%; border-collapse: collapse; margin-top: 4pt; }
table.data th, table.data td {
  border: 1pt solid #d0d0d0;
  padding: 4pt 6pt;
  text-align: left;
  font-size: 9.5pt;
}
table.data th { background: #f3f3f3; font-weight: 600; }
table.data td.num { text-align: right; font-variant-numeric: tabular-nums; }
.fine-row--at-risk td.num { color: #b32f2f; font-weight: 600; }
.profile { width: 100%; border-collapse: collapse; }
.profile td {
  padding: 4pt 6pt;
  border-bottom: 1pt solid #ececec;
  font-size: 9.5pt;
}
.profile td.label { color: #555; width: 40%; }
.peer-row--you td { background: #fff3cd; font-weight: 600; }
.footer {
  margin-top: 14pt;
  font-size: 8.5pt;
  color: #777;
  border-top: 1pt solid #d0d0d0;
  padding-top: 6pt;
}
"""


def _ordinal(n: int) -> str:
    mod100 = n % 100
    if 11 <= mod100 <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _fmt_money(value: float) -> str:
    """Whole-dollar formatting with thousands separators. Locale-free."""
    return f"${round(value):,}"


def _fmt_eui(value: float) -> str:
    return f"{value:.1f}"


def _fmt_int(value: int) -> str:
    return f"{value:,}"


def render_report_html(prediction: PredictionResponse) -> str:
    """Render a ``PredictionResponse`` to a self-contained HTML report.

    The output is deterministic for a given input — same prediction in,
    byte-identical HTML out — so it can be pinned to a snapshot.
    """
    p = prediction
    inp = p.input
    pred = p.prediction
    peer = p.peer
    ll97 = p.ll97

    property_label = _PROPERTY_TYPE_LABELS[inp.property_type]
    borough_label = _BOROUGH_LABELS[inp.borough]
    cohort_borough_label = (
        _BOROUGH_LABELS[peer.cohort.borough] if peer.cohort.borough else "All boroughs"
    )
    cohort_age_label = (
        _AGE_BAND_LABELS[peer.cohort.age_band] if peer.cohort.age_band else "All ages"
    )

    at_risk = ll97.at_risk
    status_label = "At Risk" if at_risk else "Compliant"
    status_class = "kpi--at-risk" if at_risk else "kpi--compliant"
    status_caption = (
        f"Projected fine: {_fmt_money(ll97.projected_annual_fine_usd_2030)}/yr by 2030"
        if at_risk
        else "Below current cap"
    )

    percentile = peer.percentile
    percentile_caption = "Higher = uses more energy than peers"

    generated_at = p.generated_at.isoformat()

    kpis_html = (
        f"""
    <div class="kpis">
      <div class="kpi">
        <div class="label">Predicted Site EUI</div>
        <div class="value">{_fmt_eui(pred.site_eui_kbtu_per_sqft)} kBtu/sf</div>
        <div class="caption">"""
        f"""Interval: {_fmt_eui(pred.interval_low)} - {_fmt_eui(pred.interval_high)} kBtu/sf</div>
      </div>
      <div class="kpi">
        <div class="label">Peer Percentile</div>
        <div class="value">{percentile}{_ordinal(percentile)}</div>
        <div class="caption">{escape(percentile_caption)}</div>
      </div>
      <div class="kpi {status_class}">
        <div class="label">LL97 Status</div>
        <div class="value">{status_label}</div>
        <div class="caption">{escape(status_caption)}</div>
      </div>
    </div>"""
    )

    peer_rows = [
        ("p25", _fmt_eui(peer.p25_site_eui), False),
        ("Cohort Median", _fmt_eui(peer.median_site_eui), False),
        ("Your Building", _fmt_eui(pred.site_eui_kbtu_per_sqft), True),
        ("p75", _fmt_eui(peer.p75_site_eui), False),
    ]
    peer_rows_html = "\n".join(
        f'      <tr class="peer-row--you"><td>{escape(label)}</td>'
        f'<td class="num">{value} kBtu/sf</td></tr>'
        if is_you
        else f'      <tr><td>{escape(label)}</td><td class="num">{value} kBtu/sf</td></tr>'
        for label, value, is_you in peer_rows
    )

    fine_rows_html = "\n".join(
        f'      <tr class="fine-row--at-risk"><td>{row.year}</td>'
        f'<td class="num">{_fmt_money(row.projected_annual_fine_usd)}</td></tr>'
        if row.projected_annual_fine_usd > 0
        else f"      <tr><td>{row.year}</td>"
        f'<td class="num">{_fmt_money(row.projected_annual_fine_usd)}</td></tr>'
        for row in ll97.fine_series
    )

    profile_rows = [
        ("Property Type", property_label),
        ("Borough", borough_label),
        ("Gross Floor Area", f"{_fmt_int(inp.gross_floor_area_sqft)} sqft"),
        ("Year Built", str(inp.year_built)),
        ("Buildings on Lot", str(inp.number_of_buildings)),
        ("Model Version", pred.model_version),
    ]
    profile_html = "\n".join(
        f'      <tr><td class="label">{escape(label)}</td><td>{escape(value)}</td></tr>'
        for label, value in profile_rows
    )

    cohort_descriptor = f"{cohort_age_label} {property_label} buildings in {cohort_borough_label}"
    peer_subtitle = (
        f"Your building vs. {_fmt_int(peer.cohort_size)} similar buildings"
        f" - {escape(cohort_descriptor)}."
    )
    cap_subtitle = (
        f"Projected annual fines by year. "
        f"Cap 2024-2029: {_fmt_eui(ll97.cap_kbtu_per_sqft_2024_to_2029)} kBtu/sf"
        f" / Cap 2030-2034: {_fmt_eui(ll97.cap_kbtu_per_sqft_2030_to_2034)} kBtu/sf."
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>BuildingPulse Report — {escape(p.id)}</title>
<style>
{_CSS}</style>
</head>
<body>
  <div class="sponsor-strip">
    Brought to you by your BuildingPulse partner
  </div>

  <div class="header">
    <h1>Site EUI Prediction · {escape(property_label)}</h1>
    <div class="meta">Report ID: {escape(p.id)} · Generated {escape(generated_at)}</div>
    <p>Predicted Site Energy Use Intensity, peer cohort ranking, and LL97
    compliance outlook for this NYC building.</p>
  </div>

  <h2>Headline Metrics</h2>
{kpis_html}

  <h2>Peer Cohort Comparison</h2>
  <p>{peer_subtitle}</p>
  <table class="data">
    <thead>
      <tr><th>Bucket</th><th>Site EUI</th></tr>
    </thead>
    <tbody>
{peer_rows_html}
    </tbody>
  </table>

  <h2>LL97 Fine Outlook</h2>
  <p>{cap_subtitle}</p>
  <table class="data">
    <thead>
      <tr><th>Year</th><th>Projected Annual Fine</th></tr>
    </thead>
    <tbody>
{fine_rows_html}
    </tbody>
  </table>

  <h2>Building Profile</h2>
  <table class="profile">
    <tbody>
{profile_html}
    </tbody>
  </table>

  <div class="footer">
    BuildingPulse · Predicted Site EUI is a model estimate. Use as a directional
    indicator, not a substitute for an audit.
  </div>
</body>
</html>
"""
