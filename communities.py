"""Relevant community links with support for older text-only reports."""
import streamlit as st

from engagement import valid_url


def display_relevant_communities(finding):
    communities = finding.get('related_communities') or []
    if not isinstance(communities, list):
        communities = [communities]
    linked = set()
    unlinked = False
    for community in communities:
        if isinstance(community, str):
            if valid_url(community):
                st.link_button(community, community)
                linked.add(community)
            else:
                st.write(community)  # Preserve any existing Markdown citations.
                unlinked = True
        elif isinstance(community, dict):
            name = community.get('name') or 'Community'
            url = community.get('url')
            if valid_url(url):
                st.link_button(str(name), url)
                linked.add(url)
            else:
                st.write(name)
                unlinked = True
            if community.get('platform'):
                st.caption(community['platform'])
            if community.get('description'):
                st.write(community['description'])
    # Existing structured audience research can already contain real locations.
    locations = finding.get('audience_communities') or []
    if isinstance(locations, list):
        for location in locations:
            if not isinstance(location, dict):
                continue
            url = location.get('url')
            if valid_url(url) and url not in linked:
                st.link_button(str(location.get('name') or 'Community'), url)
                if location.get('description'):
                    st.write(location['description'])
                linked.add(url)
    if not communities and not linked:
        st.caption('No relevant communities recorded.')
    elif unlinked and not linked:
        st.caption('This report has no structured community links. New research will include verified community locations when available.')
