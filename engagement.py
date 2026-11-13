"""Source-backed engagement cards and strictly grouped measurement charts."""
import math
import re
from collections import defaultdict
from html import escape
from urllib.parse import urlsplit

import plotly.graph_objects as go
import streamlit as st

EVIDENCE_TYPES = ('event', 'project', 'publication', 'community')


def valid_url(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except ValueError:
        return False


# Identity badges identify a source, not a credibility rating or peer-review status.
SOURCE_IDENTITIES = {
    'youtube.com': ('YouTube', '▶', '#b91c1c', 'Video platform'),
    'youtu.be': ('YouTube', '▶', '#b91c1c', 'Video platform'),
    'tiktok.com': ('TikTok', '♪', '#262626', 'Short-form video platform'),
    'wikipedia.org': ('Wikipedia', 'W', '#475569', 'Community-edited reference'),
    'reddit.com': ('Reddit', 'r/', '#b94717', 'Community discussion'),
    'instagram.com': ('Instagram', 'IG', '#a32a70', 'Social platform'),
    'nature.com': ('Nature Portfolio', 'N', '#374151', 'Publication / publisher'),
    'science.org': ('Science / AAAS', 'S', '#96332f', 'Publication / publisher'),
    'journals.plos.org': ('PLOS Journals', 'P', '#365c9b', 'Journal publisher'),
    'pubmed.ncbi.nlm.nih.gov': ('PubMed', 'PM', '#245c85', 'Research index; consult the linked publication'),
    'arxiv.org': ('arXiv', 'aX', '#9c3434', 'Preprint repository; peer review is not established by hosting'),
}


def source_identity(url):
    """Match actual host boundaries; never trust a name supplied in report prose."""
    host = (urlsplit(url).hostname or '').lower().removeprefix('www.')
    for domain, identity in SOURCE_IDENTITIES.items():
        if host == domain or host.endswith('.' + domain):
            return identity
    return (host, host[:2].upper(), '#536475', 'Direct source; review authorship and methodology')


def display_source_heading(identity, url, title=None):
    """A compact linked source badge and headline pointing to the exact evidence."""
    name, badge, color, _ = identity
    if not valid_url(url):
        return
    headline = escape(name)
    if title and title.casefold() != name.casefold():
        headline += f' · {escape(title)}'
    st.html(
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer" '
        'style="display:flex;align-items:center;gap:.6rem;margin:.5rem 0;'
        'color:inherit;text-decoration:none;line-height:1.3">'
        f'<span aria-hidden="true" style="background:{color};color:white;border-radius:6px;'
        f'padding:.35rem;min-width:2rem;text-align:center;font-weight:700">{escape(badge)}</span>'
        f'<strong style="font-size:1.05rem">{headline} ↗</strong></a>'
    )


def group_by_source(items, url_field):
    groups = {}
    for item in items:
        identity = source_identity(item[url_field])
        groups.setdefault(identity, []).append(item)
    return groups.items()


def verified_metrics(entry):
    """Accept only explicit finite values with verification and metric provenance."""
    result = []
    metrics = entry.get('metrics', [])
    if not isinstance(metrics, list):
        return result
    for metric in metrics:
        if not isinstance(metric, dict):
            continue
        value = metric.get('value')
        if (metric.get('verified') is not True or isinstance(value, bool)
                or not isinstance(value, (int, float)) or not math.isfinite(value)
                or not valid_url(metric.get('source_url'))):
            continue
        if not all(isinstance(metric.get(k), str) and metric[k].strip()
                   for k in ('name', 'unit', 'period')):
            continue
        result.append(metric)
    return result


def evidence_entries(finding):
    entries = finding.get('engagement_evidence') or []
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)
            and entry.get('evidence_type') in EVIDENCE_TYPES
            and all(isinstance(entry.get(k), str) and entry[k].strip()
                    for k in ('name', 'description'))
            and valid_url(entry.get('source_url'))]


