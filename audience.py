"""Audience visualization derived solely from explicit lists in saved research."""

import colorsys
import hashlib
import math
import random
import re
import textwrap
from html import escape

import plotly.graph_objects as go
import streamlit as st

from engagement import valid_url, verified_metrics


def extract_audience_groups(text):
    """Return (verbatim short label, original description) pairs, or [].

    Only explicit, sequential numbered lists or line-start bullets qualify.
    Prose and comma-separated sentences are deliberately left unparsed.
    """
    if not isinstance(text, str) or not text.strip():
        return []
    markers = list(re.finditer(r"(?<!\S)\((\d{1,2})\)\s+", text))
    if not markers:
        markers = list(re.finditer(r"(?m)^\s*(\d{1,2})[.)]\s+", text))
    if markers:
        if [int(m.group(1)) for m in markers] != list(range(1, len(markers) + 1)):
            return []
    else:
        markers = list(re.finditer(r"(?m)^\s*[-*•]\s+", text))
    if len(markers) < 2:
        return []

    groups = []
    seen = set()
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        description = text[marker.end():end].strip()
        # A blank paragraph may introduce unrelated context; do not guess its boundary.
        if not description or re.search(r"\n\s*\n", description):
            return []
        label = re.split(r":|\s+[–—-]\s+|[.!?](?:\s|$)", description, maxsplit=1)[0]
        label = label.strip().strip('*').strip()
        words = label.split()
        if not words or not any(c.isalpha() for c in label):
            return []
        label = ' '.join(words[:7]) + ('…' if len(words) > 7 else '')
        normalized = ' '.join(description.casefold().split())
        if normalized not in seen:
            groups.append((label, description))
            seen.add(normalized)
    return groups if len(groups) >= 2 else []


def extract_relationship_label(label, description):
    """Extract a short verb phrase verbatim; never infer behavior from a group name."""
    # Only consider the group's leading explanation, not later claims about others.
    body = description.strip()
    leading_sentence = re.split(r"[.!?](?:\s|$)", body, maxsplit=1)[0]
    if re.search(r"\b(?:not|never|no|may|might|could|would|if|unlikely|unverified|without)\b", leading_sentence, re.I):
        return None
    body = leading_sentence
    # Saved research commonly describes groups as "designers who ..." or
    # "players seeking ...". Locate that explicit relationship before trying
    # the older label/colon form; displayed labels may themselves be truncated.
    relative = re.search(r"\b(?:who|that)\s+", body, re.I)
    seeking = re.search(r"\b(?:seeking|interested in|drawn to)\b", body, re.I)
    if relative:
        body = body[relative.end():]
    elif seeking:
        body = body[seeking.start():]
    else:
        prefix = re.match(r"^.*?(?::|\s+[–—-]\s+)\s*", body)
        if prefix:
            body = body[prefix.end():]
        elif body.casefold().startswith(label.casefold()):
            body = body[len(label):].lstrip()
        else:
            return None
    body = re.sub(r"^(?:who|they|people who|members who)\s+", "", body, flags=re.I)
    # Parenthetical examples can contain commas; remove them before finding
    # the clause boundary, without discarding the original hover description.
    body = re.sub(r"\([^()]*\)", "", body)
    clause = re.split(r"[.!?;](?:\s|$)|,", body, maxsplit=1)[0].strip()
    clause = ' '.join(clause.split()).rstrip('; ')
    # Conservatively omit qualified/negative claims rather than turn them into assertions.
    if re.search(r"\b(?:not|never|no|may|might|could|would|if|unlikely|unverified|without)\b", clause, re.I):
        return None
    actions = (
        r"treat(?:s|ing)?|tour(?:s|ing)?|seek(?:s|ing)?|interested in|drawn to|creat(?:e|es|ing)|experiment(?:s|ing)?|play(?:s|ing)?|explor(?:e|es|ing)|"
        r"teach(?:es|ing)?|facilitat(?:e|es|ing)|discover(?:s|ing)?|"
        r"attend(?:s|ing)?|organiz(?:e|es|ing)|discuss(?:es|ing)?|"
        r"shar(?:e|es|ing)|mak(?:e|es|ing)|read(?:s|ing)?|"
        r"watch(?:es|ing)?|us(?:e|es|ing)|build(?:s|ing)?|"
        r"research(?:es|ing)?|participat(?:e|es|ing)|follow(?:s|ing)?|"
        r"learn(?:s|ing)?|host(?:s|ing)?|collect(?:s|ing)?|"
        r"engag(?:e|es|ing)|connect(?:s|ing)?|support(?:s|ing)?"
    )
    if not re.match(rf"^(?:{actions})\b", clause, re.I):
        return None
    if not 2 <= len(clause.split()) <= 18:
        return None
    return clause[0].upper() + clause[1:]


