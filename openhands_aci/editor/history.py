"""History management for file edits with disk-based storage and memory constraints."""

import tempfile
from collections import deque
from pathlib import Path
from typing import Optional

from diskcache import Cache


class FileHistoryManager:
    """Manages file edit history with disk-based storage and memory constraints."""

    def __init__(
        self, max_history_per_file: int = 10, history_dir: Optional[Path] = None
    ):
        """Initialize the history manager.

        Args:
            max_history_per_file: Maximum number of history entries to keep per file
            history_dir: Directory to store history files. If None, uses a temp directory
        """
        self.max_history_per_file = max_history_per_file
        if history_dir is None:
            history_dir = Path(tempfile.mkdtemp(prefix='oh_editor_history_'))
        self.cache = Cache(str(history_dir), size_limit=1e9)  # 1GB size limit

    def add_history(self, file_path: Path, content: str):
        """Add a new history entry for a file."""
        key = str(file_path)
        history = self.cache.get(key, deque(maxlen=self.max_history_per_file))
        history.append(content)
        self.cache.set(key, history)
        print(f'History saved for {file_path}. Current history size: {len(history)}')

    def get_last_history(self, file_path: Path) -> Optional[str]:
        """Get the most recent history entry for a file."""
        key = str(file_path)
        history = self.cache.get(key, deque())
        if not history:
            return None
        content = history.pop()
        self.cache.set(key, history)
        return content

    def clear_history(self, file_path: Path):
        """Clear history for a given file."""
        self.cache.delete(str(file_path))
