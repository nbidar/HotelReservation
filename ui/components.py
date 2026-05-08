from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
<style>
/* ---- Premium theme tokens ---- */
:root{
  --bg0:#070A14;
  --bg1:#0B1020;         /* requested */
  --bg2:#111827;         /* requested */
  --card: rgba(17, 24, 39, 0.55);
  --card2: rgba(11, 16, 32, 0.55);
  --stroke: rgba(255,255,255,0.10);
  --stroke2: rgba(255,255,255,0.16);
  --text:#F9FAFB;        /* requested */
  --muted:#9CA3AF;       /* requested */
  --accent:#7C3AED;      /* requested */
  --cyan:#06B6D4;        /* requested */
  --success:#22C55E;
  --warn:#F59E0B;
  --danger:#EF4444;
  --r16:16px;
  --r20:20px;
  --r24:24px;
  --shadow: 0 20px 55px rgba(0,0,0,0.55);
  --shadow2: 0 10px 28px rgba(0,0,0,0.45);
}

/* Font (Inter) */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ---- App background + typography ---- */
html, body, [class*="css"]  {
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Apple Color Emoji", "Segoe UI Emoji";
}
html, body{
  overflow-x: hidden !important;
  overflow-y: auto !important;
}

/* Streamlit root */
section.main{
  background:
    radial-gradient(1200px 900px at 15% 10%, rgba(124, 58, 237, 0.16), rgba(7,10,20,0) 60%),
    radial-gradient(1100px 700px at 90% 15%, rgba(6, 182, 212, 0.14), rgba(7,10,20,0) 55%),
    linear-gradient(180deg, var(--bg0) 0%, var(--bg1) 45%, #070A14 100%);
  color: var(--text);
}

/* Wider layout + consistent padding */
.block-container{
  padding-top: 1.25rem;
  padding-bottom: 2.75rem;
  max-width: 1400px;
  padding-left: clamp(14px, 2.2vw, 28px);
  padding-right: clamp(14px, 2.2vw, 28px);
}

/* Kill default white background artifacts */
div[data-testid="stAppViewContainer"]{ background: transparent; }
div[data-testid="stHeader"]{ background: rgba(7,10,20,0.55); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(255,255,255,0.06); }
div[data-testid="stAppViewContainer"], section.main, .block-container{
  overflow-x: hidden !important;
}

/* Ensure vertical scrolling always works */
div[data-testid="stAppViewContainer"]{
  overflow-y: auto !important;
}

/* Prevent sticky header from covering hero title */
.block-container{
  padding-top: calc(1.25rem + 24px);
}

/* ---- Sidebar premium glass ---- */
section[data-testid="stSidebar"]{
  background:
    radial-gradient(900px 550px at 20% 10%, rgba(124, 58, 237, 0.18), rgba(17,24,39,0) 55%),
    radial-gradient(900px 520px at 85% 20%, rgba(6, 182, 212, 0.12), rgba(17,24,39,0) 55%),
    linear-gradient(180deg, rgba(11,16,32,0.92) 0%, rgba(17,24,39,0.82) 100%);
  border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] *{ color: var(--text); }
/* Sidebar width + spacing (responsive) */
section[data-testid="stSidebar"]{
  width: 310px;
}
@media (max-width: 1024px){
  section[data-testid="stSidebar"]{ width: 280px; }
}

/* ---- Premium controls ---- */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
div[data-baseweb="slider"] > div{
  background: rgba(17,24,39,0.55) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(12px);
}

button[kind="secondary"], button[kind="primary"]{
  border-radius: 14px !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
}
button[kind="secondary"]:hover, button[kind="primary"]:hover{
  transform: translateY(-1px);
  box-shadow: 0 16px 38px rgba(0,0,0,0.35);
  border-color: rgba(255,255,255,0.20) !important;
}

/* ---- Tabs styling ---- */
div[data-baseweb="tab-list"]{
  gap: 8px;
  padding: 6px 6px;
  border-radius: 999px;
  background: rgba(17,24,39,0.35);
  border: 1px solid rgba(255,255,255,0.08);
  backdrop-filter: blur(14px);
  flex-wrap: wrap;
}
button[data-baseweb="tab"]{
  border-radius: 999px !important;
  padding: 10px 14px !important;
  color: var(--muted) !important;
}
button[data-baseweb="tab"][aria-selected="true"]{
  color: var(--text) !important;
  background: linear-gradient(135deg, rgba(124,58,237,0.38), rgba(6,182,212,0.22)) !important;
  border: 1px solid rgba(124,58,237,0.35) !important;
  box-shadow: 0 0 0 1px rgba(124,58,237,0.15), 0 18px 40px rgba(124,58,237,0.12);
}

/* ---- Premium cards ---- */
.glass{
  background: var(--card);
  border: 1px solid var(--stroke);
  border-radius: var(--r20);
  padding: 14px 16px;
  box-shadow: var(--shadow2);
  backdrop-filter: blur(14px);
}
.glass.hover{
  transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
}
.glass.hover:hover{
  transform: translateY(-2px);
  border-color: rgba(255,255,255,0.18);
  box-shadow: var(--shadow);
}

.glow-border{
  position: relative;
}
.glow-border:before{
  content:"";
  position:absolute;
  inset:-1px;
  border-radius: var(--r20);
  background: linear-gradient(135deg, rgba(124,58,237,0.65), rgba(6,182,212,0.38), rgba(124,58,237,0.25));
  opacity: .55;
  z-index: -1;
  filter: blur(10px);
}

.metric{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap: 12px;
}
.metric .k{
  font-size: 12px;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--muted);
}
.metric .v{
  font-size: 22px;
  font-weight: 650;
  margin-top: 6px;
}
.metric .ic{
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display:flex;
  align-items:center;
  justify-content:center;
  background: linear-gradient(135deg, rgba(124,58,237,0.35), rgba(6,182,212,0.18));
  border: 1px solid rgba(255,255,255,0.10);
}
.metric .ic span{
  font-size: 18px;
}

