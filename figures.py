"""Key figure cards with named work links and backwards-compatible source labels."""
import re
from urllib.parse import unquote, urlsplit

import streamlit as st

from engagement import valid_url


def source_label(url):
    """Use a readable URL title when older reports contain no explicit work title."""
    parsed = urlsplit(url)
    parts = [unquote(part) for part in parsed.path.split('/') if part]
    title = parts[-1] if parts else ''
    # Numeric article IDs are not meaningful labels; use the preceding slug.
    if title.isdigit() and len(parts) > 1:
        title = parts[-2]
    if title and not title.isdigit() and title.casefold() not in ('watch', 'index.html', 'en'):
        title = re.sub(r'\.(?:html?|pdf)$', '', title, flags=re.I)
        title = re.sub(r'[_-]+', ' ', title).strip()
        return title[:1].upper() + title[1:]
    return parsed.hostname or 'Source'


def figure_work_links(figure):
    links, seen = [], set()
    works = figure.get('supporting_work') or []
    if isinstance(works, list):
        for work in works:
            if not isinstance(work, dict) or not valid_url(work.get('url')):
                continue
            title = work.get('title') or work.get('name')
            if not isinstance(title, str) or not title.strip() or work['url'] in seen:
                continue
            links.append((title.strip(), work['url']))
            seen.add(work['url'])
    urls = figure.get('source_urls') or []
    if isinstance(urls, list):
        for url in urls:
            if valid_url(url) and url not in seen:
                links.append((source_label(url), url))
                seen.add(url)
    return links


def display_key_figure_cards(figures):
    if not isinstance(figures, list):
        return
    for figure in figures:
        if not isinstance(figure, dict):
            continue
        with st.container(border=True):
            photo = figure.get('photo_url') or figure.get('image_url')
            if valid_url(photo):
                portrait, heading = st.columns([1, 4], gap='medium')
                with portrait:
                    st.image(photo, width=100)
            else:
                heading = st.container()
            with heading:
                st.markdown('#### ' + str(figure.get('name') or 'Unnamed figure'))
                roles = [figure.get('industry'), figure.get('profession')]
                roles = [role.strip() for role in roles if isinstance(role, str) and role.strip()]
                if not roles and figure.get('field'):
                    roles = [str(figure['field'])]
                if roles:
                    st.caption(' · '.join(dict.fromkeys(roles)))
            for field in ('description', 'connection', 'significance'):
                if figure.get(field):
                    st.write(figure[field])
            links = figure_work_links(figure)
            if links:
                st.markdown('**Work & sources**')
                for title, url in links:
                    st.link_button(title, url)
            credit_url = figure.get('photo_source_url')
            if valid_url(photo) and valid_url(credit_url):
                st.link_button('Photo credit', credit_url)
