import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.rag_server import app

class ReprocessingEndpointTestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Set a dummy API key for testing purposes
        os.environ["OPENAI_API_KEY"] = "test_api_key"

    def tearDown(self):
        # Unset the dummy API key after tests
        del os.environ["OPENAI_API_KEY"]

    @patch("backend.rag_server.reprocess_enhanced_task")
    def test_reprocess_enhanced_materials_endpoint(self, mock_reprocess_task):
        """
        Test the /reprocess-enhanced-materials endpoint to ensure it triggers the background task.
        """
        # Arrange
        mock_reprocess_task.return_value = None

        # Act
        response = self.client.post("/reprocess-enhanced-materials")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "success": True,
                "message": "[ENHANCED] Reprocessing of materials initiated in the background. This may take several minutes.",
            },
        )
        mock_reprocess_task.assert_called_once()

if __name__ == "__main__":
    unittest.main()