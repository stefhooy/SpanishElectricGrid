import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import load_emerging, load_ev_type_mix, load_provinces_geojson_str
from utils.sidebar import render_sidebar

st.set_page_config(
    page_title="Strategic Markets | Spain EV 2027",
    page_icon="📈",
    layout="wide",
)

render_sidebar()

st.markdown("## 📈 Strategic Market Analysis — Objective 3")
st.markdown(
    '<span style="font-size:0.8rem;color:#94A3B8;">'
    'Province-level <span class="abbr-tooltip" data-tooltip="Electric Vehicle">EV</span> growth analysis · '
    'Opportunity scoring · Iberdrola deployment strategy'
    '</span>',
    unsafe_allow_html=True,
)
st.markdown(
    '> **What this page answers:** Which markets should Iberdrola enter — and in what order? '
    "Spain's 52 provinces grow at very different speeds. Some are large but saturating (Leaders); "
    'others are small but accelerating fastest (Emerging). '
    'The opportunity score combines '
    '<span class="abbr-tooltip" data-tooltip="Compound Annual Growth Rate — the year-over-year growth rate of EV registrations from 2021 to 2023">CAGR</span> '
    '(40%), projected fleet size (35%), and infrastructure gap (25%) to rank provinces by strategic value. '
    "Iberdrola's unique advantage in Emerging markets is that its grid subsidiary "
    '<span class="abbr-tooltip" data-tooltip="Iberdrola Distribución Eléctrica — Iberdrola\'s regulated grid subsidiary">i-DE</span> '
    'already operates the distribution network along the A-66 corridor — '
    'enabling faster permitting and grid connection than any competitor.',
    unsafe_allow_html=True,
)

df_em = load_emerging()
geojson_str = load_provinces_geojson_str()

QUADRANT_COLORS = {
    "Leader":   "#00A9CE",
    "Mature":   "#7DC855",
    "Emerging": "#F5A623",
    "Lagging":  "#64748B",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
    '**Map Colour Variable** — '
    '<span class="abbr-tooltip" data-tooltip="Compound Annual Growth Rate — year-over-year EV registration growth 2021–2023">CAGR</span> '
    'measures growth speed; Opportunity Score combines CAGR + fleet size + infrastructure gap',
    unsafe_allow_html=True,
)
    color_var = st.radio(
        "",
        ["opportunity_score", "cagr_pct", "ev_fleet_2027"],
        format_func=lambda x: {
            "opportunity_score": "Opportunity Score (0–100)",
            "cagr_pct": "CAGR 2021–2023 (%)",
            "ev_fleet_2027": "EV Fleet 2027",
        }[x],
    )
    st.markdown("---")
    st.markdown("**Quadrant filter**")
    sel_quad = st.multiselect(
        "Show quadrants",
        ["Leader", "Mature", "Emerging", "Lagging"],
        default=["Leader", "Mature", "Emerging", "Lagging"],
    )

df_filtered = df_em[df_em["quadrant"].isin(sel_quad)].copy()

color_labels = {
    "opportunity_score": "Opp. Score",
    "cagr_pct": "CAGR (%)",
    "ev_fleet_2027": "Fleet 2027",
}

# ── Province Opportunity Map (full width) ─────────────────────────────────────
st.markdown('<p class="section-header">Province Opportunity Map</p>', unsafe_allow_html=True)

