from __future__ import annotations

import streamlit as st


def render_sidebar(*, api_key_ok: bool) -> dict:
    st.sidebar.markdown(
        """
<div style="display:flex; align-items:center; gap:10px; padding: 10px 6px 2px 6px;">
  <div style="
    width:42px;height:42px;border-radius:16px;
    background: linear-gradient(135deg, rgba(124,58,237,0.55), rgba(6,182,212,0.30));
    border: 1px solid rgba(255,255,255,0.10);
    display:flex;align-items:center;justify-content:center;
    box-shadow: 0 18px 45px rgba(0,0,0,0.35);
  ">🏨</div>
  <div>
    <div style="font-weight:800; letter-spacing:-0.02em; font-size:16px;">Hotel MAS</div>
    <div style="color:#9CA3AF; font-size:12px; margin-top:1px;">Multi‑Agent Support Platform</div>
  </div>
</div>
<div class="divider"></div>
""",
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("### ⚙️ Settings")
    model = st.sidebar.selectbox(
        "Model",
        options=["gpt-4o-mini", "gpt-4o"],
        index=0,
        help="Used for all agents (fallback model is used for recovery).",
    )
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.0, 0.05)

    col1, col2 = st.sidebar.columns(2)
    clear = col1.button("🧹 Clear", use_container_width=True)
    new_thread = col2.button("➕ New", use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ✅ Status")
    st.sidebar.markdown(
        f"""
<div class="glass" style="padding: 10px 12px;">
  <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
    <div style="color:#9CA3AF; font-size:12px;">OpenAI key</div>
    <div style="font-weight:700;">{"Configured" if api_key_ok else "Missing"}</div>
  </div>
  <div style="margin-top:8px; height: 8px; border-radius:999px; background: rgba(255,255,255,0.06); overflow:hidden;">
    <div style="height:100%; width:{'100%' if api_key_ok else '18%'}; background: {'linear-gradient(90deg, rgba(34,197,94,0.95), rgba(6,182,212,0.65))' if api_key_ok else 'linear-gradient(90deg, rgba(239,68,68,0.95), rgba(245,158,11,0.65))'};"></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🕘 Session history")
    history = st.session_state.get("session_history", [])
    if not history:
        st.sidebar.caption("No past sessions yet.")
    else:
        for item in history[-10:][::-1]:
            st.sidebar.markdown(
                f"""
<div class="glass hover" style="padding: 10px 12px; margin-bottom:8px;">
  <div style="display:flex; align-items:center; justify-content:space-between; gap: 10px;">
    <div style="font-weight:650;">{str(item)[:8]}</div>
    <div class="muted mono" style="font-size:12px;">{str(item)[-6:]}</div>
  </div>
  <div class="muted" style="font-size:12px; margin-top:4px;">Previous conversation</div>
</div>
""",
                unsafe_allow_html=True,
            )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 Agent activity")
    activity = st.session_state.get("agent_activity", [])
    if not activity:
        st.sidebar.caption("No activity yet.")
    else:
        for step in activity[-12:][::-1]:
            st.sidebar.markdown(
                f"""
<div class="glass" style="padding: 9px 12px; margin-bottom:8px; border-radius: 16px;">
  <div style="display:flex; align-items:center; gap:10px;">
    <div style="width:8px;height:8px;border-radius:999px;background: rgba(6,182,212,0.9); box-shadow: 0 0 0 4px rgba(6,182,212,0.10);"></div>
    <div style="font-weight:650; font-size:13px;">{step}</div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

    return {"model": model, "temperature": temperature, "clear": clear, "new_thread": new_thread}

