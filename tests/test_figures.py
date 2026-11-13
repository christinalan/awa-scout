import unittest
from unittest.mock import patch

from figures import source_label, figure_work_links, display_key_figure_cards


class FigureTests(unittest.TestCase):
    def test_legacy_work_title(self):
        self.assertEqual(source_label('https://en.wikipedia.org/wiki/Gemini_Home_Entertainment'), 'Gemini Home Entertainment')
        self.assertEqual(source_label('https://example.org/'), 'example.org')

    def test_named_work_preferred_and_duplicates_removed(self):
        figure = {'supporting_work': [{'title': 'Gemini Home Entertainment', 'url': 'https://example.org/work'}],
                  'source_urls': ['https://example.org/work', 'javascript:alert(1)']}
        self.assertEqual(figure_work_links(figure), [('Gemini Home Entertainment', 'https://example.org/work')])

    def test_existing_figure_card_preserves_text(self):
        figure = dict(name='Remy Abode', field='Online horror series creation', connection='Creator of Gemini Home Entertainment.', significance='Description of significance.', source_urls=['https://en.wikipedia.org/wiki/Gemini_Home_Entertainment'])
        with patch('figures.st.container'), patch('figures.st.markdown'), patch('figures.st.caption') as caption, patch('figures.st.write') as write, patch('figures.st.link_button') as link, patch('figures.st.image') as image:
            display_key_figure_cards([figure])
        image.assert_not_called()
        caption.assert_called_once_with(figure['field'])
        self.assertEqual([call.args[0] for call in write.call_args_list], [figure['connection'], figure['significance']])
        link.assert_called_once_with('Gemini Home Entertainment', figure['source_urls'][0])


if __name__ == '__main__':
    unittest.main()
