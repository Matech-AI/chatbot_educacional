```python
import os
import logging
from pathlib import Path
from typing import List, Optional
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DriveHandler:
    """Handles downloading and managing files from Google Drive"""
    
    def __init__(self, materials_dir: str = "data/materials"):
        self.materials_dir = Path(materials_dir)
        self.materials_dir.mkdir(parents=True, exist_ok=True)
    
    def download_file(self, file_id: str, filename: str) -> Optional[Path]:
        """
        Download a single file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            filename: Name to save the file as
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Direct download URL
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            # Download file
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save file
            file_path = self.materials_dir / filename
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"Downloaded {filename}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error downloading {filename}: {str(e)}")
            return None
    
    def process_folder(self, folder_url: str) -> List[Path]:
        """
        Process all files in a Google Drive folder
        
        Args:
            folder_url: URL to Google Drive folder
            
        Returns:
            List of paths to downloaded files
        """
        # Extract folder ID from URL
        parsed_url = urlparse(folder_url)
        path_parts = parsed_url.path.split('/')
        folder_id = path_parts[-1]
        
        # For demo, we'll use a predefined list of files
        # In production, this would use the Google Drive API
        demo_files = [
            ("file1_id", "treinamento_forca.pdf"),
            ("file2_id", "periodizacao.pdf"),
            ("file3_id", "nutricao_esportiva.pdf")
        ]
        
        downloaded_files = []
        for file_id, filename in demo_files:
            file_path = self.download_file(file_id, filename)
            if file_path:
                downloaded_files.append(file_path)
                
        return downloaded_files
```