def starting_word_capitalization(text):
    """Capitalize the initial letter without lowercasing acronyms or names."""
    return re.sub(r"[A-Za-z]", lambda match: match.group().upper(), text, count=1)


def shorten_audience_title(description):
    """Use the original leading noun phrase, stopping before an explanatory clause."""
    title = re.split(
        r"\b(?:who|that|which|seeking|interested in|drawn to)\b|:|\s+[–—-]\s+|[.!?;](?:\s|$)",
        description, maxsplit=1, flags=re.I,
    )[0]
    title = re.sub(r"\([^()]*\)", "", title).strip().strip('*').strip()
    # A comma often introduces examples or another audience; keep the first noun phrase.
    title = title.split(',', 1)[0].strip()
    return starting_word_capitalization(title or description.strip())


def _wrapped(text, width):
    return '<br>'.join(escape(line) for line in textwrap.wrap(text, width=width))


def build_audience_constellation(name, groups):
    """Build an equal-node radial map; edges indicate inclusion in this finding only."""
    seed = hashlib.sha256(repr((name, groups)).encode('utf-8')).digest()
    rng = random.Random(seed)
    # Keep each node in its own angular sector so the organic offsets do not
    # imply clusters or introduce audience-to-audience connections.
    step = 2 * math.pi / len(groups)
    rotation = rng.uniform(0.20, 0.48)
    angles = [math.pi / 2 + rotation + step * i + rng.uniform(-0.09, 0.09) * step
              for i in range(len(groups))]
    radii = [rng.uniform(0.94, 1.08) for _ in groups]
    x = [radius * math.cos(angle) for radius, angle in zip(radii, angles)]
    y = [radius * math.sin(angle) for radius, angle in zip(radii, angles)]
    # Evenly spaced hues give every bubble a distinct color; dark fills keep
    # white labels readable. The seeded shuffle is stable across selection reruns.
    hue = rng.random()
    colors = []
    for i in range(len(groups) + 1):
        rgb = colorsys.hls_to_rgb((hue + i / (len(groups) + 1)) % 1, 0.30, 0.52)
        colors.append('#' + ''.join(f'{round(channel * 255):02x}' for channel in rgb))
    rng.shuffle(colors)
    edge_x, edge_y = [], []
    for px, py in zip(x, y):
        edge_x.extend([0, px, None])
        edge_y.extend([0, py, None])
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode='lines', line=dict(color='#c8aaa0', width=1.5),
        hoverinfo='skip', showlegend=False,
    ))
    figure.add_trace(go.Scatter(
        x=x, y=y, mode='markers+text',
        marker=dict(size=160, color=colors[:-1]),
        text=[_wrapped(shorten_audience_title(description), 17) for _, description in groups],
        textfont=dict(size=15, color='white'),
        textposition='middle center',
        customdata=[_wrapped(description, 48) for _, description in groups],
        hovertemplate='%{customdata}<extra></extra>',
        showlegend=False,
    ))
    figure.add_trace(go.Scatter(
        x=[0], y=[0], mode='markers+text', marker=dict(size=190, color=colors[-1]),
        text=[_wrapped(starting_word_capitalization(name), 18)], textposition='middle center',
        textfont=dict(size=18, color='white'),
        hovertext=[escape(name)], hovertemplate='%{hovertext}<extra></extra>',
        showlegend=False,
    ))
    research_text = ' '.join([name] + [description for _, description in groups])
    if re.search(r"\bTTRPGs?\b", research_text, re.I):
        figure.add_annotation(
            xref='paper', yref='paper', x=0, y=1.06,
            xanchor='left', yanchor='bottom', showarrow=False,
            text='<b>Key</b><br>TTRPG = tabletop role-playing game',
            align='left', font=dict(size=12, color='#334155'),
            bgcolor='rgba(255,255,255,0.95)', borderpad=6,
        )
    figure.update_layout(
        autosize=True, height=680, margin=dict(l=15, r=15, t=85, b=40),
        xaxis=dict(visible=False, range=[-1.65, 1.65]),
        yaxis=dict(visible=False, range=[-1.5, 1.5], scaleanchor='x', scaleratio=1),
        hoverlabel=dict(align='left'), dragmode='pan', clickmode='event+select',
    )
    return figure


