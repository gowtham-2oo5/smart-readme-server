import os
import time
from pathlib import Path
from typing import Dict
from config import Config

class FileService:
    """Service for handling local file operations"""
    
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_readme(self, owner: str, repo: str, content: str) -> str:
        """Save README content to local file"""
        timestamp = int(time.time())
        filename = f"{owner}-{repo}-{timestamp}.md"
        file_path = self.output_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ README saved to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"❌ Failed to save README: {e}")
            raise
    
    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """Get information about saved file"""
        path = Path(file_path)
        
        if not path.exists():
            return {}
        
        stat = path.stat()
        return {
            'file_path': str(path.absolute()),
            'file_name': path.name,
            'file_size': stat.st_size,
            'created_at': stat.st_ctime,
            'modified_at': stat.st_mtime
        }
    
    def list_generated_readmes(self) -> list:
        """List all generated README files"""
        try:
            files = []
            for file_path in self.output_dir.glob("*.md"):
                files.append({
                    'name': file_path.name,
                    'path': str(file_path.absolute()),
                    'size': file_path.stat().st_size,
                    'created': file_path.stat().st_ctime
                })
            
            # Sort by creation time (newest first)
            files.sort(key=lambda x: x['created'], reverse=True)
            return files
            
        except Exception as e:
            print(f"❌ Failed to list files: {e}")
            return []
    
    def read_readme(self, file_path: str) -> str:
        """Read README content from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Failed to read file: {e}")
            raise
    
    def delete_readme(self, file_path: str) -> bool:
        """Delete a README file"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                print(f"✅ Deleted: {file_path}")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to delete file: {e}")
            return False
