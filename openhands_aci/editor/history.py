"""History management for file edits with disk-based storage and memory constraints."""

import json
import os
import shutil
import tempfile
from collections import deque
from pathlib import Path
from typing import Optional


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
        self._temp_dir: Optional[str] = None
        if history_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix='oh_editor_history_')
            self.history_dir = Path(self._temp_dir)
        else:
            self.history_dir = history_dir
            self.history_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache of recent histories with access order
        self._cache: dict[Path, deque[str]] = {}
        self._cache_order: list[Path] = []  # Track access order
        self.MAX_CACHE_ENTRIES = 5

    def __del__(self):
        """Cleanup temporary directory if one was created."""
        if self._temp_dir is not None:
            shutil.rmtree(self._temp_dir, ignore_errors=True)

    def _get_history_path(self, file_path: Path) -> Path:
        """Get the path where history for a file should be stored."""
        # Use file path hash to avoid issues with special characters
        return self.history_dir / f'{hash(str(file_path))}.history'

    def _load_history(self, file_path: Path) -> deque:
        """Load history from disk for a given file."""
        history_path = self._get_history_path(file_path)
        if history_path in self._cache:
            return self._cache[history_path]

        if not history_path.exists():
            return deque(maxlen=self.max_history_per_file)

        try:
            with open(history_path, 'r') as f:
                history_list = json.load(f)
                history = deque(history_list, maxlen=self.max_history_per_file)

            # Update cache
            if history_path in self._cache:
                # Move to end (most recently used)
                self._cache_order.remove(history_path)
                self._cache_order.append(history_path)
            else:
                # Add new entry
                if len(self._cache) >= self.MAX_CACHE_ENTRIES:
                    # Remove least recently used entry
                    oldest_path = self._cache_order.pop(0)
                    del self._cache[oldest_path]
                self._cache_order.append(history_path)
            self._cache[history_path] = history

            return history
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or can't be read, start fresh
            return deque(maxlen=self.max_history_per_file)

    def _save_history(self, file_path: Path, history: deque):
        """Save history to disk for a given file."""
        history_path = self._get_history_path(file_path)
        try:
            with open(history_path, 'w') as f:
                json.dump(list(history), f)
        except IOError:
            # If we can't save, just continue - it's not critical
            pass

    def add_history(self, file_path: Path, content: str):
        """Add a new history entry for a file."""
        history = self._load_history(file_path)
        history.append(content)
        self._save_history(file_path, history)
        print(f'History saved for {file_path}. Current history size: {len(history)}')

    def get_last_history(self, file_path: Path) -> Optional[str]:
        """Get the most recent history entry for a file."""
        history = self._load_history(file_path)
        if not history:
            return None
        content = history.pop()
        self._save_history(file_path, history)
        return content

    def clear_history(self, file_path: Path):
        """Clear history for a given file."""
        history_path = self._get_history_path(file_path)
        if history_path in self._cache:
            del self._cache[history_path]
            self._cache_order.remove(history_path)
        try:
            os.remove(history_path)
        except FileNotFoundError:
            pass
