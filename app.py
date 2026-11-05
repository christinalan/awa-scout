
import json
import streamlit as st

from database import ( 
    create_tables,
    create_report_table, 
    get_reports,
    save_report
    )

from scout import run_scout


# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="AWA Greenlight",
    page_icon="🔎",
    layout="wide"
)

st.title("AWA / Greenlight")
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

    st.markdown("**Sources**")

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
    """Display notable people connected to a finding."""

    if not figures:
        return

    st.markdown("**Key figures**")

    for figure in figures:
        if not isinstance(figure, dict):
            continue

        st.markdown(
            f"**{figure.get('name', 'Unknown')}**"
        )

        if figure.get("field"):
            st.caption(figure["field"])

        display_value(figure.get("connection"))
        display_value(figure.get("significance"))

        for url in figure.get("source_urls", []):
            if isinstance(url, str) and url.startswith(
                ("https://", "http://")
            ):
                st.markdown(f"[Supporting source]({url})")

def display_finding(finding):
    """Display an individual research finding."""

    st.subheader(finding.get("name", "Unnamed finding"))

    category = finding.get("category", "Uncategorized")
    evidence = finding.get(
        "evidence_strength", "Not assessed"
    )

    st.caption(
        f"{category} | Evidence: {evidence}"
    )

    st.write(finding.get("description", ""))

    # Momentum is particularly important for Greenlight.
    momentum = finding.get("momentum", {})

    if isinstance(momentum, dict):
        status = momentum.get("status", "Unverified")

        st.markdown(f"**Cultural momentum: {status.title()}**")

        display_value(momentum.get("assessment"))

        if momentum.get("historical_comparison"):
            st.caption(
                momentum["historical_comparison"]
            )

    with st.expander("Explore full research"):

        sections = [
            ("History", "history"),
            ("Audience", "audience"),
            ("Engagement", "engagement"),
            ("Cultural significance", "cultural_significance"),
            ("Commercial signals", "commercial_signals"),
            ("Commercial potential", "commercial_potential"),
            ("Related communities", "related_communities"),
            ("Narrative themes", "narrative_themes"),
            ("Unverified claims", "unverified_claims")
        ]

        for heading, key in sections:
            value = finding.get(key)

            if value:
                st.markdown(f"**{heading}**")
                display_value(value)

        display_key_figures(
            finding.get("key_figures", [])
        )

        display_sources(
            finding.get("sources", [])
        )

def display_report(report):
    """Display a complete Cultural Intelligence Report."""

    approach = report.get(
        "research_approach", "Unclassified"
    )

    research_date = report.get("research_date", "")

    st.caption(
        f"Research approach: {approach} | {research_date}"
    )

    if report.get("summary"):
        st.markdown("### Research summary")
        st.write(report["summary"])

    findings = report.get("findings", [])

    st.markdown(f"### Findings ({len(findings)})")

    for finding in findings:
        with st.container(border=True):
            display_finding(finding)

    if report.get("overall_assessment"):
        st.markdown("### Overall assessment")
        st.write(report["overall_assessment"])

    limitations = report.get("research_limitations", [])

    if limitations:
        with st.expander("Research limitations"):
            display_value(limitations)


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

        display_report(
            st.session_state.scout_results
        )

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
        st.caption(
            f"{len(reports)} saved research reports"
        )

        search_term = st.text_input(
            "Search reports",
            placeholder="Search research topics..."
        )

        approaches = sorted({
            report["research_approach"]
            for report in reports
            if report["research_approach"]
        })

        selected_approaches = st.multiselect(
            "Research approach",
            options=approaches,
            default=approaches
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
                not approaches
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

                display_report(report)