def build_engagement_charts(entries):
    """Never infer comparability from unit alone or combine periods in a bar chart."""
    bars, histories = defaultdict(list), defaultdict(list)
    for index, entry in enumerate(entries):
        for metric in verified_metrics(entry):
            # comparison_group must explicitly identify a shared definition,
            # platform, population/scope and counting methodology.
            if not all(isinstance(metric.get(k), str) and metric[k].strip()
                       for k in ('comparison_group', 'measurement_basis', 'period_kind')):
                continue
            kind = metric['period_kind']
            patterns = {'snapshot': r'\d{4}-\d{2}-\d{2}', 'daily': r'\d{4}-\d{2}-\d{2}',
                        'monthly': r'\d{4}-\d{2}', 'annual': r'\d{4}'}
            if kind not in patterns or not re.fullmatch(patterns[kind], metric['period']):
                continue
            # Reject invalid calendar dates before plotting.
            from datetime import datetime
            fmt = {'snapshot': '%Y-%m-%d', 'daily': '%Y-%m-%d', 'monthly': '%Y-%m', 'annual': '%Y'}[kind]
            try:
                datetime.strptime(metric['period'], fmt)
            except ValueError:
                continue
            common = tuple(metric[k].strip().casefold() for k in
                           ('name', 'unit', 'comparison_group', 'measurement_basis', 'period_kind'))
            bars[common + (metric['period'],)].append((index, entry, metric))
            histories[(index,) + common].append((index, entry, metric))
    charts = []
    for rows in bars.values():
        if len({row[0] for row in rows}) < 2 or len({row[0] for row in rows}) != len(rows):
            continue
        metric = rows[0][2]
        title = f"{metric['name']} · {metric['period']}"
        fig = go.Figure(go.Bar(
            x=[row[1]['name'] for row in rows], y=[row[2]['value'] for row in rows],
            customdata=[[row[2]['period'], row[2]['source_url']] for row in rows],
            hovertemplate='%{x}<br>%{y}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>',
        ))
        fig.update_layout(title=title, yaxis_title=metric['unit'])
        charts.append((fig, rows))
    for rows in histories.values():
        periods = [row[2]['period'] for row in rows]
        if len(set(periods)) < 2 or len(set(periods)) != len(periods):
            continue
        rows = sorted(rows, key=lambda row: row[2]['period'])
        metric = rows[0][2]
        fig = go.Figure(go.Scatter(
            x=[row[2]['period'] for row in rows], y=[row[2]['value'] for row in rows],
            mode='lines+markers', customdata=[row[2]['source_url'] for row in rows],
            hovertemplate='%{x}<br>%{y}<br>%{customdata}<extra></extra>',
        ))
        fig.update_layout(title=f"{rows[0][1]['name']} · {metric['name']}",
                          xaxis_title=metric['period_kind'].capitalize(), yaxis_title=metric['unit'])
        charts.append((fig, rows))
    return charts


def display_engagement_dashboard(finding, key='engagement'):
    """Preserve the original summary and show only sourced, structured evidence."""
    if finding.get('engagement'):
        st.write(finding['engagement'])
    st.markdown('#### Engagement evidence dashboard')
    entries = evidence_entries(finding)
    if not entries:
        if 'engagement_evidence' not in finding:
            st.info(
                'This saved report predates structured engagement evidence. '
                'Run a new research request to collect sourced evidence cards '
                'and, when available, verified measurements for charts. '
                'The original engagement summary and research links are preserved.'
            )
        else:
            st.info('No usable sourced engagement evidence was returned for this finding.')
    for identity, source_entries in group_by_source(entries, 'source_url'):
        for entry in source_entries:
            display_source_heading(identity, entry['source_url'], entry['name'])
            metrics = verified_metrics(entry)
            if metrics:
                stats, description = st.columns([1, 2], gap='medium')
                with stats:
                    for metric in metrics:
                        st.metric(metric['name'], f"{metric['value']:,} {metric['unit']}")
                        st.caption(f"Period: {metric['period']}")
                        st.link_button('Metric source', metric['source_url'])
                with description:
                    st.write(entry['description'])
            else:
                st.write(entry['description'])
    charts = build_engagement_charts(entries)
    for index, (figure, rows) in enumerate(charts):
        st.plotly_chart(figure, use_container_width=True, key=f'{key}_chart_{index}')
        st.caption(f"Comparison scope: {rows[0][2]['comparison_group']} · Basis: {rows[0][2]['measurement_basis']}")
        with st.expander('Chart sources'):
            for _, entry, metric in rows:
                st.link_button(f"{entry['name']} · {metric['period']}", metric['source_url'])
    if entries:
        st.caption('Numbers are shown only when the report marks them verified and provides a metric source and period.')
    # Retain the existing report's source links, including legacy reports.
    sources = finding.get('sources') or []
    if isinstance(sources, list):
        links = [s for s in sources if isinstance(s, dict) and valid_url(s.get('url'))]
        if links:
            with st.expander('Research source links'):
                for identity, source_links in group_by_source(links, 'url'):
                    for source in source_links:
                        display_source_heading(identity, source['url'])
                        if source.get('relevance'):
                            st.caption(source['relevance'])
