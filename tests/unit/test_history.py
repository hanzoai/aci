"""Tests for file history management."""
import tempfile
from pathlib import Path

from openhands_aci.editor.history import FileHistoryManager


def test_history_keys_are_unique():
    """Test that history keys remain unique even after removing old entries."""
    with tempfile.NamedTemporaryFile() as temp_file:
        path = Path(temp_file.name)
        manager = FileHistoryManager(max_history_per_file=2)

        # Add 3 entries - this should trigger removal of the first entry
        manager.add_history(path, 'content1')
        manager.add_history(path, 'content2')
        manager.add_history(path, 'content3')

        # Get the entries list
        entries = manager.cache.get(f'{str(path)}:entries', [])
        assert len(entries) == 2  # Should only keep last 2 entries

        # Keys should be unique and sequential
        keys = [int(k.split(':')[-1]) for k in entries]
        assert len(set(keys)) == len(keys)  # All keys should be unique
        assert sorted(keys) == keys  # Keys should be sequential

        # Add another entry
        manager.add_history(path, 'content4')
        new_entries = manager.cache.get(f'{str(path)}:entries', [])
        new_keys = [int(k.split(':')[-1]) for k in new_entries]

        # New key should be greater than all previous keys
        assert min(new_keys) > min(keys)
        assert len(set(new_keys)) == len(new_keys)  # All keys should still be unique


def test_history_counter_persists():
    """Test that history counter persists across manager instances."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / 'test.txt'
        path.write_text('initial')

        # First manager instance
        manager1 = FileHistoryManager(history_dir=Path(temp_dir))
        manager1.add_history(path, 'content1')
        manager1.add_history(path, 'content2')

        # Second manager instance using same directory
        manager2 = FileHistoryManager(history_dir=Path(temp_dir))
        manager2.add_history(path, 'content3')

        # Get all entries
        entries = manager2.cache.get(f'{str(path)}:entries', [])
        keys = [int(k.split(':')[-1]) for k in entries]

        # Keys should be sequential even across instances
        assert len(set(keys)) == len(keys)  # All keys should be unique
        assert sorted(keys) == keys  # Keys should be sequential


def test_clear_history_resets_counter():
    """Test that clearing history resets the counter."""
    with tempfile.NamedTemporaryFile() as temp_file:
        path = Path(temp_file.name)
        manager = FileHistoryManager()

        # Add some entries
        manager.add_history(path, 'content1')
        manager.add_history(path, 'content2')

        # Clear history
        manager.clear_history(path)

        # Counter should be reset
        counter = manager.cache.get(f'{str(path)}:counter', None)
        assert counter is None

        # Adding new entries should start from 0
        manager.add_history(path, 'new_content')
        entries = manager.cache.get(f'{str(path)}:entries', [])
        assert len(entries) == 1
        assert entries[0].endswith(':0')  # First key should end with :0