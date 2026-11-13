
import hashlib
import json
from datetime import datetime
from html import escape
import streamlit as st

from database import ( 
    create_tables,
    create_report_table, 
    get_reports,
    save_report
    )

from scout import run_scout
from audience import display_audience_blocks
from engagement import display_engagement_dashboard
from figures import display_key_figure_cards
from communities import display_relevant_communities
from momentum import display_cultural_momentum


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="AWA Scout",
    page_icon="🔎",
    layout="wide"
)

st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
[data-testid="stMainBlockContainer"] {
    padding-top: 3rem;
}
[class*="st-key-finding_reader"] {
    --scout-accent: #b65a38;
}
[class*="st-key-finding_reader"] h3 {
    font-family: "Inter", sans-serif;
    letter-spacing: -0.025em;
}
[class*="st-key-finding_reader"] h3.scout-section-heading {
    font-family: "Source Sans 3", "Source Sans Pro", sans-serif;
    font-size: .85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: #6b7280;
    background: rgba(107, 114, 128, .09);
    border-radius: 5px;
    padding: .65rem .85rem;
    margin: .75rem 0 .6rem;
    line-height: 1.4;
}
[class*="st-key-finding_reader"] h3.scout-section-heading.findings-heading {
    color: #b65a38;
    background: rgba(182, 90, 56, .12);
}
[class*="st-key-finding_reader"] [data-testid="stButton"] button {
    text-align: left;
    justify-content: flex-start;
    min-height: 3.5rem;
    border-radius: 6px;
    padding: 0.8rem 1rem;
}
[class*="st-key-finding_reader"] [data-testid="stButton"] button[kind="primary"] {
    background: #b65a38;
    border-color: #b65a38;
    color: white;
}
/* Scope to a keyed container: button keys are not CSS classes in all versions. */
[class*="st-key-findings_home_"] [data-testid="stVerticalBlock"] {
    gap: 0.3rem;
}
[class*="st-key-findings_home_"] [data-testid="stButton"] button {
    justify-content: flex-start !important;
    text-align: left !important;
    min-height: 0;
    padding: 0.35rem 0.65rem;
    border: 1px solid rgba(182, 90, 56, 0.22);
    background: rgba(182, 90, 56, 0.035);
    box-shadow: none;
    transition: background-color 150ms ease, border-color 150ms ease;
}
[class*="st-key-findings_home_"] [data-testid="stButton"] button > div {
    flex: 1;
    justify-content: flex-start !important;
    text-align: left !important;
}
[class*="st-key-findings_home_"] [data-testid="stButton"] button p {
    font-size: 1.2rem;
    font-weight: 600;
    text-align: left !important;
}
[class*="st-key-findings_home_"] [data-testid="stButton"] button:hover {
    color: #b65a38;
    background: rgba(182, 90, 56, 0.09);
    border-color: rgba(182, 90, 56, 0.45);
}
[class*="st-key-findings_home_"] [data-testid="stMarkdown"] p {
    margin-bottom: 0.35rem;
}
[class*="st-key-finding_reader"] [data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 10px;
}
@media (max-width: 760px) {
    [class*="st-key-finding_reader"] [data-testid="stHorizontalBlock"] {
        flex-direction: column;
    }
    [class*="st-key-finding_reader"] [data-testid="stColumn"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
}
</style>
""")

st.title("AWA Scout")
st.caption("Cultural intelligence and audience discovery")


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

# Ensure tables exist when the app starts.
create_tables()
create_report_table()


# --------------------------------------------------
# DISPLAY HELPERS
# --------------------------------------------------

def display_section_heading(title, findings=False):
    """Render a consistent divider-style report heading."""
    extra_class = " findings-heading" if findings else ""
    st.html(f'<h3 class="scout-section-heading{extra_class}">{escape(str(title))}</h3>')


def display_value(value):
    """Display text, lists, or structured values."""

    if value is None or value == "" or value == []:
        return

    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                st.json(item)
            else:
                st.markdown(f"- {item}")

    elif isinstance(value, dict):
        for key, item in value.items():
            st.markdown(f"**{key.replace('_', ' ').title()}**")
            display_value(item)

    else:
        st.write(value)

def display_sources(sources):
    """Display supporting research links."""

    if not sources:
        return

    for source in sources:
        if not isinstance(source, dict):
            continue

        url = source.get("url")
        platform = source.get("platform") or "Source"
        relevance = source.get("relevance")

        if url and url.startswith(("https://", "http://")):
            st.markdown(f"- [{platform}]({url})")

            if relevance:
                st.caption(relevance)

def display_key_figures(figures):
    """Display each figure as a separate card."""
    display_key_figure_cards(figures)

def display_finding(finding, page_key):
    """Show a finding page with a menu of its research topics."""

    st.subheader(finding.get("name", "Unnamed finding"))
    st.write(finding.get("description", ""))
    evidence = finding.get("evidence_strength") or "Not assessed"
    evidence_colors = {
        "strong": ("#166534", "#dcfce7"),
        "moderate": ("#854d0e", "#fef9c3"),
        "weak": ("#991b1b", "#fee2e2"),
    }
    evidence_label = str(evidence).strip().capitalize()
    color, background = evidence_colors.get(
        evidence_label.casefold(), ("#4b5563", "#f3f4f6")
    )
    st.html(
        f'<div style="display:inline-flex;align-items:center;gap:.5rem;'
        f'padding:.45rem .8rem;border-radius:8px;border-left:4px solid {color};'
        f'background:{background};color:{color};font-size:.95rem">'
        f'<span style="font-weight:400">Evidence strength:</span> '
        f'<strong>{escape(evidence_label)}</strong></div>'
    )

    sections = [
        ("History & context", "history"),
        ("Audience", "audience"),
        ("Engagement", "engagement"),
        ("Cultural momentum", "momentum"),
        ("Key figures", "key_figures"),
        ("Cultural significance", "cultural_significance"),
        ("Commercial signals", "commercial_signals"),
        ("Commercial potential", "commercial_potential"),
        ("Relevant communities", "related_communities"),
        ("Narrative themes", "narrative_themes"),
        ("Unverified claims", "unverified_claims"),
        ("Sources", "sources"),
    ]
    chapter_key = f"{page_key}_topic"
    if chapter_key not in st.session_state:
        st.session_state[chapter_key] = "history"

    menu, reader = st.columns([1, 2.4], gap="large")
    with menu:
        st.caption("RESEARCH CHAPTERS")
        for index, (heading, field) in enumerate(sections, start=1):
            st.button(
                f"{index:02d} · {heading}",
                key=f"{page_key}_topic_{field}",
                type="primary" if st.session_state[chapter_key] == field else "secondary",
                use_container_width=True,
                on_click=select_chapter,
                args=(chapter_key, field),
            )

    with reader:
        with st.container(border=True):
            field = st.session_state[chapter_key]
            heading = dict((field, heading) for heading, field in sections)[field]
            display_section_heading(heading)
            value = finding.get(field)
            if field == "engagement":
                display_engagement_dashboard(finding, key=f"{page_key}_engagement")
            elif field == "momentum":
                display_cultural_momentum(value)
            elif field == "related_communities":
                display_relevant_communities(finding)
            elif not value:
                st.caption("No research reported for this chapter.")
            elif field == "key_figures":
                display_key_figures(value)
            elif field == "sources":
                display_sources(value)
            elif field == "audience":
                display_audience_blocks(finding, key=f"{page_key}_audience")
            else:
                display_value(value)


def display_report(report, context="latest"):
    """Display the findings home or the selected finding page."""

    findings = report.get("findings") or []
    # Separate report and placement identities keep library/latest menus independent.
    identity = hashlib.sha256(
        json.dumps(report, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    selection_key = f"finding_{context}_{identity}"
    if selection_key not in st.session_state:
        st.session_state[selection_key] = None
    selected = st.session_state[selection_key]
    if isinstance(selected, int) and 0 <= selected < len(findings):
        st.button(
            "← Findings",
            key=f"{selection_key}_home",
            on_click=select_chapter,
            args=(selection_key, None),
        )
        display_finding(findings[selected], page_key=f"{selection_key}_{selected}")
        return

    approach = report.get("research_approach", "Unclassified")
    research_date = report.get("research_date", "")
    if research_date:
        try:
            research_date = datetime.fromisoformat(
                research_date.replace("Z", "+00:00")
            ).strftime("%m-%d-%Y")
        except (ValueError, TypeError, AttributeError):
            research_date = "Date unavailable"
    st.caption(f"Research approach: {approach} | {research_date}")

    if report.get("summary"):
        display_section_heading("Research summary", findings=True)
        st.write(report["summary"])

    display_section_heading(f"Findings: {len(findings)}", findings=True)
    if findings:
        with st.container(key=f"findings_home_{context}_{identity}"):
            for index, finding in enumerate(findings):
                st.button(
                    f"{index + 1:02d} · {finding.get('name', 'Unnamed finding')}",
                    key=f"{selection_key}_open_{index}",
                    use_container_width=True,
                    on_click=select_chapter,
                    args=(selection_key, index),
                )
                st.write(finding.get("description", ""))
    else:
        st.info("This report has no findings.")

    if report.get("overall_assessment"):
        display_section_heading("Overall assessment", findings=True)
        display_value(report["overall_assessment"])
    if report.get("research_limitations"):
        with st.expander("Research limitations"):
            display_value(report["research_limitations"])


def select_chapter(selection_key, index):
    st.session_state[selection_key] = index


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "scout_results" not in st.session_state:
    st.session_state.scout_results = None

if "scout_request" not in st.session_state:
    st.session_state.scout_request = None

# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------

tab_research, tab_library = st.tabs([
    "Ask Scout",
    "Research Library"
])

# --------------------------------------------------
# TAB 1: ASK SCOUT
# --------------------------------------------------

with tab_research:

    st.header("Ask Scout")

    st.write(
        "Discover cultural phenomena, investigate "
        "audience interests, or explore the traction "
        "behind a particular idea."
    )

    research_request = st.text_area(
        "What would you like to explore?",
        placeholder=(
            "Find overlooked cultural phenomena "
            "with growing audiences, or investigate "
            "the cultural momentum of a specific idea."
        ),
        height=120
    )

    if st.button("Run Scout", type="primary"):

        if not research_request.strip():
            st.warning(
                "Enter a topic, idea, or research request."
            )

        else:
            # Clear the previous result before a new run.
            st.session_state.scout_results = None
            st.session_state.scout_request = None

            with st.spinner(
                "Scout is researching. This may take a few minutes..."
            ):
                try:
                    # Perform new research.
                    report = run_scout(research_request)

                    # Save the complete report to SQLite.
                    save_report(report)

                    # Retain results across Streamlit reruns.
                    st.session_state.scout_results = report
                    st.session_state.scout_request = research_request

                    st.success(
                        "Research complete. Report saved "
                        "to your library."
                    )

                except Exception as error:
                    st.error(
                        f"Scout encountered an error: {error}"
                    )

    # Show latest results.
    if st.session_state.scout_results:

        st.divider()

        st.markdown("## Latest research")

        st.caption(
            st.session_state.scout_request
        )

        with st.container(key="finding_reader_latest"):
            display_report(st.session_state.scout_results)

# --------------------------------------------------
# TAB 2: RESEARCH LIBRARY
# --------------------------------------------------

with tab_library:

    st.header("Research Library")

    reports = get_reports()

    if not reports:
        st.info(
            "No Cultural Intelligence Reports saved yet. "
            "Run Scout to create your first report."
        )

    else:
        approaches = sorted({
            report["research_approach"]
            for report in reports
            if report["research_approach"]
        })

        search_column, approach_column = st.columns([3, 1.5], gap="small")
        with search_column:
            search_term = st.text_input(
                "Search reports",
                placeholder="Search research topics..."
            )
        with approach_column:
            selected_approaches = st.multiselect(
                "Research approach",
                options=approaches,
                default=[],
                placeholder="All approaches"
            )

        filtered = [
            report for report in reports
            if (
                search_term.lower()
                in (
                    (report["research_request"] or "")
                    + " "
                    + (report["summary"] or "")
                ).lower()
            )
            and (
                not selected_approaches
                or report["research_approach"]
                in selected_approaches
            )
        ]

        st.caption(
            f"Showing {len(filtered)} reports"
        )

        for saved_report in filtered:

            title = saved_report["research_request"]

            with st.expander(title):

                report = json.loads(
                    saved_report["report_json"]
                )

                with st.container(key=f"finding_reader_library_{saved_report['id']}"):
                    display_report(report, context=f"library_{saved_report['id']}")