/* ---- Header ---- */
.hero{
  margin-top: .35rem;
  margin-bottom: 1.15rem;
}
.hero-title{
  font-size: 28px;
  line-height: 1.15;
  font-weight: 750;
  letter-spacing: -0.02em;
  margin: 0;
}
.gradient-text{
  background: linear-gradient(90deg, #F9FAFB 0%, rgba(124,58,237,0.95) 35%, rgba(6,182,212,0.95) 70%, #F9FAFB 100%);
  -webkit-background-clip:text;
  background-clip:text;
  color: transparent;
}
.hero-sub{
  color: var(--muted);
  margin-top: 6px;
  font-size: 14px;
}
.status-pill{
  display:inline-flex;
  align-items:center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(17,24,39,0.55);
  border: 1px solid rgba(255,255,255,0.10);
  color: var(--muted);
}
.dot{
  width: 8px; height: 8px; border-radius: 999px;
  background: var(--success);
  box-shadow: 0 0 0 0 rgba(34,197,94,0.55);
  animation: pulse 1.6s infinite;
}
@keyframes pulse{
  0% { box-shadow: 0 0 0 0 rgba(34,197,94,0.55); }
  70% { box-shadow: 0 0 0 10px rgba(34,197,94,0.0); }
  100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.0); }
}

/* ---- Chat ---- */
div[data-testid="stChatMessage"]{
  border-radius: var(--r20);
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(17,24,39,0.35);
  backdrop-filter: blur(12px);
  padding: 10px 12px;
  max-width: 920px;
  margin-left: auto;
  margin-right: auto;
}

/* Differentiate user vs assistant message subtly */
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]){
  background: linear-gradient(135deg, rgba(124,58,237,0.12), rgba(17,24,39,0.30));
  border-color: rgba(124,58,237,0.20);
  margin-left: auto;
  margin-right: 0;
  max-width: 860px;
}
div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]){
  background: linear-gradient(135deg, rgba(6,182,212,0.10), rgba(17,24,39,0.30));
  border-color: rgba(6,182,212,0.18);
  margin-left: 0;
  margin-right: auto;
  max-width: 860px;
}

