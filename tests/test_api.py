#!/usr/bin/env python3
"""
Basic tests for the MarkItDown API.
"""

import unittest
import requests
from io import BytesIO
import os
import sys
from pathlib import Path


class TestMarkItDownAPI(unittest.TestCase):
    """Tests for the MarkItDown API."""
    
    def setUp(self):
        """Set up the test case."""
        self.api_url = os.environ.get("API_URL", "http://localhost:8000")
        self.test_files_dir = Path(__file__).parent / "test_files"
        self.test_files_dir.mkdir(exist_ok=True)
        
        # Create a simple text file for testing
        self.test_text_file = self.test_files_dir / "sample.txt"
        with open(self.test_text_file, "w") as f:
            f.write("# Sample Document\n\nThis is a sample document for testing the MarkItDown API.")
    
    def test_health_endpoint(self):
        """Test the health endpoint."""
        response = requests.get(f"{self.api_url}/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})
    
    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = requests.get(self.api_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())
    
    def test_convert_text_file(self):
        """Test converting a text file."""
        with open(self.test_text_file, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{self.api_url}/convert", files=files)
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("markdown_content", result)
        self.assertIn("Sample Document", result["markdown_content"])
    
    def test_convert_with_options(self):
        """Test converting a file with options."""
        with open(self.test_text_file, "rb") as f:
            files = {"file": f}
            data = {"enable_plugins": "true"}
            response = requests.post(f"{self.api_url}/convert", files=files, data=data)
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("markdown_content", result)
    
    def test_invalid_file(self):
        """Test with an invalid file."""
        # Create an empty request with no file
        response = requests.post(f"{self.api_url}/convert")
        self.assertNotEqual(response.status_code, 200)  # Should not be successful


if __name__ == "__main__":
    # Check if the API is running
    try:
        api_url = os.environ.get("API_URL", "http://localhost:8000")
        requests.get(f"{api_url}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the API. Make sure it's running.", file=sys.stderr)
        sys.exit(1)
    
    unittest.main() 