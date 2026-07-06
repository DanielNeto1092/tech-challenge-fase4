"""Sentinela AI — Streamlit Demo Application.

Premium multimodal analysis dashboard.
Run with: streamlit run app_demo.py
"""
from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from src.pipeline import SentinelaPipeline

logger = logging.getLogger("sentinela.ui")

# ═══════════════════════════════════════════════════════════════════════════
# Page config
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Sentinela AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
# Design Tokens — FIAP palette
# ═══════════════════════════════════════════════════════════════════════════
_PRIMARY = "#ED145B"
_PRIMARY_SOFT = "#FF4D8D"
_BG = "#050816"
_CARD = "#0F172A"
_SURFACE = "#111827"
_TEXT = "#FFFFFF"
_TEXT2 = "#94A3B8"
_TEXT3 = "#64748B"
_BORDER = "rgba(255,255,255,0.06)"
_BORDER_ACCENT = "rgba(237,20,91,0.15)"
_SUCCESS = "#22C55E"
_WARN = "#F59E0B"
_DANGER = "#EF4444"

# ═══════════════════════════════════════════════════════════════════════════
# CSS — Minimal, safe, no * font override
# ═══════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
    /* === FONTS === */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }}
    .stApp button, .stApp input, .stApp textarea,
    .stApp select, .stApp label {{
        font-family: inherit !important;
    }}
    /* Restore icon fonts for Streamlit expander toggles */
    [data-testid="stExpanderToggleIcon"] {{
        font-family: 'Material Symbols Rounded' !important;
    }}

    /* === CHROME === */
    #MainMenu, footer {{visibility:hidden !important; height:0 !important;}}
    .stDeployButton, [data-testid="stToolbar"] {{display:none !important;}}
    header[data-testid="stHeader"] {{background:transparent !important; border:none !important;}}

    /* === SIDEBAR === */
    [data-testid="stSidebar"] {{
        background:{_CARD} !important;
        border-right:1px solid {_BORDER} !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background:{_CARD} !important;
        padding-top:0.5rem;
    }}

    /* === LAYOUT === */
    .stApp, [data-testid="stAppViewContainer"] {{background:{_BG} !important;}}
    .main .block-container {{
        padding-top:0.5rem;
        padding-bottom:2rem;
        max-width:1100px;
    }}

    /* === SIDEBAR COMPONENTS === */
    [data-testid="stSidebar"] .stTextArea textarea {{
        background:{_SURFACE} !important;
        border:1px solid rgba(255,255,255,0.08) !important;
        border-radius:10px !important;
        color:{_TEXT} !important;
        font-size:0.85rem !important;
        padding:0.6rem 0.8rem !important;
    }}
    [data-testid="stSidebar"] .stTextArea textarea:focus {{
        border-color:rgba(237,20,91,0.3) !important;
        box-shadow:0 0 0 2px rgba(237,20,91,0.06) !important;
    }}
    [data-testid="stSidebar"] .stTextArea textarea::placeholder {{color:#475569 !important;}}

    [data-testid="stSidebar"] [data-testid="stFileUploader"] {{
        background:{_SURFACE} !important;
        border:1px dashed rgba(255,255,255,0.08) !important;
        border-radius:10px !important;
        padding:0.35rem 0.5rem !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploader"]:hover {{
        border-color:{_BORDER_ACCENT} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button {{
        background:transparent !important;
        border:1px solid rgba(255,255,255,0.08) !important;
        border-radius:8px !important;
        color:{_TEXT2} !important;
        font-size:0.78rem !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploader"] small {{
        color:{_TEXT3} !important;
        font-size:0.72rem !important;
    }}
    [data-testid="stSidebar"] .stButton > button {{
        background:linear-gradient(135deg,{_PRIMARY},{_PRIMARY_SOFT}) !important;
        border:none !important;
        border-radius:10px !important;
        padding:0.7rem 1.2rem !important;
        font-weight:700 !important;
        font-size:0.92rem !important;
        color:white !important;
        letter-spacing:0.2px !important;
        box-shadow:0 4px 20px rgba(237,20,91,0.2) !important;
        transition:all 0.2s ease !important;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        box-shadow:0 6px 28px rgba(237,20,91,0.3) !important;
        transform:translateY(-1px) !important;
    }}
    [data-testid="stSidebar"] [data-testid="stExpander"] {{
        border:1px solid {_BORDER} !important;
        border-radius:10px !important;
        background:transparent !important;
    }}

    /* === EXPANDERS (general) === */
    [data-testid="stExpander"] {{
        background:{_CARD} !important;
        border:1px solid {_BORDER} !important;
        border-radius:12px !important;
    }}
    [data-testid="stExpander"] summary {{
        font-weight:600 !important;
        color:{_TEXT2} !important;
        font-size:0.85rem !important;
    }}

    /* === PROGRESS === */
    .stProgress > div > div > div {{
        background:linear-gradient(90deg,{_PRIMARY},{_PRIMARY_SOFT}) !important;
        border-radius:6px !important;
    }}
    .stProgress > div > div {{
        background:rgba(255,255,255,0.04) !important;
        border-radius:6px !important;
    }}

    /* === SCROLLBAR === */
    ::-webkit-scrollbar {{width:5px;}}
    ::-webkit-scrollbar-track {{background:transparent;}}
    ::-webkit-scrollbar-thumb {{background:rgba(255,255,255,0.07); border-radius:3px;}}

    /* ══════════════════════════════════════════════════════════════════
       CUSTOM COMPONENTS
       ══════════════════════════════════════════════════════════════════ */

    /* Section labels */
    .section-label {{
        font-size:0.62rem; text-transform:uppercase; letter-spacing:2.5px;
        color:{_TEXT3}; font-weight:700;
        margin:1.5rem 0 0.6rem 0;
        padding-bottom:0.3rem;
        border-bottom:1px solid rgba(255,255,255,0.04);
    }}

    /* Sidebar brand */
    .sidebar-brand {{
        text-align:center; padding:0.3rem 0 0.7rem 0;
        border-bottom:1px solid rgba(255,255,255,0.04);
        margin-bottom:0.3rem;
    }}
    .brand-name {{
        font-size:1.25rem; font-weight:800; color:{_TEXT};
        letter-spacing:-0.5px;
    }}
    .brand-dot {{color:{_PRIMARY};}}
    .brand-sub {{
        font-size:0.62rem; color:{_TEXT3};
        margin-top:0.1rem; letter-spacing:0.3px;
    }}

    /* Upload labels */
    .upload-label {{
        font-size:0.72rem; font-weight:600; color:{_TEXT2};
        margin:0.5rem 0 0.1rem 0;
        display:flex; align-items:center; gap:0.3rem;
    }}

    /* Hero */
    .sentinela-hero {{
        text-align:center;
        padding:0.8rem 1rem 0.5rem 1rem;
    }}
    .sentinela-hero h1 {{
        font-size:1.9rem; font-weight:900; letter-spacing:-1px;
        color:{_TEXT}; margin:0; line-height:1.1;
    }}
    .hero-dot {{color:{_PRIMARY};}}
    .sentinela-hero .subtitle {{
        font-size:0.85rem; color:{_TEXT2};
        margin:0.35rem auto 0; line-height:1.5;
        max-width:520px;
    }}

    /* Badges */
    .sentinela-badge-row {{
        display:flex; justify-content:center; gap:0.3rem;
        margin:0.6rem 0 0 0; flex-wrap:wrap;
    }}
    .sentinela-badge {{
        padding:0.15rem 0.5rem; border-radius:20px;
        font-size:0.58rem; font-weight:600; letter-spacing:0.3px;
        border:1px solid rgba(255,255,255,0.08);
        background:rgba(255,255,255,0.02);
        color:{_TEXT3};
    }}
    .sentinela-badge.primary {{
        border-color:{_BORDER_ACCENT};
        background:rgba(237,20,91,0.04);
        color:{_PRIMARY_SOFT};
    }}

    /* KPI row */
    .kpi-card {{
        background:{_CARD}; border:1px solid {_BORDER};
        border-radius:12px; padding:0.6rem 0.7rem; text-align:center;
    }}
    .kpi-value {{
        font-size:1.3rem; font-weight:800; color:{_TEXT}; line-height:1.2;
    }}
    .kpi-label {{
        font-size:0.6rem; color:{_TEXT3}; text-transform:uppercase;
        letter-spacing:1px; margin-top:0.1rem;
    }}

    /* Input hero card */
    .input-hero {{
        background:{_CARD}; border:1px solid {_BORDER};
        border-radius:14px; padding:1rem 1.2rem; margin:0.4rem 0 0.6rem 0;
    }}
    .input-hero h3 {{
        font-size:0.88rem; font-weight:700; color:{_TEXT}; margin:0 0 0.2rem 0;
    }}
    .input-hero p {{
        font-size:0.78rem; color:{_TEXT3}; margin:0; line-height:1.5;
    }}

    /* Evidence grid */
    .evidence-grid {{
        display:grid; grid-template-columns:repeat(4,1fr); gap:0.4rem;
        margin:0.5rem 0 0 0;
    }}
    .evidence-item {{
        display:flex; align-items:center; gap:0.3rem;
        padding:0.4rem 0.5rem;
        background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.04);
        border-radius:10px; font-size:0.74rem; color:{_TEXT2};
    }}
    .evidence-check {{color:{_SUCCESS}; font-weight:700;}}
    .evidence-empty {{color:#334155;}}

    /* Risk hero card */
    .risk-hero {{
        background:{_CARD}; border:1px solid {_BORDER};
        border-radius:16px; padding:1.5rem 1.8rem; text-align:center;
        margin:0.4rem 0; overflow:hidden;
    }}
    .risk-hero::before {{
        content:''; display:block;
        height:3px; margin:-1.5rem -1.8rem 1rem -1.8rem;
    }}
    .risk-hero.rh-low::before {{background:linear-gradient(90deg,transparent,{_SUCCESS},transparent);}}
    .risk-hero.rh-medium::before {{background:linear-gradient(90deg,transparent,{_WARN},transparent);}}
    .risk-hero.rh-high::before {{background:linear-gradient(90deg,transparent,{_DANGER},transparent);}}
    .risk-hero.rh-critical::before {{background:linear-gradient(90deg,transparent,{_DANGER},transparent);}}
    .risk-hero .rh-level {{
        font-size:0.68rem; text-transform:uppercase; letter-spacing:2px;
        font-weight:700; margin:0 0 0.25rem 0;
    }}
    .risk-hero .rh-score {{
        font-size:3.8rem; font-weight:900; letter-spacing:-3px;
        line-height:1; margin:0;
    }}
    .risk-hero .rh-sub {{
        font-size:0.74rem; color:{_TEXT3}; margin:0.3rem 0 0 0;
    }}
    .risk-hero .rh-summary {{
        font-size:0.82rem; color:{_TEXT2}; margin:0.7rem auto 0;
        max-width:480px; line-height:1.5;
    }}

    /* Partial notice */
    .partial-notice {{
        background:rgba(245,158,11,0.06); border:1px solid rgba(245,158,11,0.12);
        border-radius:10px; padding:0.6rem 1rem; margin:0.4rem 0;
        font-size:0.78rem; color:{_WARN};
    }}
    .partial-notice p {{color:{_TEXT2}; font-size:0.76rem; margin:0.15rem 0 0 0;}}

    /* Degraded notice */
    .degraded-notice {{
        background:rgba(239,68,68,0.06); border:1px solid rgba(239,68,68,0.12);
        border-radius:10px; padding:0.6rem 1rem; margin:0.3rem 0;
        font-size:0.78rem; color:{_DANGER};
    }}

    /* Result cards */
    .result-card {{
        background:{_CARD}; border:1px solid {_BORDER};
        border-radius:14px; padding:1rem 1.2rem; margin:0.3rem 0;
    }}
    .result-card h4 {{
        font-size:0.84rem; font-weight:700; color:{_TEXT};
        margin:0 0 0.45rem 0;
    }}

    /* Signal rows */
    .signal-row {{
        display:flex; align-items:center; gap:0.5rem;
        padding:0.35rem 0;
        border-bottom:1px solid rgba(255,255,255,0.03);
    }}
    .signal-name {{flex:2; font-weight:500; font-size:0.78rem; color:#CBD5E1;}}
    .signal-bar-bg {{
        flex:3; height:3px; border-radius:2px;
        background:rgba(255,255,255,0.05); overflow:hidden;
    }}
    .signal-bar-fill {{height:100%; border-radius:2px; transition:width 0.5s ease;}}
    .signal-val {{
        min-width:44px; text-align:right; font-size:0.73rem;
        font-family:'JetBrains Mono','SF Mono',monospace !important;
        color:{_TEXT3};
    }}

    /* Modality cards */
    .mod-cards {{display:grid; grid-template-columns:repeat(2,1fr); gap:0.5rem;}}
    .mod-card {{
        background:{_SURFACE}; border:1px solid rgba(255,255,255,0.04);
        border-radius:12px; padding:0.75rem 0.9rem;
    }}
    .mod-card .mod-header {{
        display:flex; align-items:center; justify-content:space-between;
        margin-bottom:0.3rem;
    }}
    .mod-card .mod-name {{
        font-size:0.7rem; font-weight:600; color:#CBD5E1;
        text-transform:uppercase; letter-spacing:0.5px;
    }}
    .mod-card .mod-score {{
        font-size:1rem; font-weight:800;
        font-family:'JetBrains Mono',monospace !important;
    }}
    .mod-card .mod-bar {{
        height:2px; background:rgba(255,255,255,0.05);
        border-radius:1px; overflow:hidden; margin-bottom:0.3rem;
    }}
    .mod-card .mod-bar-fill {{height:100%; border-radius:1px;}}
    .mod-card .mod-detail {{font-size:0.68rem; color:{_TEXT3};}}

    /* Timeline */
    .tl-row {{
        display:flex; align-items:flex-start; gap:0.5rem;
        padding:0.35rem 0; border-bottom:1px solid rgba(255,255,255,0.03);
    }}
    .tl-time {{
        font-family:'JetBrains Mono',monospace !important;
        font-size:0.7rem; color:{_TEXT3}; min-width:44px; padding-top:2px;
    }}
    .tl-dot {{width:6px; height:6px; border-radius:50%; margin-top:5px; flex-shrink:0;}}
    .tl-dot-info {{background:#334155;}}
    .tl-dot-warning {{background:{_WARN};}}
    .tl-dot-critical {{background:{_DANGER};}}
    .tl-text {{font-size:0.78rem; color:#CBD5E1; line-height:1.4;}}

    /* Care stepper */
    .care-stepper {{
        display:flex; gap:0; margin:0.4rem 0; overflow:hidden;
        border-radius:12px; border:1px solid {_BORDER};
    }}
    .care-step {{
        flex:1; text-align:center; padding:0.6rem 0.4rem;
        background:{_CARD}; border-right:1px solid rgba(255,255,255,0.04);
    }}
    .care-step:last-child {{border-right:none;}}
    .care-step.active {{
        background:rgba(237,20,91,0.06);
        border-bottom:2px solid {_PRIMARY};
    }}
    .care-step .cs-label {{font-size:0.7rem; font-weight:700;}}
    .care-step .cs-sub {{font-size:0.6rem; color:#475569; margin-top:0.08rem;}}

    /* Limitations */
    .limitations {{
        background:rgba(255,255,255,0.02);
        border:1px solid rgba(255,255,255,0.04);
        border-radius:10px; padding:0.7rem 1rem; margin:0.6rem 0;
    }}
    .limitations h5 {{
        font-size:0.7rem; text-transform:uppercase; letter-spacing:1.5px;
        color:#475569; font-weight:700; margin:0 0 0.2rem 0;
    }}
    .limitations p {{
        font-size:0.74rem; color:#475569; margin:0; line-height:1.6;
    }}

    /* Responsive */
    @media (max-width:768px) {{
        .evidence-grid {{grid-template-columns:repeat(2,1fr);}}
        .mod-cards {{grid-template-columns:1fr;}}
        .care-stepper {{flex-wrap:wrap;}}
        .care-step {{flex:1 1 45%;}}
    }}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════
LEVEL_LABELS_PT = {"low": "Baixo", "medium": "Moderado", "high": "Elevado", "critical": "Crítico"}
LEVEL_COLORS = {"low": _SUCCESS, "medium": _WARN, "high": _DANGER, "critical": _DANGER}
PATHWAY_LABELS = {
    "acompanhamento_rotina": "Acompanhamento de Rotina",
    "coleta_adicional": "Coleta Adicional de Dados",
    "acolhimento_e_monitoramento": "Acolhimento e Monitoramento",
    "revisao_prioritaria": "Revisão Prioritária",
}
PATHWAY_ORDER = ["acompanhamento_rotina", "coleta_adicional", "acolhimento_e_monitoramento", "revisao_prioritaria"]
PATHWAY_SHORT = {
    "acompanhamento_rotina": "Rotina",
    "coleta_adicional": "Coleta",
    "acolhimento_e_monitoramento": "Acolhimento",
    "revisao_prioritaria": "Prioritária",
}
RISK_LABELS = {"ROTINA": "Rotina", "MONITORAR": "Monitorar", "URGENTE": "Urgente"}
STAGE_LABELS = {
    "text_extraction": "Processando relato",
    "audio_extraction": "Extraindo padrões emocionais",
    "audio_emotion": "Classificando emoções",
    "pose_extraction": "Analisando postura",
    "motion_extraction": "Analisando movimento corporal",
    "visual_wellbeing": "Avaliando bem-estar visual",
    "object_detection": "Detectando objetos de risco",
    "fusion_engine": "Aplicando fusão multimodal",
    "risk_engine": "Calculando risco",
    "care_engine": "Gerando recomendação",
}
MOD_LABELS = {"audio": "Áudio", "text": "Texto", "video": "Vídeo", "objects": "Objetos"}
MOD_COLORS = {"audio": _PRIMARY, "text": "#a78bfa", "video": "#38bdf8", "objects": _WARN}

# ═══════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""<div class="sidebar-brand">
        <div class="brand-name">Sentinela<span class="brand-dot">.</span> Care AI</div>
        <div class="brand-sub">Inteligência Multimodal de Segurança</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<p class="section-label" style="margin-top:0.2rem;">Fontes de Entrada</p>', unsafe_allow_html=True)

    st.markdown('<div class="upload-label">📝 Relato ou transcrição</div>', unsafe_allow_html=True)
    transcript_text = st.text_area(
        "Relato", placeholder="Cole aqui um relato, transcrição ou descrição do caso...",
        height=72, label_visibility="collapsed",
    )

    st.markdown('<div class="upload-label">🎤 Áudio (.wav)</div>', unsafe_allow_html=True)
    audio_file = st.file_uploader("Áudio", type=["wav"], label_visibility="collapsed", key="audio_up")

    st.markdown('<div class="upload-label">🎥 Vídeo (.mp4 .avi .mov)</div>', unsafe_allow_html=True)
    video_file = st.file_uploader("Vídeo", type=["mp4", "avi", "mov"], label_visibility="collapsed", key="video_up")

    st.markdown('<div class="upload-label">🖼️ Imagem (.jpg .png .jpeg)</div>', unsafe_allow_html=True)
    image_file = st.file_uploader("Imagem", type=["jpg", "jpeg", "png"], label_visibility="collapsed", key="image_up")

    st.markdown('<p class="section-label">Análise</p>', unsafe_allow_html=True)
    run_analysis = st.button("Analisar com Sentinela", type="primary", use_container_width=True)

    with st.expander("Sobre o Sentinela", expanded=False):
        st.caption(
            "Sistema multimodal de apoio à identificação de sinais de risco e sofrimento. "
            "Processa áudio, texto, vídeo e objetos em trilhas de cuidado trauma-informadas. "
            "Ferramenta de apoio à decisão — nunca diagnóstico automatizado."
        )
        st.caption("POSTECH IADT · Tech Challenge Fase 4")


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _pill(level: str) -> str:
    label = LEVEL_LABELS_PT.get(level, level)
    return (
        f'<span style="display:inline-block;padding:0.15rem 0.55rem;border-radius:20px;'
        f'font-weight:700;font-size:0.66rem;letter-spacing:0.5px;text-transform:uppercase;'
        f'background:rgba(255,255,255,0.05);color:{LEVEL_COLORS.get(level, _TEXT3)};">'
        f'{label}</span>'
    )


def make_radar_chart(report: dict[str, Any]) -> go.Figure | None:
    ms = report.get("modality_scores", {})
    care_dims = (report.get("care_assessment") or {}).get("dimensions", {})
    labels, values = [], []
    for key, label in [("audio", "Áudio"), ("text", "Texto"), ("video", "Vídeo"), ("objects", "Objetos")]:
        if key in ms:
            labels.append(label)
            values.append(ms[key].get("score_0_1", 0))
    for key, label in [("wellbeingIndex", "Bem-Estar"), ("safetySignal", "Segurança"),
                       ("nonverbalAlert", "Não-Verbal"), ("affectiveDistress", "Afeto")]:
        if key in care_dims:
            labels.append(label)
            values.append(care_dims[key])
    if not values:
        return None
    values_c = values + [values[0]]
    labels_c = labels + [labels[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_c, theta=labels_c,
        fill="toself",
        fillcolor="rgba(237,20,91,0.06)",
        line=dict(color=_PRIMARY, width=2),
        marker=dict(size=5, color=_PRIMARY),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], tickvals=[0.25, 0.5, 0.75],
                            ticktext=["", "0.5", ""],
                            tickfont=dict(size=9, color="#525252", family="Inter"),
                            gridcolor="rgba(255,255,255,0.03)", linecolor="rgba(255,255,255,0.02)"),
            angularaxis=dict(tickfont=dict(size=11, color=_TEXT2, family="Inter"),
                             gridcolor="rgba(255,255,255,0.03)", linecolor="rgba(255,255,255,0.02)"),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False, margin=dict(l=55, r=55, t=25, b=25),
        height=360, paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"),
    )
    return fig


def make_modality_cards_html(modality_scores: dict[str, dict]) -> str:
    cards = []
    for key in ["text", "audio", "video", "objects"]:
        if key not in modality_scores:
            continue
        s = modality_scores[key].get("score_0_1", 0)
        pct = max(1, int(s * 100))
        c = MOD_COLORS.get(key, _PRIMARY)
        name = MOD_LABELS.get(key, key)
        ev = modality_scores[key].get("evidence", {})
        detail = ""
        if key == "text":
            labels = ev.get("labels", {})
            active = [k.replace("_", " ") for k, v in labels.items()
                      if isinstance(v, dict) and v.get("score", 0) > 0]
            if active:
                detail = ", ".join(active[:3])
        elif key == "audio":
            emo = ev.get("emotion_baseline", {})
            if emo.get("available"):
                detail = f"emoção: {emo.get('predictedEmotion', '?')}"
        elif key == "video":
            detail = f"modo: {ev.get('mode', '?')}"
        elif key == "objects":
            det_count = ev.get("risk_detections", 0)
            detail = f"{det_count} detecção(ões)" if det_count else "nenhuma detecção"
        sc = _DANGER if s > 0.6 else _WARN if s > 0.3 else _SUCCESS
        cards.append(f"""<div class="mod-card">
            <div class="mod-header">
                <div class="mod-name" style="color:{c};">{name}</div>
                <div class="mod-score" style="color:{sc};">{s:.3f}</div>
            </div>
            <div class="mod-bar"><div class="mod-bar-fill" style="width:{pct}%;background:{c};"></div></div>
            <div class="mod-detail">{detail}</div>
        </div>""")
    return f'<div class="mod-cards">{"".join(cards)}</div>'


def build_explainability(report: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    ms = report.get("modality_scores", {})
    weights = report.get("weights", {})
    audio = ms.get("audio", {})
    if audio:
        score = audio.get("score_0_1", 0)
        ev = audio.get("evidence", {})
        comps = ev.get("components", {})
        emo = ev.get("emotion_baseline", {})
        if score > 0:
            signals.append({"signal": "Distress vocal", "value": round(score * weights.get("audio", 0), 3),
                            "detail": f"variabilidade={comps.get('variability', 0):.2f}"})
        if emo.get("available"):
            signals.append({"signal": f"Emoção: {emo.get('predictedEmotion', '?')}", "value": round(emo.get("confidence", 0) * 0.15, 3),
                            "detail": f"confiança={emo.get('confidence', 0):.2f}"})
    text = ms.get("text", {})
    if text:
        label_pt = {"safety_concern": "segurança", "coercion": "coerção", "isolation": "isolamento",
                    "hopelessness": "desesperança", "psychological_distress": "distress psicológico"}
        for lbl, data in sorted((text.get("evidence", {}).get("labels", {})).items(),
                                 key=lambda x: x[1].get("score", 0) if isinstance(x[1], dict) else 0, reverse=True):
            if isinstance(data, dict) and data.get("score", 0) > 0:
                signals.append({"signal": f"Texto: {label_pt.get(lbl, lbl.replace('_', ' '))}", "value": round(data["score"] * weights.get("text", 0), 3),
                                "detail": ", ".join(data.get("hits", [])[:3])})
    video = ms.get("video", {})
    if video and video.get("score_0_1", 0) > 0:
        ev = video.get("evidence", {})
        mode_pt = {"motion": "movimento", "visual_wellbeing": "bem-estar visual", "pose": "postura"}
        signals.append({"signal": f"Vídeo: {mode_pt.get(ev.get('mode', '?'), ev.get('mode', '?'))}", "value": round(video["score_0_1"] * weights.get("video", 0), 3),
                        "detail": f"modo={ev.get('mode', '?')}"})
    objects = ms.get("objects", {})
    if objects and objects.get("score_0_1", 0) > 0:
        signals.append({"signal": "Objeto cortante", "value": round(objects["score_0_1"] * weights.get("objects", 0), 3),
                        "detail": f"detecções={objects.get('evidence', {}).get('risk_detections', 0)}"})
    return sorted(signals, key=lambda s: s["value"], reverse=True)


def build_timeline_events(report: dict[str, Any]) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    trace = report.get("_trace", {})
    ms = report.get("modality_scores", {})
    cumulative = 0.0
    for s in trace.get("stages", []):
        name = s.get("stage", "")
        cumulative += s.get("elapsed_ms", 0)
        ts = f"{cumulative / 1000:.2f}s"
        if name == "text_extraction" and ms.get("text", {}).get("score_0_1", 0) > 0.3:
            sc = ms["text"]["score_0_1"]
            events.append({"time": ts, "text": f"Sinais textuais detectados (score {sc:.2f})", "sev": "warning" if sc > 0.5 else "info"})
        elif name == "audio_extraction" and ms.get("audio", {}).get("score_0_1", 0) > 0.2:
            sc = ms["audio"]["score_0_1"]
            events.append({"time": ts, "text": f"Indicador de distress vocal (score {sc:.2f})", "sev": "warning" if sc > 0.5 else "info"})
        elif name == "audio_emotion":
            emo = ms.get("audio", {}).get("evidence", {}).get("emotion_baseline", {})
            if emo.get("available"):
                events.append({"time": ts, "text": f"Emoção classificada: {emo.get('predictedEmotion', '?')}", "sev": "info"})
        elif name == "object_detection" and ms.get("objects", {}).get("score_0_1", 0) > 0:
            sc = ms["objects"]["score_0_1"]
            events.append({"time": ts, "text": f"Objeto cortante detectado (score {sc:.2f})", "sev": "critical" if sc > 0.7 else "warning"})
        elif name == "fusion_engine":
            lv = LEVEL_LABELS_PT.get(report.get("level", "?"), report.get("level", "?"))
            events.append({"time": ts, "text": f"Fusão multimodal — nível: {lv}", "sev": "info"})
        elif name == "care_engine":
            pw = (report.get("care_assessment") or {}).get("carePathway", "?")
            events.append({"time": ts, "text": f"Trilha: {PATHWAY_LABELS.get(pw, pw)}", "sev": "info"})
    return events


def generate_summary_short(report: dict[str, Any]) -> str:
    level = report.get("level", "low")
    score = report.get("multimodal_score_0_1", 0)
    mods = list(report.get("modality_scores", {}).keys())
    level_desc = {"low": "Perfil de baixo risco", "medium": "Indicadores moderados de distress",
                  "high": "Indicadores elevados de risco", "critical": "Perfil de risco crítico"}
    mod_label = "modalidade" if len(mods) == 1 else "modalidades"
    return f"{level_desc.get(level, 'Desconhecido')} detectado em {len(mods)} {mod_label} (score: {score:.3f})."


def generate_executive_summary(report: dict[str, Any]) -> str:
    level = report.get("level", "low")
    score = report.get("multimodal_score_0_1", 0)
    care = report.get("care_assessment", {})
    priority = report.get("priority", {})
    mods = list(report.get("modality_scores", {}).keys())
    level_desc = {"low": "Perfil de baixo risco", "medium": "Indicadores moderados de distress",
                  "high": "Indicadores elevados de risco", "critical": "Perfil de risco crítico"}
    mod_label = "modalidade" if len(mods) == 1 else "modalidades"
    parts = [f"**{level_desc.get(level, 'Desconhecido')}** detectado em {len(mods)} "
             f"{mod_label} (score de fusão: {score:.3f})."]
    sigs = build_explainability(report)
    if sigs:
        top = sigs[:3]
        parts.append("Sinais principais: " + " · ".join(f"{s['signal']} (+{s['value']:.3f})" for s in top) + ".")
    pw = care.get("carePathway", "")
    if pw:
        parts.append(f"Trilha recomendada: **{PATHWAY_LABELS.get(pw, pw)}**.")
    if priority.get("humanReviewRequired"):
        parts.append("⚠ Avaliação assistida por profissional recomendada.")
    else:
        parts.append("Continuar monitoramento de rotina.")
    return "\n\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# Main flow
# ═══════════════════════════════════════════════════════════════════════════
if run_analysis:
    has_input = bool(transcript_text.strip()) or audio_file or video_file or image_file
    if not has_input:
        st.markdown(f"""<div class="input-hero" style="text-align:center;padding:1.5rem;">
            <h3>Nenhuma entrada detectada</h3>
            <p>Adicione pelo menos uma modalidade na barra lateral para iniciar a análise.</p>
            <div class="evidence-grid" style="max-width:440px;margin:0.8rem auto 0;">
                <div class="evidence-item"><span class="evidence-empty">○</span> Texto</div>
                <div class="evidence-item"><span class="evidence-empty">○</span> Áudio</div>
                <div class="evidence-item"><span class="evidence-empty">○</span> Vídeo</div>
                <div class="evidence-item"><span class="evidence-empty">○</span> Imagem</div>
            </div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    # Context hint
    if (image_file or video_file or audio_file) and not transcript_text.strip():
        st.info("💡 **Dica:** adicionar uma descrição do contexto pode aumentar a precisão da interpretação multimodal.")

    # Save files
    tmpdir = tempfile.mkdtemp(prefix="sentinela_")
    kwargs: dict[str, Any] = {}
    if transcript_text.strip():
        txt_path = Path(tmpdir) / "transcript.txt"
        txt_path.write_text(transcript_text.strip(), encoding="utf-8")
        kwargs["transcript"] = txt_path
    if audio_file:
        p = Path(tmpdir) / audio_file.name; p.write_bytes(audio_file.read())
        kwargs["audio_wav"] = p
    if video_file:
        p = Path(tmpdir) / video_file.name; p.write_bytes(video_file.read())
        kwargs["video_file"] = p
    if image_file:
        p = Path(tmpdir) / image_file.name; p.write_bytes(image_file.read())
        kwargs["image_for_objects"] = p

    # Pipeline execution
    progress_ph = st.empty()
    with progress_ph.container():
        st.progress(0, text="Inicializando pipeline…")

    try:
        pipeline = SentinelaPipeline()
    except Exception as e:
        logger.error("Pipeline init failed: %s", e)
        st.markdown(f'<div class="degraded-notice"><strong>Erro na inicialização</strong> — {e}</div>', unsafe_allow_html=True)
        st.stop()

    t0 = time.perf_counter()
    try:
        report = pipeline.analyze(**kwargs)
    except Exception as e:
        logger.error("Pipeline error: %s", e)
        st.markdown(f'<div class="degraded-notice"><strong>Erro no pipeline</strong> — {e}</div>', unsafe_allow_html=True)
        st.stop()

    elapsed = time.perf_counter() - t0

    # Stage-by-stage progress
    stages_done = report.get("_trace", {}).get("stages", [])
    for i, stg in enumerate(stages_done):
        pct = int(5 + (i + 1) / max(len(stages_done), 1) * 90)
        lbl = STAGE_LABELS.get(stg["stage"], stg["stage"])
        with progress_ph.container():
            st.progress(pct, text=f"✓ {lbl}")
        time.sleep(0.04)
    with progress_ph.container():
        st.progress(100, text=f"✓ Análise concluída — {elapsed:.2f}s")
    time.sleep(0.25)
    progress_ph.empty()

    # === EXTRACT ===
    level = report.get("level", "low")
    score = report.get("multimodal_score_0_1", 0)
    priority = report.get("priority", {})
    care = report.get("care_assessment", {})
    risk_level = priority.get("riskLevel", "ROTINA")
    conf = priority.get("confidence", 0)
    review = priority.get("humanReviewRequired", False)
    ms = report.get("modality_scores", {})
    active_modalities = len(ms)
    is_partial = active_modalities < 4
    pipeline_warnings = report.get("_warnings", [])
    pathway = care.get("carePathway", "")
    pathway_label = PATHWAY_LABELS.get(pathway, pathway)
    score_100 = int(score * 100)
    level_color = LEVEL_COLORS.get(level, _TEXT3)

    # Pipeline degradation warnings
    for w in pipeline_warnings:
        st.markdown(
            f'<div class="degraded-notice"><strong>Modalidade indisponível</strong> — {w}. '
            f'A análise continuou com as evidências disponíveis.</div>',
            unsafe_allow_html=True,
        )

    # ═══════════════════════════════════════════════════════════════
    # HERO RISK CARD
    # ═══════════════════════════════════════════════════════════════
    summary_short = generate_summary_short(report)
    st.markdown(f"""<div class="risk-hero rh-{level}">
        <p class="rh-level" style="color:{level_color};">Risco {LEVEL_LABELS_PT.get(level, level)}</p>
        <p class="rh-score" style="color:{level_color};">{score_100}</p>
        <p class="rh-sub">score multimodal · confiança {conf:.0%} · {active_modalities} modalidade{"s" if active_modalities > 1 else ""}</p>
        <p class="rh-summary">{summary_short}</p>
    </div>""", unsafe_allow_html=True)

    # Partial notice
    if is_partial:
        rec = ("Adicione um relato clínico para enriquecer a análise." if "text" not in ms
               else "Adicione modalidades complementares para maior confiança.")
        st.markdown(f"""<div class="partial-notice">
            <strong>Modo de análise parcial</strong>
            <p>Análise com {active_modalities}/4 modalidades. {rec}</p>
        </div>""", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # TWO-COLUMN RESULTS
    # ═══════════════════════════════════════════════════════════════
    st.markdown('<p class="section-label">Análise Detalhada</p>', unsafe_allow_html=True)
    col_left, col_right = st.columns([1, 1])

    with col_left:
        signals = build_explainability(report)
        st.markdown(f"""<div class="result-card">
            <h4>Explicabilidade</h4>
            <p style="font-size:0.76rem;color:{_TEXT3};margin:0 0 0.4rem 0;">Por que o Sentinela chegou a esta conclusão:</p>
        """, unsafe_allow_html=True)
        if signals:
            for s in signals[:5]:
                val = s["value"]
                c = _DANGER if val > 0.15 else _WARN if val > 0.05 else _SUCCESS
                pct = max(2, min(int(val / 0.3 * 100), 100))
                st.markdown(f"""<div class="signal-row">
                    <div class="signal-name">{s['signal']}</div>
                    <div class="signal-bar-bg"><div class="signal-bar-fill" style="width:{pct}%;background:{c};"></div></div>
                    <div class="signal-val" style="color:{c};">+{val:.3f}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f'<p style="font-size:0.78rem;color:{_TEXT3};">Nenhum sinal significativo detectado.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        cards_html = make_modality_cards_html(ms)
        if cards_html:
            st.markdown(f'<div style="margin-top:0.5rem;">{cards_html}</div>', unsafe_allow_html=True)

    with col_right:
        fig_radar = make_radar_chart(report)
        if fig_radar:
            st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})

        events = build_timeline_events(report)
        if events:
            st.markdown('<div class="result-card"><h4>Timeline</h4>', unsafe_allow_html=True)
            for ev in events:
                sev = ev.get("sev", "info")
                st.markdown(f"""<div class="tl-row">
                    <div class="tl-time">{ev['time']}</div>
                    <div class="tl-dot tl-dot-{sev}"></div>
                    <div class="tl-text">{ev['text']}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # CARE PATHWAY STEPPER
    # ═══════════════════════════════════════════════════════════════
    st.markdown('<p class="section-label">Recomendação de Cuidado</p>', unsafe_allow_html=True)

    stepper_html = '<div class="care-stepper">'
    for pw_key in PATHWAY_ORDER:
        is_active = "active" if pw_key == pathway else ""
        color = f"color:{_PRIMARY};" if pw_key == pathway else f"color:{_TEXT3};"
        stepper_html += f"""<div class="care-step {is_active}">
            <div class="cs-label" style="{color}">{PATHWAY_SHORT[pw_key]}</div>
            <div class="cs-sub">{PATHWAY_LABELS[pw_key].split()[-1] if pw_key != pathway else '● Ativa'}</div>
        </div>"""
    stepper_html += '</div>'
    st.markdown(stepper_html, unsafe_allow_html=True)

    review_focus = care.get("reviewFocus", [])
    guardrails = care.get("guardrails", [])
    if review_focus or guardrails:
        with st.expander("Detalhes da Trilha de Cuidado", expanded=False):
            if review_focus:
                st.markdown("**Foco de Revisão:**")
                for item in review_focus:
                    st.markdown(f"- {item}")
            if guardrails:
                st.markdown("**Guardrails:**")
                for g in guardrails:
                    st.caption(f"• {g}")

    # AI Assessment
    st.markdown('<p class="section-label">Avaliação da IA</p>', unsafe_allow_html=True)
    summary_full = generate_executive_summary(report)
    st.markdown(summary_full)

    # ═══════════════════════════════════════════════════════════════
    # LIMITATIONS
    # ═══════════════════════════════════════════════════════════════
    st.markdown(f"""<div class="limitations">
        <h5>Limitações da Análise</h5>
        <p>Esta análise utiliza modelos baseline com capacidade limitada de generalização.
        Os resultados são indicativos e não substituem avaliação profissional.
        A precisão varia conforme a qualidade e representatividade dos dados de entrada.
        Sistema projetado como ferramenta de apoio à decisão.</p>
    </div>""", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # ENGINEERING (collapsed)
    # ═══════════════════════════════════════════════════════════════
    with st.expander("Trace do Pipeline", expanded=False):
        trace_data = report.get("_trace", {})
        st.caption(f"Request: {trace_data.get('request_id', 'N/A')} · {trace_data.get('total_ms', 0):.1f}ms · {len(stages_done)} etapas")
        for s in trace_data.get("stages", []):
            lbl = STAGE_LABELS.get(s["stage"], s["stage"])
            st.caption(f"✓ {lbl} — {s['elapsed_ms']:.1f}ms")

    with st.expander("JSON Completo", expanded=False):
        st.json(report)

else:
    # ═══════════════════════════════════════════════════════════════
    # WELCOME STATE — compact, above the fold
    # ═══════════════════════════════════════════════════════════════

    # Hero
    st.markdown("""<div class="sentinela-hero">
        <h1>Sentinela<span class="hero-dot">.</span> Care AI</h1>
        <p class="subtitle">Inteligência multimodal para identificação de sinais de sofrimento,
        risco e vulnerabilidade feminina.</p>
        <div class="sentinela-badge-row">
            <span class="sentinela-badge primary">FIAP Tech Challenge</span>
            <span class="sentinela-badge">Multimodal AI</span>
            <span class="sentinela-badge">Explainable</span>
            <span class="sentinela-badge">Trauma-Informed</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # KPI row
    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1:
        st.markdown("""<div class="kpi-card">
            <div class="kpi-value">4</div>
            <div class="kpi-label">Modalidades</div>
        </div>""", unsafe_allow_html=True)
    with kc2:
        st.markdown("""<div class="kpi-card">
            <div class="kpi-value">Fusão Tardia</div>
            <div class="kpi-label">Estratégia</div>
        </div>""", unsafe_allow_html=True)
    with kc3:
        st.markdown("""<div class="kpi-card">
            <div class="kpi-value">4 Trilhas</div>
            <div class="kpi-label">Cuidado</div>
        </div>""", unsafe_allow_html=True)
    with kc4:
        st.markdown("""<div class="kpi-card">
            <div class="kpi-value">5</div>
            <div class="kpi-label">Baselines</div>
        </div>""", unsafe_allow_html=True)

    # Two-column body: left = ready card, right = radar chart
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown(f"""<div class="input-hero">
            <h3>Pronto para análise</h3>
            <p>O Sentinela adapta automaticamente a análise às evidências disponíveis.
            Envie uma ou mais modalidades na barra lateral:</p>
            <div class="evidence-grid">
                <div class="evidence-item"><span class="evidence-check">✓</span> Relato</div>
                <div class="evidence-item"><span class="evidence-check">✓</span> Áudio</div>
                <div class="evidence-item"><span class="evidence-check">✓</span> Vídeo</div>
                <div class="evidence-item"><span class="evidence-check">✓</span> Imagem</div>
            </div>
        </div>""", unsafe_allow_html=True)

    with col2:
        # Static radar chart demonstrating modality balance
        _demo_labels = ["Texto", "Áudio", "Objetos", "Vídeo", "Texto"]
        _demo_values = [0.65, 0.70, 0.55, 0.60, 0.65]
        _fig_welcome = go.Figure()
        _fig_welcome.add_trace(go.Scatterpolar(
            r=_demo_values, theta=_demo_labels,
            fill="toself",
            fillcolor="rgba(237,20,91,0.06)",
            line=dict(color=_PRIMARY, width=2),
            marker=dict(size=5, color=_PRIMARY),
        ))
        _fig_welcome.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1], tickvals=[0.25, 0.5, 0.75],
                                ticktext=["", "0.5", ""],
                                tickfont=dict(size=9, color="#525252", family="Inter"),
                                gridcolor="rgba(255,255,255,0.03)", linecolor="rgba(255,255,255,0.02)"),
                angularaxis=dict(tickfont=dict(size=11, color=_TEXT2, family="Inter"),
                                 gridcolor="rgba(255,255,255,0.03)", linecolor="rgba(255,255,255,0.02)"),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=False, margin=dict(l=55, r=55, t=25, b=25),
            height=340, paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"),
        )
        st.plotly_chart(_fig_welcome, use_container_width=True, config={"displayModeBar": False})

    # How it works
    with st.expander("Como o Sentinela funciona", expanded=False):
        st.markdown("""
**Pipeline de análise em 4 modalidades:**
- **Texto** — NLP em português com detecção multi-label de sinais
- **Áudio** — Extração de features acústicas + baseline emocional
- **Vídeo** — Estimação de postura, movimento e bem-estar visual
- **Objetos** — Detecção de objetos cortantes via YOLOv8

**Fusão e Cuidado:**
Fusão tardia com normalização ponderada por confiança.
Motor de cuidado trauma-informado com 4 trilhas e guardrails.
""")