fig_choro = px.choropleth_mapbox(
    df_filtered,
    geojson=json.loads(geojson_str),
    locations="province_code",
    featureidkey="properties.cod_prov",
    color=color_var,
    color_continuous_scale=[[0, "#0A2E1A"], [0.5, "#006B2B"], [1.0, "#00B140"]],
    mapbox_style="carto-darkmatter",
    zoom=4.8,
    center={"lat": 40.2, "lon": -3.5},
    opacity=0.75,
    hover_name="province_name",
    hover_data={
        "province_code": False,
        "auto_community": True,
        "quadrant": True,
        "cagr_pct": ":.1f",
        "ev_fleet_2027": ":,",
        "opportunity_score": ":.1f",
    },
    labels={
        "cagr_pct": "CAGR (%)",
        "ev_fleet_2027": "Fleet 2027",
        "opportunity_score": "Opp. Score",
        "auto_community": "Region",
        "quadrant": "Quadrant",
    },
)
fig_choro.update_layout(
    paper_bgcolor="#0F172A",
    margin=dict(t=0, b=0, l=0, r=0),
    height=500,
    coloraxis_colorbar=dict(
        title=dict(text=color_labels[color_var], font=dict(color="#94A3B8")),
        tickfont=dict(color="#94A3B8"),
    ),
)
st.plotly_chart(fig_choro, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Growth vs Fleet Quadrant Scatter (full width) ────────────────────────────
st.markdown('<p class="section-header">Growth vs Fleet Quadrant View</p>', unsafe_allow_html=True)

national_cagr = df_em["cagr_pct"].mean()
median_fleet = df_em["ev_fleet_2027"].median()

top12 = df_filtered.nlargest(12, "opportunity_score")["province_name"].tolist()
df_filtered["label"] = df_filtered.apply(
    lambda r: r["province_name"] if r["province_name"] in top12 else "", axis=1
)

fig_scatter = px.scatter(
    df_filtered,
    x="cagr_pct",
    y="ev_fleet_2027",
    size="opportunity_score",
    color="quadrant",
    color_discrete_map=QUADRANT_COLORS,
    text="label",
    hover_name="province_name",
    hover_data={
        "cagr_pct": ":.1f",
        "ev_fleet_2027": ":,",
        "opportunity_score": ":.1f",
        "quadrant": True,
        "label": False,
    },
    labels={
        "cagr_pct": "CAGR 2021–23 (%)",
        "ev_fleet_2027": "EV Fleet 2027",
        "opportunity_score": "Opp. Score",
    },
    template="plotly_dark",
    size_max=50,
)
fig_scatter.update_traces(textposition="top center", textfont=dict(size=10, color="#CBD5E1"))
fig_scatter.add_vline(x=national_cagr, line_dash="dash", line_color="#94A3B8", opacity=0.6,
                      annotation_text=f"Avg CAGR {national_cagr:.1f}%", annotation_font_color="#94A3B8")
fig_scatter.add_hline(y=median_fleet, line_dash="dash", line_color="#94A3B8", opacity=0.6,
                      annotation_text="Median fleet", annotation_font_color="#94A3B8")

fig_scatter.update_layout(
    paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
    height=480, margin=dict(t=20, b=20, l=0, r=0),
    yaxis=dict(gridcolor="#1E293B", type="log", title="EV Fleet 2027 (log scale)"),
    xaxis=dict(gridcolor="#1E293B"),
    legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# ── CAGR by Community + Operator Landscape ────────────────────────────────────
col_cagr, col_ops = st.columns(2)

with col_cagr:
    st.markdown('<p class="section-header">EV Growth Rate by Autonomous Community</p>', unsafe_allow_html=True)
    st.markdown(
        '<span style="font-size:0.8rem;color:#94A3B8;">'
        'Aggregated average <span class="abbr-tooltip" data-tooltip="Compound Annual Growth Rate — year-over-year EV registration growth 2021–2023">CAGR</span> '
        'per region reveals where structural <span class="abbr-tooltip" data-tooltip="Electric Vehicle">EV</span> adoption is happening fastest. '
        'Extremadura and Castilla-La Mancha lead — both crossed by the A-66 corridor where Iberdrola controls the grid.'
        '</span>',
        unsafe_allow_html=True,
    )
    community_cagr = (
        df_em.groupby("auto_community")["cagr_pct"]
        .mean()
        .reset_index()
        .sort_values("cagr_pct")
    )
    fig_comm = px.bar(
        community_cagr,
        x="cagr_pct", y="auto_community",
        orientation="h",
        color="cagr_pct",
        color_continuous_scale=["#0A2E1A", "#00B140"],
        text=community_cagr["cagr_pct"].map(lambda v: f"{v:.1f}%"),
        template="plotly_dark",
        labels={"cagr_pct": "Avg CAGR (%)", "auto_community": "Region"},
    )
    fig_comm.update_traces(textposition="outside", textfont=dict(color="#94A3B8", size=10))
    fig_comm.update_layout(
        paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
        height=400, margin=dict(t=10, b=10, l=0, r=40),
        coloraxis_showscale=False,
        xaxis=dict(gridcolor="#1E293B"),
        yaxis=dict(gridcolor="#1E293B"),
    )
    st.plotly_chart(fig_comm, use_container_width=True)

with col_ops:
    st.markdown('<p class="section-header">Operator Competitive Landscape</p>', unsafe_allow_html=True)
    st.markdown(
        '<span style="font-size:0.8rem;color:#94A3B8;">'
        'Iberdrola Clientes leads Spain\'s public charging market with 10,694 connectors — '
        'but Repsol Soluciones (6,354) is growing aggressively. The window for first-mover advantage '
        'in Emerging provinces is narrowing. Deploying on the A-66 before 2026 locks in Iberdrola\'s corridor dominance. '
        'Source: <span class="abbr-tooltip" data-tooltip="Dirección General de Tráfico — Spain\'s traffic authority, operator of the national charger registry">DGT</span> '
        'DATEX II registry.'
        '</span>',
        unsafe_allow_html=True,
    )
    ops_data = {
        "Operator": ["Iberdrola\nClientes", "Repsol\nSoluciones", "Endesa\nX Way", "Others"],
        "Connectors": [10694, 6354, 5688, 1839],
        "color": ["#00B140", "#EF4444", "#EAB308", "#64748B"],
    }
    import pandas as _pd
    df_ops = _pd.DataFrame(ops_data)
    fig_ops = go.Figure(go.Bar(
        x=df_ops["Connectors"],
        y=df_ops["Operator"],
        orientation="h",
        marker_color=df_ops["color"],
        text=df_ops["Connectors"].map(lambda v: f"{v:,}"),
        textposition="outside",
        textfont=dict(color="#94A3B8", size=11),
    ))
    fig_ops.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
        height=400, margin=dict(t=10, b=10, l=0, r=60),
        xaxis=dict(gridcolor="#1E293B", range=[0, 13000]),
        yaxis=dict(gridcolor="#1E293B"),
    )
    st.plotly_chart(fig_ops, use_container_width=True)

st.markdown("---")

# ── Top 10 Emerging bar chart ─────────────────────────────────────────────────
col_bar, col_strategy = st.columns([1, 1.1])

with col_bar:
    st.markdown('<p class="section-header">Top 10 Emerging Provinces — Opportunity Ranking</p>', unsafe_allow_html=True)
    top10 = (
        df_em[df_em["quadrant"] == "Emerging"]
        .nlargest(10, "opportunity_score")
        .sort_values("opportunity_score")
    )
    fig_bar = px.bar(
        top10,
        x="opportunity_score",
        y="province_name",
        orientation="h",
        color="opportunity_score",
        color_continuous_scale=["#F5A623", "#00B140"],
        text=top10["cagr_pct"].map(lambda v: f"CAGR {v:.1f}%"),
        template="plotly_dark",
        labels={"opportunity_score": "Opportunity Score", "province_name": "Province"},
    )
    fig_bar.update_traces(textposition="inside", textfont=dict(color="#1E293B", size=10))
    fig_bar.update_layout(
        paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
        height=340, margin=dict(t=10, b=10, l=0, r=0),
        coloraxis_showscale=False,
        xaxis=dict(gridcolor="#1E293B", range=[0, 110]),
        yaxis=dict(gridcolor="#1E293B"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_strategy:
    st.markdown('<p class="section-header">Deployment Strategy</p>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Balanced Strategy", "Emerging-First"])

    with tab1:
        st.markdown(
            '<div class="phase-card phase-1">'
            '<p class="phase-title">Phase 1 — Self-authorise i-DE Congested Nodes (Q3 2026)</p>'
            '<p class="phase-body">Initiate substation upgrades at the 5 Congested nodes where i-DE '
            '(Iberdrola\'s own distribution subsidiary) manages the grid — IBE_020 (AP-9, A Coruña), '
            'IBE_022 (AP-7N, Castellón), IBE_024 (A-3, Madrid–Valencia), IBE_030 (N-332, Alicante), '
            'IBE_031 (AP-68, Bilbao). No third-party approval needed — cuts the standard 18–24 month '
            'process to weeks. Each node earns a grid upgrade fee + charging revenue simultaneously.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="phase-card phase-2">'
            '<p class="phase-title">Phase 2 — Negotiate External Congested Nodes (Q4 2026)</p>'
            '<p class="phase-body">Open negotiations with Endesa and Viesgo for the 5 remaining '
            'Congested nodes — IBE_014 (A-4, Cádiz), IBE_016 (A-49, Huelva/Portugal border), '
            'IBE_017 (AP-7N, Girona/France border), IBE_023 (A-7, Málaga), IBE_029 (N-260, Pyrenees). '
            'These are high-traffic corridors that cannot be skipped for AFIR compliance. '
            'EU TEN-T corridor status strengthens the regulatory co-financing case.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="phase-card phase-3">'
            '<p class="phase-title">Phase 3 — Activate Moderate Stations (2027)</p>'
            '<p class="phase-body">As i-DE and external upgrades complete, activate the remaining '
            'Moderate-grid stations across all corridors. Re-run composite scoring quarterly as new '
            'DGT charger data is published. Expand focus to high-CAGR Emerging provinces: '
            'Badajoz (49.8%), Albacete (46.9%), Guadalajara (36.6%), Cuenca (34.1%).</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    with tab2:
        emerging_top = df_em[df_em["quadrant"] == "Emerging"].nlargest(10, "opportunity_score")
        st.markdown(
            "**Congested-first strategy:** Prioritise high-CAGR Emerging provinces where "
            "grid congestion is the only barrier — resolving it unlocks both the charger revenue "
            "and the grid upgrade fee at the same node. Iberdrola's i-DE controls the grid "
            "along the top Emerging corridors (A-66, A-3, AP-9), enabling internal fast-track approval."
        )
        st.dataframe(
            emerging_top[["province_name", "auto_community", "cagr_pct", "ev_fleet_2027", "opportunity_score"]]
            .rename(columns={
                "province_name": "Province",
                "auto_community": "Region",
                "cagr_pct": "CAGR (%)",
                "ev_fleet_2027": "Fleet 2027",
                "opportunity_score": "Score",
            }),
            hide_index=True,
            use_container_width=True,
        )
        st.info(
            "A-66 (Ruta de la Plata) passes through 6 of the top 10 emerging provinces. "
            "Iberdrola's i-DE manages the grid along this corridor — a unique competitive advantage.",
            icon="⚡",
        )

st.markdown("---")

# ── EV Type Mix ───────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">EV Type Mix — Top 10 Provinces (2027)</p>', unsafe_allow_html=True)
st.markdown(
    '<span style="font-size:0.8rem;color:#94A3B8;">'
    '<span class="abbr-tooltip" data-tooltip="Battery Electric Vehicle — runs entirely on electricity, no combustion engine">BEV</span> drivers '
    'require fast <span class="abbr-tooltip" data-tooltip="High Power Charging — DC fast charging ≥150 kW">HPC</span> charging for interurban trips '
    '— they cannot rely on slow <span class="abbr-tooltip" data-tooltip="Alternating Current — standard electricity type used for slow home/destination charging">AC</span> chargers. '
    '<span class="abbr-tooltip" data-tooltip="Plug-in Hybrid Electric Vehicle — electric + combustion engine, can charge from a socket">PHEV</span>/'
    '<span class="abbr-tooltip" data-tooltip="Range Extended Electric Vehicle — electric drive with a small combustion range extender">REEV</span> '
    'drivers have a combustion fallback. The higher a province\'s BEV share, the more urgent the HPC deployment. '
    'Madrid and Barcelona show the highest absolute BEV counts, driving the strongest business case for HPC investment.'
    '</span>',
    unsafe_allow_html=True,
)
df_mix = load_ev_type_mix()
df_mix_long = df_mix.melt(id_vars="province_name", value_vars=["bev", "phev", "reev"],
                           var_name="type", value_name="vehicles")
df_mix_long["type"] = df_mix_long["type"].map({"bev": "BEV", "phev": "PHEV", "reev": "REEV"})
fig_mix = px.bar(
    df_mix_long,
    x="vehicles", y="province_name",
    color="type",
    orientation="h",
    color_discrete_map={"BEV": "#00B140", "PHEV": "#00A9CE", "REEV": "#F5A623"},
    template="plotly_dark",
    labels={"vehicles": "EV Fleet 2027", "province_name": "Province", "type": "EV Type"},
    barmode="stack",
)
fig_mix.update_layout(
    paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
    height=320, margin=dict(t=10, b=10, l=0, r=0),
    xaxis=dict(gridcolor="#1E293B", tickformat=","),
    yaxis=dict(gridcolor="#1E293B"),
    legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center", font=dict(color="#94A3B8")),
)
st.plotly_chart(fig_mix, use_container_width=True)

st.markdown("---")
st.markdown('<p class="section-header">All Provinces — Full Opportunity Ranking</p>', unsafe_allow_html=True)

def _color_quad(val: str) -> str:
    return {
        "Leader":   "background-color:#0A2936; color:#00A9CE",
        "Mature":   "background-color:#0A2E1A; color:#7DC855",
        "Emerging": "background-color:#2A1A08; color:#F5A623",
        "Lagging":  "background-color:#1E293B; color:#94A3B8",
    }.get(val, "")

st.dataframe(
    df_em.sort_values("opportunity_score", ascending=False)[
        ["province_name", "auto_community", "quadrant", "cagr_pct", "ev_fleet_2027", "opportunity_score"]
    ].rename(columns={
        "province_name": "Province", "auto_community": "Region",
        "quadrant": "Quadrant", "cagr_pct": "CAGR (%)",
        "ev_fleet_2027": "Fleet 2027", "opportunity_score": "Opp. Score",
    })
    .style.map(_color_quad, subset=["Quadrant"]),
    use_container_width=True,
    hide_index=True,
    height=400,
)