def audience_labels_html(groups):
    """Two audience cards per row with shortened titles and full descriptions."""
    cards = []
    for label, description in groups:
        label = shorten_audience_title(description)
        subtitle = f'<span>{escape(starting_word_capitalization(description))}</span>'
        cards.append(
            f'<div class="audience-label" tabindex="0" title="{escape(description, quote=True)}">'
            f'<strong>{escape(label)}</strong>{subtitle}</div>'
        )
    return """<style>
    .audience-label-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .6rem; }
    .audience-label { border: 1px solid rgba(182,90,56,.25); border-radius: 8px;
        padding: .65rem .8rem; background: rgba(182,90,56,.04); overflow-wrap: anywhere; }
    .audience-label span { display: block; font-size: 1rem; line-height: 1.55; margin-top: .4rem; }
    .audience-label:hover, .audience-label:focus { background: rgba(182,90,56,.10); }
    </style><div class="audience-label-grid">""" + ''.join(cards) + '</div>'


def audience_community_entries(finding):
    """Require both the actual gathering-place link and evidence for its relevance."""
    entries = finding.get('audience_communities') or []
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)
            and all(isinstance(entry.get(field), str) and entry[field].strip()
                    for field in ('audience_group', 'name', 'platform', 'description'))
            and valid_url(entry.get('url')) and valid_url(entry.get('evidence_url'))]


def display_audience_communities(finding):
    """Show reported audience-to-community mappings without inferring new connections."""
    st.markdown('#### Where this audience gathers')
    entries = audience_community_entries(finding)
    if not entries:
        if 'audience_communities' not in finding:
            st.caption('This report has no structured community locations. New research can collect named communities and supporting links.')
        else:
            st.caption('No community locations were verified for this finding.')
        with st.expander('Preview community layout — no credits used'):
            st.info('Illustrative preview only. These are sample communities and explanations, not research findings. Nothing is saved.')
            groups = extract_audience_groups(finding.get('audience', ''))
            group = shorten_audience_title(groups[0][1]) if groups else 'Example audience'
            _display_community_entries([
                dict(audience_group=group, name='Example discussion community (sample)',
                     platform='Reddit', url='https://example.org/#sample-community',
                     description='Sample explanation: research would identify a specific community and describe a publicly documented discussion connecting this audience to the topic.',
                     evidence_url='https://example.org/#sample-evidence', metrics=[]),
                dict(audience_group=group, name='Example server directory (sample)',
                     platform='Discord', url='https://example.org/#sample-directory',
                     description='Sample explanation: an official directory or public community page would establish relevance. Private conversations would not be treated as observed evidence.',
                     evidence_url='https://example.org/#sample-directory-evidence', metrics=[]),
            ])
        return
    _display_community_entries(entries)


def _display_community_entries(entries):
    grouped = {}
    for entry in entries:
        grouped.setdefault(entry['audience_group'].strip(), []).append(entry)
    for group, communities in grouped.items():
        st.markdown('##### ' + starting_word_capitalization(group))
        for community in communities:
            st.link_button(f"{community['platform']} · {community['name']}", community['url'])
            st.write(community['description'])
            st.link_button('Evidence of connection', community['evidence_url'])
            for metric in verified_metrics(community):
                st.metric(metric['name'], f"{metric['value']:,} {metric['unit']}")
                st.caption(f"Observed: {metric['period']}")
                st.link_button('Count source', metric['source_url'])
    st.caption('Community membership and online counts do not establish active participation or total audience size.')


def display_audience_constellation(finding, key=None):
    """Render explicit audience groups, falling back to the unmodified audience text."""
    audience = finding.get('audience', '')
    groups = extract_audience_groups(audience)
    if not groups:
        st.write(audience)
        display_audience_communities(finding)
        return
    event = st.plotly_chart(
        build_audience_constellation(finding.get('name') or 'Finding', groups),
        use_container_width=True, config={'responsive': True, 'displaylogo': False},
        key=key, on_select='rerun', selection_mode='points',
    )
    st.html(audience_labels_html(groups))
    st.caption('Full audience descriptions appear below the graph. Select a node to focus on its explanation. Equal nodes and lines do not represent audience size, engagement scores, or relationships between groups.')
    points = event.get('selection', {}).get('points', [])
    for point in reversed(points):
        index = point.get('point_index')
        if point.get('curve_number') != 1 or not isinstance(index, int) or not 0 <= index < len(groups):
            continue
        label, description = groups[index]
        with st.container(border=True):
            st.markdown('#### Audience connection')
            st.write(shorten_audience_title(description))
            relationship = extract_relationship_label(label, description)
            if relationship:
                st.write(relationship)
            st.write(description)
        break
    display_audience_communities(finding)
    # Also provide readable, touch-accessible descriptions and preserve introductory context.
    with st.expander('Original audience research'):
        st.write(audience)


