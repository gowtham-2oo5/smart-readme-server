import logging
import time
from pathlib import Path
from typing import Any, Dict, List

from config import settings

log = logging.getLogger(__name__)


class FileService:
    """Service for handling local file operations."""

    def __init__(self):
        self.output_dir = Path(settings.output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

    def save_readme(self, owner: str, repo: str, content: str) -> str:
        """Save README content to local file."""
        timestamp = int(time.time())
        filename = f"{owner}-{repo}-{timestamp}.md"
        file_path = self.output_dir / filename

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            log.info("✅ README saved to: %s", file_path)
            return str(file_path)

        except Exception as e:
            log.error("❌ Failed to save README: %s", e)
            raise

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a saved file."""
        path = Path(file_path)

        if not path.exists():
            return {}

        stat = path.stat()
        return {
            "file_path": str(path.absolute()),
            "file_name": path.name,
            "file_size": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
        }

    def list_generated_readmes(self) -> List[Dict[str, Any]]:
        """List all generated README files."""
        try:
            files: List[Dict[str, Any]] = []
            for file_path in self.output_dir.glob("*.md"):
                files.append(
                    {
                        "name": file_path.name,
                        "path": str(file_path.absolute()),
                        "size": file_path.stat().st_size,
                        "created": file_path.stat().st_ctime,
                    }
                )

            # Sort by creation time (newest first)
            files.sort(key=lambda x: x["created"], reverse=True)
            return files

        except Exception as e:
            log.error("❌ Failed to list files: %s", e)
            return []

    def read_readme(self, file_path: str) -> str:
        """Read README content from file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            log.error("❌ Failed to read file: %s", e)
            raise

    def delete_readme(self, file_path: str) -> bool:
        """Delete a README file."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                log.info("✅ Deleted: %s", file_path)
                return True
            return False
        except Exception as e:
            log.error("❌ Failed to delete file: %s", e)
            return False