div[data-testid="stChatMessage"] p, div[data-testid="stChatMessage"] li{
  color: var(--text);
  font-size: 14px;
  line-height: 1.6;
}
div[data-testid="stChatMessage"] code{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  background: rgba(6,182,212,0.10);
  border: 1px solid rgba(6,182,212,0.16);
  padding: 2px 6px;
  border-radius: 10px;
}
div[data-testid="stChatMessage"] pre{
  background: rgba(7,10,20,0.75) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 16px !important;
  padding: 12px 12px !important;
}
.ts{
  color: var(--muted);
  font-size: 12px;
  margin-top: 6px;
}

/* Chat spacing */
div[data-testid="stChatMessage"] + div[data-testid="stChatMessage"]{
  margin-top: 10px;
}

/* Chat input polish */
div[data-testid="stChatInput"]{
  max-width: 920px;
  margin-left: auto;
  margin-right: auto;
}
div[data-testid="stChatInput"] textarea{
  border-radius: 18px !important;
  padding: 14px 14px !important;
  background: rgba(17,24,39,0.55) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
}
div[data-testid="stChatInput"] button{
  border-radius: 16px !important;
}

@media (max-width: 640px){
  div[data-testid="stChatMessage"],
  div[data-testid="stChatInput"]{
    max-width: 100%;
  }
  .hero-title{ font-size: 22px; }
}

/* Expander polish (execution steps etc.) */
details{
  border-radius: var(--r20);
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(17,24,39,0.35);
  padding: 10px 12px;
}
details summary{
  cursor: pointer;
  color: var(--text);
  font-weight: 650;
}

/* ---- Scrollbars ---- */
*::-webkit-scrollbar{ width: 10px; height: 10px; }
*::-webkit-scrollbar-thumb{
  background: linear-gradient(180deg, rgba(124,58,237,0.45), rgba(6,182,212,0.35));
  border-radius: 999px;
  border: 2px solid rgba(7,10,20,0.65);
}
*::-webkit-scrollbar-track{ background: rgba(7,10,20,0.35); }

/* ---- Utility ---- */
.muted{ color: var(--muted); }
.mono{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.divider{ height: 1px; background: rgba(255,255,255,0.08); margin: 10px 0; }

/* Reduce top padding of main menu area */
div[data-testid="stToolbar"]{ right: 0.75rem; }
</style>
""",
        unsafe_allow_html=True,
    )


@dataclass(frozen=True)
class Metric:
    label: str
    value: str
    icon: str
    hint: str | None = None


def hero_header(*, title: str, subtitle: str, status_text: str = "Online") -> None:
    st.markdown(
        f"""
<div class="hero">
  <div style="display:flex; align-items:flex-start; justify-content:space-between; gap: 12px;">
    <div>
      <div class="hero-title gradient-text">{title}</div>
      <div class="hero-sub">{subtitle}</div>
    </div>
    <div class="status-pill"><span class="dot"></span><span>{status_text}</span></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def metric_cards(metrics: Iterable[Metric], *, columns: int = 4) -> None:
    cols = st.columns(columns)
    for idx, m in enumerate(metrics):
        with cols[idx % columns]:
            hint = f"<div class='muted' style='margin-top:2px'>{m.hint}</div>" if m.hint else ""
            st.markdown(
                f"""
<div class="glass hover glow-border">
  <div class="metric">
    <div>
      <div class="k">{m.label}</div>
      <div class="v">{m.value}</div>
      {hint}
    </div>
    <div class="ic"><span>{m.icon}</span></div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )


def glass_panel(title: str, *, subtitle: str | None = None) -> None:
    sub = f"<div class='muted' style='margin-top:2px'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
<div class="glass glow-border" style="margin-top:12px;">
  <div style="display:flex; align-items:baseline; justify-content:space-between; gap: 10px;">
    <div style="font-weight:700; font-size: 16px;">{title}</div>
  </div>
  {sub}
</div>
""",
        unsafe_allow_html=True,
    )

