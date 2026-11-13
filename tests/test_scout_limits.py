"""Exercise incomplete API responses using mocks only; never send research requests."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch


class ScoutLimitTests(unittest.TestCase):
    def load_scout(self):
        spec = importlib.util.spec_from_file_location('scout_limit_test_module', Path(__file__).resolve().parents[1] / 'scout.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-only'}), patch('openai.OpenAI'):
            spec.loader.exec_module(module)
        module.client = MagicMock()
        return module

    def test_research_limit_does_not_retry_or_save(self):
        scout = self.load_scout()
        scout.client.responses.create.return_value = SimpleNamespace(
            status='incomplete', output_text='{"findings": [',
            incomplete_details=SimpleNamespace(reason='max_output_tokens'))
        with TemporaryDirectory() as directory, patch.object(scout, 'RESULTS_DIR', Path(directory)), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, '32,000-token output limit during research'):
                scout.run_scout('Test request')
            self.assertEqual(list(Path(directory).iterdir()), [])
        self.assertEqual(scout.client.responses.create.call_count, 1)
        self.assertEqual(scout.client.responses.create.call_args.kwargs['max_output_tokens'], 32000)

    def test_formatting_limit_does_not_save_or_retry(self):
        scout = self.load_scout()
        scout.client.responses.create.side_effect = [
            SimpleNamespace(status='completed', output_text='Not JSON'),
            SimpleNamespace(status='incomplete', output_text='', incomplete_details={'reason': 'max_output_tokens'}),
        ]
        with TemporaryDirectory() as directory, patch.object(scout, 'RESULTS_DIR', Path(directory)), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, 'during JSON formatting'):
                scout.run_scout('Test request')
            self.assertEqual(list(Path(directory).iterdir()), [])
        self.assertEqual(scout.client.responses.create.call_count, 2)


if __name__ == '__main__':
    unittest.main()