def audience_blocks(finding):
    """Prefer sourced structured groups; preserve explicit legacy groups without guessing."""
    structured = finding.get('audience_groups')
    groups = []
    if isinstance(structured, list):
        for group in structured:
            if not isinstance(group, dict):
                continue
            if not all(isinstance(group.get(k), str) and group[k].strip() for k in ('name', 'description')):
                continue
            sources = group.get('source_urls', [])
            sources = [url for url in sources if valid_url(url)] if isinstance(sources, list) else []
            if not sources:
                continue
            raw_examples = group.get('examples', [])
            examples = [example for example in raw_examples if isinstance(example, dict)
                        and valid_url(example.get('url'))
                        and all(isinstance(example.get(k), str) and example[k].strip()
                                for k in ('name', 'description'))] if isinstance(raw_examples, list) else []
            groups.append(dict(name=group['name'], description=group['description'],
                               source_urls=sources, examples=examples))
    if groups:
        return groups
    legacy = [dict(name=shorten_audience_title(description), description=description,
                   source_urls=[], examples=[])
              for _, description in extract_audience_groups(finding.get('audience', ''))]
    if legacy:
        return legacy
    text = finding.get('audience')
    if isinstance(text, str) and text.strip():
        return [dict(name='Audience overview', description=text, source_urls=[], examples=[])]
    return []


def audience_blocks_html(groups):
    """Readable colored blocks with full hover definitions and visible sourced examples."""
    colors = ['#8c492f', '#315b78', '#546935', '#704d89', '#826224', '#326c67']
    cards = []
    for index, group in enumerate(groups):
        name = starting_word_capitalization(group['name'])
        description = starting_word_capitalization(group['description'])
        examples = ''.join(
            f'<li><a href="{escape(example["url"], quote=True)}" target="_blank" rel="noopener noreferrer">'
            f'{escape(example["name"])}</a><br>{escape(example["description"])}</li>'
            for example in group['examples']
        )
        examples = '<strong>Examples</strong><ul>' + examples + '</ul>' if examples else '<small>No sourced examples recorded.</small>'
        sources = ' · '.join(
            f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">Source {i + 1}</a>'
            for i, url in enumerate(group['source_urls'])
        )
        cards.append(
            '<article class="audience-block">'
            f'<div class="audience-block-title" tabindex="0" title="{escape(description, quote=True)}" '
            f'style="background:{colors[index % len(colors)]}">{escape(name)}</div>'
            f'<div class="audience-block-body"><p>{escape(description)}</p>{examples}'
            f'<div class="audience-block-sources">{sources}</div></div></article>'
        )
    return '''<style>
    .audience-block-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem;align-items:start}
    .audience-block {border:1px solid #8884;border-radius:10px;overflow:hidden}
    .audience-block-title {color:white;padding:1rem;font-size:1.15rem;font-weight:650;line-height:1.4;cursor:help}
    .audience-block-title:hover,.audience-block-title:focus {filter:brightness(1.12)}
    .audience-block-body {padding:.8rem 1rem;line-height:1.55;overflow-wrap:anywhere}
    .audience-block-body p {margin:0 0 .8rem}
    .audience-block-body ul {padding-left:1.2rem;margin:.4rem 0}
    .audience-block-body li {margin-bottom:.75rem}
    .audience-block-sources {font-size:.85rem;margin-top:.5rem}
    @media(max-width:650px){.audience-block-grid{grid-template-columns:1fr}}
    </style><div class="audience-block-grid">''' + ''.join(cards) + '</div>'


def display_audience_blocks(finding, key=None):
    """Standard audience presentation; no API calls occur while interacting."""
    groups = audience_blocks(finding)
    if groups:
        st.html(audience_blocks_html(groups))
    elif finding.get('audience'):
        # Prose cannot safely be split into specific personas without new research.
        st.write(finding['audience'])
        st.caption('This report contains a prose audience overview. New research can collect distinct audience blocks and sourced examples.')
    else:
        st.caption('No audience research recorded.')
    display_audience_communities(finding)
    if groups and finding.get('audience'):
        with st.expander('Original audience research'):
            st.write(finding['audience'])
