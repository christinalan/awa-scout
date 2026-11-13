import copy
import unittest
from unittest.mock import patch

from engagement import build_engagement_charts, display_engagement_dashboard, verified_metrics, source_identity, group_by_source


def metric(value=10, period='2025-01', **overrides):
    # Synthetic fixtures only; never used by the app or research prompt.
    result = dict(name='Monthly active participants', value=value, unit='people',
                  period=period, source_url='https://example.org/evidence', verified=True,
                  comparison_group='Same platform, participant definition, and population',
                  measurement_basis='Unique people during month', period_kind='monthly')
    result.update(overrides)
    return result


def entry(name='Community A', metrics=None):
    return dict(name=name, evidence_type='community', description='Documented participation.',
                source_url='https://example.org/community', metrics=metrics or [])


class EngagementTests(unittest.TestCase):
    def test_source_identity_uses_real_host(self):
        self.assertEqual(source_identity('https://www.youtube.com/watch?v=abc')[0], 'YouTube')
        self.assertEqual(source_identity('https://youtu.be/abc')[0], 'YouTube')
        self.assertEqual(source_identity('https://en.wikipedia.org/wiki/Example')[0], 'Wikipedia')
        self.assertEqual(source_identity('https://youtube.com.example.org/video')[0], 'youtube.com.example.org')
        self.assertEqual(source_identity('https://example.org/?source=youtube.com')[0], 'example.org')

    def test_platform_aliases_share_one_group(self):
        rows = [dict(source_url='https://youtube.com/watch?v=a'),
                dict(source_url='https://youtu.be/b'), dict(source_url='https://tiktok.com/c')]
        groups = list(group_by_source(rows, 'source_url'))
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups[0][1]), 2)

    def test_reject_unsourced_or_non_numeric_metrics(self):
        for overrides in [dict(verified=False), dict(verified='true'), dict(value=True),
                          dict(value='10'), dict(value=float('nan')), dict(value=float('inf')),
                          dict(source_url='javascript:alert(1)'), dict(period=''), dict(unit='')]:
            self.assertEqual(verified_metrics(entry(metrics=[metric(**overrides)])), [])
        self.assertEqual(len(verified_metrics(entry(metrics=[metric(value=0)]))), 1)

    def test_comparable_bar_chart(self):
        rows = [entry(metrics=[metric()]), entry('Community B', [metric(value=20)])]
        charts = build_engagement_charts(rows)
        self.assertEqual(len(charts), 1)
        self.assertEqual(charts[0][0].data[0].type, 'bar')
        self.assertEqual(tuple(charts[0][0].data[0].y), (10, 20))

    def test_incompatible_measurements_never_share_charts(self):
        for overrides in [dict(unit='views'), dict(period='2025-02'),
                          dict(comparison_group='Different platform'),
                          dict(measurement_basis='Cumulative total'),
                          dict(name='Registered participants'), dict(period_kind='snapshot'),
                          dict(comparison_group=''), dict(period='2025-99')]:
            rows = [entry(metrics=[metric()]), entry('Community B', [metric(**overrides)])]
            self.assertEqual(build_engagement_charts(rows), [])

    def test_history_sorted_and_keeps_source(self):
        rows = [entry(metrics=[metric(period='2025-02', value=20), metric(period='2025-01')])]
        chart = build_engagement_charts(rows)[0][0]
        self.assertEqual(chart.data[0].type, 'scatter')
        self.assertEqual(tuple(chart.data[0].x), ('2025-01', '2025-02'))
        self.assertEqual(chart.data[0].customdata[0], 'https://example.org/evidence')
        chart.to_json()

    def test_duplicate_periods_do_not_make_history(self):
        self.assertEqual(build_engagement_charts([entry(metrics=[metric(), metric()])]), [])

    def test_legacy_summary_and_links_remain(self):
        finding = dict(engagement='Original summary with [citation](https://example.org).',
                       sources=[dict(url='https://example.org', platform='Original source')])
        original = copy.deepcopy(finding)
        with patch('engagement.st.write') as write, patch('engagement.st.link_button') as link, patch('engagement.st.expander'), patch('engagement.st.html') as html:
            display_engagement_dashboard(finding)
        write.assert_called_once_with(finding['engagement'])
        link.assert_not_called()
        self.assertIn('href="https://example.org"', html.call_args.args[0])
        self.assertEqual(finding, original)


if __name__ == '__main__':
    unittest.main()
