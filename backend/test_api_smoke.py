"""Flask compatibility checks with synthetic data and inert speech providers.

These tests do not validate NeMo inference or call any speech service.
"""
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


class ApiSmokeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        modules = {}
        for name, functions in {
            'utils.process_manager': ['start_processing', 'get_processing_status'],
            'speaker_id_testing': ['process_conversation'],
            'update_speaker_db_verified': ['update_speaker_database'],
            'rename_speaker': ['rename_speaker_in_conversation'],
        }.items():
            module = types.ModuleType(name)
            for function in functions:
                setattr(module, function, Mock(side_effect=AssertionError('Unexpected provider call')))
            modules[name] = module
        spec = importlib.util.spec_from_file_location('synthetic_speaker_app', Path(__file__).with_name('app.py'))
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules', modules), patch('os.makedirs'):
            spec.loader.exec_module(self.module)
        self.module.CONVERSATIONS_FOLDER = self.directory.name
        self.module.UPLOAD_FOLDER = self.directory.name
        self.module.app.config['TESTING'] = True
        self.client = self.module.app.test_client()

    def test_health(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'ok')

    def test_empty_conversation_list(self):
        self.assertEqual(self.client.get('/api/conversations').json, [])

    def test_synthetic_conversation(self):
        folder = Path(self.directory.name) / 'synthetic'
        folder.mkdir()
        (folder / 'metadata.json').write_text(json.dumps({
            'original_audio': 'synthetic.wav', 'duration_seconds': 2,
            'date_processed': '2026-01-01T00:00:00', 'utterances': [{
                'id': 'u1', 'start_ms': 0, 'end_ms': 2000, 'text': 'Synthetic test',
                'speaker': 'Test Speaker', 'embedding_id': 'test-id', 'confidence': 0.9,
            }],
        }))
        response = self.client.get('/api/conversations')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]['segments'][0]['end'], 2)
        self.assertEqual(response.json[0]['segments'][0]['speaker']['speakerName'], 'Test Speaker')

    def test_missing_upload(self):
        self.assertEqual(self.client.post('/api/process').status_code, 400)

    def test_invalid_rename(self):
        self.assertEqual(self.client.post('/api/speakers/rename', json={}).status_code, 400)

    def test_missing_conversation(self):
        self.assertEqual(self.client.get('/api/conversations/missing').status_code, 404)

    def test_local_frontend_cors(self):
        response = self.client.get('/api/health', headers={'Origin': 'http://localhost:3000'})
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'http://localhost:3000')


if __name__ == '__main__':
    unittest.main()
