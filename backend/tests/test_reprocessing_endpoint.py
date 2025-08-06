import os
import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add the backend directory to the sys.path to resolve imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag_server import app
import backend.rag_server as rag_server_module
from rag_system.rag_handler import RAGHandler

class ReprocessingEndpointTestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        os.environ["OPENAI_API_KEY"] = "test_api_key"
        
        # Manually mock the global rag_handler for the test
        self.original_rag_handler = rag_server_module.rag_handler
        self.mock_rag_handler = MagicMock(spec=RAGHandler)
        rag_server_module.rag_handler = self.mock_rag_handler

    def tearDown(self):
        # Restore the original rag_handler
        rag_server_module.rag_handler = self.original_rag_handler
        del os.environ["OPENAI_API_KEY"]

    @patch("fastapi.BackgroundTasks.add_task")
    def test_reprocess_materials_endpoint(self, mock_add_task):
        """
        Test the /process-materials endpoint to ensure it triggers the background task.
        """
        # Arrange
        mock_add_task.return_value = None

        # Act
        response = self.client.post("/process-materials", json={"force_reprocess": True, "enable_educational_features": True})

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "success": True,
                "message": "Material processing started in the background.",
            },
        )
        mock_add_task.assert_called_once()
        # Check that the correct kwargs were passed to the task
        call_args = mock_add_task.call_args
        self.assertEqual(call_args.kwargs, {'force_reprocess': True})

if __name__ == "__main__":
    unittest.main()