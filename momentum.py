"""Categorical cultural momentum display; colors do not imply numeric scores."""
from html import escape

import streamlit as st

STATUS_STYLES = {
    'growing': ('↑', '#166534', '#dcfce7'),
    'stable': ('→', '#854d0e', '#fef9c3'),
    'declining': ('↓', '#991b1b', '#fee2e2'),
    'changing': ('↔', '#1e40af', '#dbeafe'),
    'unverified': ('?', '#4b5563', '#f3f4f6'),
}


def momentum_status_html(status):
    normalized = status.strip().casefold() if isinstance(status, str) else 'unverified'
    normalized = normalized if normalized in STATUS_STYLES else 'unverified'
    icon, color, background = STATUS_STYLES[normalized]
    return (
        f'<div role="status" aria-label="Cultural momentum: {normalized}" '
        f'style="display:flex;align-items:center;gap:.7rem;padding:.8rem 1rem;'
        f'border-left:5px solid {color};border-radius:8px;background:{background};color:{color}">'
        f'<span aria-hidden="true" style="font-size:1.7rem;font-weight:700">{escape(icon)}</span>'
        '<div><div style="font-size:.8rem">Cultural momentum</div>'
        f'<strong style="font-size:1.15rem">{normalized.capitalize()}</strong></div></div>'
    )


def display_cultural_momentum(momentum):
    if not isinstance(momentum, dict):
        st.html(momentum_status_html(None))
        if momentum:
            st.write(momentum)
        return
    st.html(momentum_status_html(momentum.get('status')))
    # Keep the research explanation and any additional saved fields visible.
    for field, value in momentum.items():
        if field == 'status' or not value:
            continue
        st.markdown(f"#### {field.replace('_', ' ').capitalize()}")
        st.write(value)
