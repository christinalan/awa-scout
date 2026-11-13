import unittest
from unittest.mock import patch

from audience import (
    build_audience_constellation,
    audience_community_entries,
    audience_blocks,
    audience_blocks_html,
    display_audience_communities,
    audience_labels_html,
    shorten_audience_title,
    display_audience_constellation,
    extract_audience_groups,
    extract_relationship_label,
)


class AudienceTests(unittest.TestCase):
    def test_inline_numbered_groups_preserve_descriptions(self):
        text = 'Audiences include: (1) Artists: People making art. (2) Readers: People reading books.'
        self.assertEqual(extract_audience_groups(text), [
            ('Artists', 'Artists: People making art.'),
            ('Readers', 'Readers: People reading books.'),
        ])

    def test_line_lists(self):
        for text in ['1. Artists: Art makers\n2. Readers: Book readers',
                     '- Artists: Art makers\n- Readers: Book readers']:
            self.assertEqual([label for label, _ in extract_audience_groups(text)], ['Artists', 'Readers'])

    def test_ambiguous_text_falls_back(self):
        for text in ['Artists, readers, and fans enjoy this.',
                     '(1) Artists (3) Readers', '(2026) Artists (2027) Readers',
                     '(1) Artists', '(1) Artists (2) ',
                     '(1) Artists\n\nUnrelated paragraph (2) Readers', None]:
            self.assertEqual(extract_audience_groups(text), [])

    def test_duplicate_descriptions_are_not_distinct_groups(self):
        self.assertEqual(extract_audience_groups('(1) Artists (2) Artists'), [])

    def test_fallback_renders_original(self):
        finding = {'audience': 'Artists, readers, and fans.'}
        with patch('audience.st.write') as write, patch('audience.st.plotly_chart') as plot:
            display_audience_constellation(finding)
        write.assert_any_call(finding['audience'])
        plot.assert_not_called()

    def test_relationships_are_extracted_not_inferred(self):
        self.assertEqual(extract_relationship_label('Artists', 'Artists: Create and experiment with the medium.'), 'Create and experiment with the medium')
        self.assertEqual(extract_relationship_label('Fans', 'Fans who discover the topic through conventions.'), 'Discover the topic through conventions')
        self.assertEqual(extract_relationship_label('Artists', 'Artists: People interested in culture.'), 'Interested in culture')
        for description in [
                            'Artists: May create new works.',
                            'Artists: Do not create new works.',
                            'Artists: Create works without documented participation.',
                            'Artists: Readers create new works.']:
            self.assertIsNone(extract_relationship_label('Artists', description))

    def test_saved_research_relationship_patterns(self):
        cases = [
            ('dedicated TTRPG players seeking non-mainstream experiences (solo…',
             'dedicated TTRPG players seeking non-mainstream experiences (solo journaling games, queer romance games, political micro-RPGs, etc.);',
             'Seeking non-mainstream experiences'),
            ('librarians, educators, and community organizers who use…',
             'librarians, educators, and community organizers who use simple indie games for programming and outreach; and',
             'Use simple indie games for programming and outreach'),
            ('independent illustrators, comic artists, and merch designers…',
             'independent illustrators, comic artists, and merch designers who tour multiple conventions each year;',
             'Tour multiple conventions each year'),
        ]
        for label, description, expected in cases:
            self.assertEqual(extract_relationship_label(label, description), expected)
        self.assertIsNone(extract_relationship_label('Artists', 'Artists who may create new works.'))

    def test_relationship_labels_and_larger_center(self):
        figure = build_audience_constellation('Topic', [
            ('Artists', 'Artists: Create and experiment.'),
            ('Fans', 'Fans: No documented connection.'),
        ])
        self.assertFalse(figure.layout.annotations)
        html = audience_labels_html([('Artists', 'Artists: Create and experiment.')])
        self.assertIn('<strong>Artists</strong>', html)
        self.assertIn('<span>Artists: Create and experiment.</span>', html)
        self.assertIn('title="Artists: Create and experiment."', html)
        self.assertEqual(figure.data[1].text[1], 'Fans')
        self.assertGreater(figure.data[2].textfont.size, figure.data[1].textfont.size)

    def test_short_titles_use_original_noun_phrase(self):
        self.assertEqual(shorten_audience_title('indie game designers who treat small zines as art;'), 'Indie game designers')
        self.assertEqual(shorten_audience_title('dedicated TTRPG players seeking new experiences'), 'Dedicated TTRPG players')
        self.assertEqual(shorten_audience_title('librarians, educators, and organizers who use games'), 'Librarians')
        chart = build_audience_constellation('Topic', [('Old long label', 'indie game designers who create games'), ('Fans', 'Fans: Read comics')])
        self.assertEqual(chart.data[1].text[0], 'Indie game<br>designers')
        self.assertEqual(chart.data[1].textposition, 'middle center')

    def test_organic_layout_colors_and_acronym_key(self):
        groups = [('Players', 'TTRPG players who explore games'), ('Designers', 'Designers who create games')]
        first = build_audience_constellation('Topic', groups)
        second = build_audience_constellation('Topic', groups)
        self.assertEqual(first.to_json(), second.to_json())
        colors = list(first.data[1].marker.color) + [first.data[2].marker.color]
        self.assertEqual(len(set(colors)), 3)
        self.assertTrue(all(abs(value) > 0.01 for value in first.data[1].x))
        self.assertIn('TTRPG = tabletop role-playing game', first.layout.annotations[0].text)
        self.assertEqual(first.layout.annotations[0].xanchor, 'left')

    def test_communities_require_direct_and_supporting_links(self):
        entry = dict(audience_group='Indie game players', name='A community',
                     platform='Forum', url='https://example.org/community',
                     evidence_url='https://example.org/discussion',
                     description='A documented discussion of indie games.')
        finding = {'audience_communities': [entry]}
        self.assertEqual(audience_community_entries(finding), [entry])
        with patch('audience.st.link_button') as link, patch('audience.st.write') as write:
            display_audience_communities(finding)
        write.assert_called_once_with(entry['description'])
        self.assertEqual(len(link.call_args_list), 2)
        entry['evidence_url'] = 'javascript:alert(1)'
        self.assertEqual(audience_community_entries(finding), [])

    def test_standard_blocks_support_legacy_prose_and_lists(self):
        groups = audience_blocks({'audience': 'Artists and photographers interested in a topic.'})
        self.assertEqual(groups[0]['name'], 'Audience overview')
        self.assertEqual(groups[0]['examples'], [])
        self.assertEqual(len(audience_blocks({'audience': '(1) Artists: Make art. (2) Players: Play games.'})), 2)

    def test_blocks_require_sourced_examples_and_escape_html(self):
        finding = {'audience_groups': [dict(name='Photographers', description='Observe empty spaces <quietly>.',
                   source_urls=['https://example.org/photo'], examples=[
                       dict(name='A photograph', description='A documented empty room.', url='https://example.org/work'),
                       dict(name='Unsafe', description='Unsupported example', url='javascript:alert(1)')])]}
        groups = audience_blocks(finding)
        self.assertEqual(len(groups[0]['examples']), 1)
        html = audience_blocks_html(groups)
        self.assertIn('title="Observe empty spaces &lt;quietly&gt;."', html)
        self.assertIn('https://example.org/work', html)
        self.assertNotIn('javascript:', html)
        self.assertIn('Examples', html)

    def test_selected_audience_detail_preserves_description(self):
        finding = {'name': 'Topic', 'audience': '(1) Artists: Create new works. (2) Fans: Follow the topic.'}
        event = {'selection': {'points': [{'curve_number': 1, 'point_index': 1}]}}
        with patch('audience.st.plotly_chart', return_value=event) as plot, patch('audience.st.write') as write:
            display_audience_constellation(finding, key='test_chart')
        self.assertIn(('Fans: Follow the topic.',), [call.args for call in write.call_args_list])
        self.assertEqual(plot.call_args.kwargs['on_select'], 'rerun')

    def test_chart_has_uniform_nodes_and_spokes_only(self):
        groups = [('Artists', 'Artists: Full original detail.'), ('Readers', 'Readers: Another detail.')]
        figure = build_audience_constellation('Test finding', groups)
        edges, audiences, center = figure.data
        self.assertEqual(len(edges.x), 6)
        self.assertEqual(audiences.marker.size, 160)
        self.assertEqual(len(audiences.x), 2)
        self.assertEqual(center.x, (0,))
        self.assertEqual(center.text, ('Test finding',))
        self.assertIn('Full original detail.', audiences.customdata[0])
        figure.to_json()


if __name__ == '__main__':
    unittest.main()
