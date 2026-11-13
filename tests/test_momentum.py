import unittest
from unittest.mock import patch

from momentum import momentum_status_html, display_cultural_momentum


class MomentumTests(unittest.TestCase):
    def test_status_colors_and_labels(self):
        for status, color, icon in [
            ('growing', '#166534', '↑'), ('stable', '#854d0e', '→'),
            ('declining', '#991b1b', '↓'), ('changing', '#1e40af', '↔'),
            ('unverified', '#4b5563', '?'),
        ]:
            html = momentum_status_html(status.upper())
            self.assertIn(color, html)
            self.assertIn(icon, html)
            self.assertIn(status.capitalize(), html)

    def test_unknown_or_missing_status_is_unverified(self):
        for status in (None, {}, 'unexpected', '<script>'):
            self.assertIn('<strong style="font-size:1.15rem">Unverified</strong>', momentum_status_html(status))

    def test_research_explanations_preserved(self):
        with patch('momentum.st.html'), patch('momentum.st.markdown'), patch('momentum.st.write') as write:
            display_cultural_momentum({'status': 'growing', 'assessment': 'Assessment text',
                                       'historical_comparison': 'Historical text'})
        self.assertEqual([call.args[0] for call in write.call_args_list], ['Assessment text', 'Historical text'])


if __name__ == '__main__':
    unittest.main()
