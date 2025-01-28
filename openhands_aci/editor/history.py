"""History management for file edits with disk-based storage and memory constraints."""

import tempfile
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
        # Get list of entry indices for this file
        entries_key = f'{key}:entries'
        entries = self.cache.get(entries_key, [])

        # Add new entry
        entry_key = f'{key}:{len(entries)}'
        self.cache.set(entry_key, content)
        entries.append(entry_key)

        # Keep only last N entries
        if len(entries) > self.max_history_per_file:
            old_key = entries.pop(0)
            self.cache.delete(old_key)

        # Update entries list
        self.cache.set(entries_key, entries)
        print(f'History saved for {file_path}. Current history size: {len(entries)}')

    def get_last_history(self, file_path: Path) -> Optional[str]:
        """Get the most recent history entry for a file."""
        key = str(file_path)
        entries_key = f'{key}:entries'
        entries = self.cache.get(entries_key, [])

        if not entries:
            return None

        # Get and remove last entry
        last_key = entries.pop()
        content = self.cache.get(last_key)
        self.cache.delete(last_key)

        # Update entries list
        self.cache.set(entries_key, entries)
        return content

    def clear_history(self, file_path: Path):
        """Clear history for a given file."""
        key = str(file_path)
        entries_key = f'{key}:entries'
        entries = self.cache.get(entries_key, [])

        # Delete all entries
        for entry_key in entries:
            self.cache.delete(entry_key)

        # Delete entries list
        self.cache.delete(entries_key)
