import json
import os
import re
import resource

import psutil
import pytest

from openhands_aci.editor import file_editor


@pytest.fixture
def temp_file(tmp_path):
    # Set up a temporary directory with test files
    test_file = tmp_path / 'test_file.txt'
    test_file.write_text('This is a test file.\nThis file is for testing purposes.')
    return str(test_file)


def test_file_editor_happy_path(temp_file):
    command = 'str_replace'
    old_str = 'test file'
    new_str = 'sample file'

    # Call the `file_editor` function
    result = file_editor(
        command=command,
        path=temp_file,
        old_str=old_str,
        new_str=new_str,
        enable_linting=False,
    )

    # Extract the JSON content using a regular expression
    match = re.search(
        r'<oh_aci_output_[0-9a-f]{32}>(.*?)</oh_aci_output_[0-9a-f]{32}>',
        result,
        re.DOTALL,
    )
    assert match, 'Output does not contain the expected <oh_aci_output_> tags in the correct format.'
    result_dict = json.loads(match.group(1))

    # Validate the formatted output in the result dictionary
    formatted_output = result_dict['formatted_output_and_error']
    assert (
        formatted_output
        == f"""The file {temp_file} has been edited. Here's the result of running `cat -n` on a snippet of {temp_file}:
     1\tThis is a sample file.
     2\tThis file is for testing purposes.
Review the changes and make sure they are as expected. Edit the file again if necessary."""
    )
    assert result_dict['path'] == temp_file
    assert result_dict['prev_exist'] is True
    assert (
        result_dict['old_content']
        == 'This is a test file.\nThis file is for testing purposes.'
    )
    assert (
        result_dict['new_content']
        == 'This is a sample file.\nThis file is for testing purposes.'
    )

    # Ensure the file content was updated
    with open(temp_file, 'r') as f:
        content = f.read()
    assert 'This is a sample file.' in content


def test_file_editor_with_xml_tag_parsing(temp_file):
    # Create content that includes the XML tag pattern
    xml_content = """This is a file with XML tags parsing logic...
match = re.search(
    r'<oh_aci_output_[0-9a-f]{32}>(.*?)</oh_aci_output_[0-9a-f]{32}>',
    result,
    re.DOTALL,
)
...More text here.
"""

    with open(temp_file, 'w') as f:
        f.write(xml_content)

    result = file_editor(
        command='view',
        path=temp_file,
    )

    # Ensure the content is extracted correctly
    match = re.search(
        r'<oh_aci_output_[0-9a-f]{32}>(.*?)</oh_aci_output_[0-9a-f]{32}>',
        result,
        re.DOTALL,
    )

    assert match, 'Output does not contain the expected <oh_aci_output_> tags in the correct format.'
    result_dict = json.loads(match.group(1))

    # Validate the formatted output in the result dictionary
    formatted_output = result_dict['formatted_output_and_error']
    print(formatted_output)
    assert (
        formatted_output
        == f"""Here's the result of running `cat -n` on {temp_file}:
     1\tThis is a file with XML tags parsing logic...
     2\tmatch = re.search(
     3\t    r'<oh_aci_output_[0-9a-f]{{32}}>(.*?)</oh_aci_output_[0-9a-f]{{32}}>',
     4\t    result,
     5\t    re.DOTALL,
     6\t)
     7\t...More text here.
     8\t
"""
    )


def test_validation_error_formatting():
    """Test that validation errors are properly formatted in the output."""
    result = file_editor(
        command='view',
        path='/nonexistent/file.txt',
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'does not exist' in result_json['formatted_output_and_error']
    assert result_json['error'] == 'Invalid `path` parameter: /nonexistent/file.txt. The path /nonexistent/file.txt does not exist. Please provide a valid path.'

    # Test directory validation for non-view commands
    result = file_editor(
        command='str_replace',
        path='/tmp',
        old_str='something',
        new_str='new',
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'only the `view` command' in result_json['formatted_output_and_error']
    assert 'directory and only the `view` command' in result_json['error']

def test_str_replace_error_handling(temp_file):
    """Test error handling in str_replace command."""
    # Create a test file
    content = 'line 1\nline 2\nline 3\n'
    with open(temp_file, 'w') as f:
        f.write(content)

    # Test non-existent string
    result = file_editor(
        command='str_replace',
        path=temp_file,
        old_str='nonexistent',
        new_str='something',
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'did not appear verbatim' in result_json['formatted_output_and_error']
    assert 'did not appear verbatim' in result_json['error']

    # Test multiple occurrences
    with open(temp_file, 'w') as f:
        f.write('line\nline\nother')

    result = file_editor(
        command='str_replace',
        path=temp_file,
        old_str='line',
        new_str='new_line',
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'Multiple occurrences' in result_json['formatted_output_and_error']
    assert 'lines [1, 2]' in result_json['error']

def test_view_range_validation(temp_file):
    """Test validation of view_range parameter."""
    # Create a test file
    content = 'line 1\nline 2\nline 3\n'
    with open(temp_file, 'w') as f:
        f.write(content)

    # Test invalid range format
    result = file_editor(
        command='view',
        path=temp_file,
        view_range=[1],  # Should be [start, end]
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'should be a list of two integers' in result_json['formatted_output_and_error']

    # Test out of bounds range
    result = file_editor(
        command='view',
        path=temp_file,
        view_range=[1, 10],  # File only has 3 lines
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'should be smaller than the number of lines' in result_json['formatted_output_and_error']

    # Test invalid range order
    result = file_editor(
        command='view',
        path=temp_file,
        view_range=[3, 1],  # End before start
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'should be greater than or equal to' in result_json['formatted_output_and_error']

def test_insert_validation(temp_file):
    """Test validation in insert command."""
    # Create a test file
    content = 'line 1\nline 2\nline 3\n'
    with open(temp_file, 'w') as f:
        f.write(content)

    # Test insert at negative line
    result = file_editor(
        command='insert',
        path=temp_file,
        insert_line=-1,
        new_str='new line',
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'should be within the range' in result_json['formatted_output_and_error']

    # Test insert beyond file length
    result = file_editor(
        command='insert',
        path=temp_file,
        insert_line=10,
        new_str='new line',
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'should be within the range' in result_json['formatted_output_and_error']

def test_undo_validation(temp_file):
    """Test undo_edit validation."""
    # Create a test file
    content = 'line 1\nline 2\nline 3\n'
    with open(temp_file, 'w') as f:
        f.write(content)

    # Try to undo without any previous edits
    result = file_editor(
        command='undo_edit',
        path=temp_file,
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'No edit history found' in result_json['formatted_output_and_error']

def test_successful_operations(temp_file):
    """Test successful file operations and their output formatting."""
    # Create a test file
    content = 'line 1\nline 2\nline 3\n'
    with open(temp_file, 'w') as f:
        f.write(content)

    # Test view
    result = file_editor(
        command='view',
        path=temp_file,
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert "Here's the result of running `cat -n`" in result_json['formatted_output_and_error']
    assert 'line 1' in result_json['formatted_output_and_error']

    # Test str_replace
    result = file_editor(
        command='str_replace',
        path=temp_file,
        old_str='line 2',
        new_str='replaced line',
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'has been edited' in result_json['formatted_output_and_error']
    assert 'replaced line' in result_json['formatted_output_and_error']

    # Test insert
    result = file_editor(
        command='insert',
        path=temp_file,
        insert_line=1,
        new_str='inserted line',
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'has been edited' in result_json['formatted_output_and_error']
    assert 'inserted line' in result_json['formatted_output_and_error']

    # Test undo
    result = file_editor(
        command='undo_edit',
        path=temp_file,
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'undone successfully' in result_json['formatted_output_and_error']

def test_tab_expansion(temp_file):
    """Test that tabs are properly expanded in file operations."""
    # Create a file with tabs
    content = 'no tabs\n\tindented\nline\twith\ttabs\n'
    with open(temp_file, 'w') as f:
        f.write(content)

    # Test view command
    result = file_editor(
        command='view',
        path=temp_file,
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    # Tabs should be expanded to spaces in output
    assert '\t' not in result_json['formatted_output_and_error']
    assert '        indented' in result_json['formatted_output_and_error']

    # Test str_replace with tabs in old_str
    result = file_editor(
        command='str_replace',
        path=temp_file,
        old_str='line\twith\ttabs',
        new_str='replaced line',
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'replaced line' in result_json['formatted_output_and_error']

    # Test str_replace with tabs in new_str
    result = file_editor(
        command='str_replace',
        path=temp_file,
        old_str='replaced line',
        new_str='new\tline\twith\ttabs',
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    # Tabs should be expanded in the output
    assert '\t' not in result_json['formatted_output_and_error']
    assert 'new        line        with        tabs' in result_json['formatted_output_and_error']

    # Test insert with tabs
    result = file_editor(
        command='insert',
        path=temp_file,
        insert_line=1,
        new_str='\tindented\tline',
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    # Tabs should be expanded in the output
    assert '\t' not in result_json['formatted_output_and_error']
    assert '        indented        line' in result_json['formatted_output_and_error']

def test_file_validation(temp_file):
    """Test file validation for various file types."""
    # Test binary file
    with open(temp_file, 'wb') as f:
        f.write(b'Some text\x00with binary\x00content')

    result = file_editor(
        command='view',
        path=temp_file,
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'binary' in result_json['formatted_output_and_error'].lower()

    # Test large file
    large_size = 11 * 1024 * 1024  # 11MB
    with open(temp_file, 'w') as f:
        f.write('x' * large_size)

    result = file_editor(
        command='view',
        path=temp_file,
        enable_linting=False,
    )
    result_json = json.loads(result[result.find('{'):result.rfind('}')+1])
    assert 'too large' in result_json['formatted_output_and_error']
    assert '10MB' in result_json['formatted_output_and_error']

def test_file_read_memory_usage(temp_file):
    """Test that reading a large file uses memory efficiently."""
    # Create a large file (9.5MB to stay under 10MB limit)
    file_size_mb = 9.5
    line_size = 100  # bytes per line approximately
    num_lines = int((file_size_mb * 1024 * 1024) // line_size)

    print(f'\nCreating test file with {num_lines} lines...')
    with open(temp_file, 'w') as f:
        for i in range(num_lines):
            f.write(f'Line {i}: ' + 'x' * (line_size - 10) + '\n')

    actual_size = os.path.getsize(temp_file) / (1024 * 1024)
    print(f'File created, size: {actual_size:.2f} MB')

    # Force Python to release file handles and clear buffers
    import gc

    gc.collect()

    # Get initial memory usage
    initial_memory = psutil.Process(os.getpid()).memory_info().rss
    print(f'Initial memory usage: {initial_memory / 1024 / 1024:.2f} MB')

    # Test reading specific lines
    try:
        result = file_editor(
            command='view',
            path=temp_file,
            view_range=[5000, 5100],  # Read 100 lines from middle
        )
    except Exception as e:
        print(f'\nError during file read: {str(e)}')
        raise

    # Check memory usage after reading
    current_memory = psutil.Process(os.getpid()).memory_info().rss
    memory_growth = current_memory - initial_memory
    print(
        f'Memory growth after reading 100 lines: {memory_growth / 1024 / 1024:.2f} MB'
    )

    # Memory growth should be small since we're only reading 100 lines
    # Allow for some overhead but it should be much less than file size
    max_growth_mb = 1  # 1MB max growth
    assert memory_growth < max_growth_mb * 1024 * 1024, (
        f'Memory growth too high: {memory_growth / 1024 / 1024:.2f} MB '
        f'(limit: {max_growth_mb} MB)'
    )

    # Parse the JSON output
    try:
        result_json = json.loads(result[result.find('{') : result.rfind('}') + 1])
        content = result_json['formatted_output_and_error']
    except Exception as e:
        print(f'\nError parsing result: {str(e)}')
        print(f'Result: {result[:200]}...')
        raise

    # Extract the actual content (skip the header)
    content_start = content.find("Here's the result of running `cat -n`")
    if content_start == -1:
        print(f'\nUnexpected content format: {content[:200]}...')
        raise ValueError('Could not find expected content header')
    content_start = content.find('\n', content_start) + 1
    content = content[content_start:]

    # Verify we got the correct lines
    line_count = content.count('\n')
    assert line_count >= 99, f'Should have read at least 99 lines, got {line_count}'
    assert 'Line 5000:' in content, 'Should contain the first requested line'
    assert 'Line 5099:' in content, 'Should contain the last requested line'

    print('Test completed successfully')


def test_file_editor_memory_leak(temp_file):
    """Test to demonstrate memory growth during multiple file edits."""
    print('\nStarting memory leak test...')

    # Set memory limit to 128MB to make it more likely to catch issues
    memory_limit = 128 * 1024 * 1024  # 128MB in bytes
    try:
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
        print('Memory limit set successfully')
    except Exception as e:
        print(f'Warning: Could not set memory limit: {str(e)}')

    initial_memory = psutil.Process(os.getpid()).memory_info().rss
    print(f'\nInitial memory usage: {initial_memory / 1024 / 1024:.2f} MB')

    # Create initial content that's large enough to test but not overwhelming
    # Keep total file size under 10MB to avoid file validation errors
    base_content = (
        'Initial content with some reasonable length to make the file larger\n'
    )
    content = base_content * 100
    print(f'\nCreating initial file with {len(content)} bytes')
    with open(temp_file, 'w') as f:
        f.write(content)
    print(f'Initial file created, size: {os.path.getsize(temp_file) / 1024:.1f} KB')

    try:
        # Store memory readings for analysis
        memory_readings = []
        file_size_mb = 0

        # Perform edits with reasonable content size
        for i in range(1000):  # Increased iterations, smaller content per iteration
            # Create content for each edit - keep it small to avoid file size limits
            old_content = f'content_{i}\n' * 5  # 5 lines per edit
            new_content = f'content_{i + 1}\n' * 5

            # Instead of appending, we'll replace content to keep file size stable
            with open(temp_file, 'r') as f:
                current_content = f.read()

            # Insert old_content at a random position while keeping file size stable
            insert_pos = len(current_content) // 2
            new_file_content = (
                current_content[:insert_pos]
                + old_content
                + current_content[insert_pos + len(old_content) :]
            )
            with open(temp_file, 'w') as f:
                f.write(new_file_content)

            # Perform the edit
            try:
                if i == 0:
                    print(
                        f'\nInitial file size: {os.path.getsize(temp_file) / (1024 * 1024):.2f} MB'
                    )
                    print(f'Sample content to replace: {old_content[:100]}...')
                result = file_editor(
                    command='str_replace',
                    path=temp_file,
                    old_str=old_content,
                    new_str=new_content,
                    enable_linting=False,
                )
                if i == 0:
                    print(f'First edit result: {result[:200]}...')
            except Exception as e:
                print(f'\nError during edit {i}:')
                print(f'File size: {os.path.getsize(temp_file) / (1024 * 1024):.2f} MB')
                print(f'Error: {str(e)}')
                raise

            if i % 25 == 0:  # Check more frequently
                current_memory = psutil.Process(os.getpid()).memory_info().rss
                memory_mb = current_memory / 1024 / 1024
                memory_readings.append(memory_mb)

                # Get current file size
                file_size_mb = os.path.getsize(temp_file) / (1024 * 1024)

                print(f'\nIteration {i}:')
                print(f'Memory usage: {memory_mb:.2f} MB')
                print(f'File size: {file_size_mb:.2f} MB')

                # Calculate memory growth
                memory_growth = current_memory - initial_memory
                growth_percent = (memory_growth / initial_memory) * 100
                print(
                    f'Memory growth: {memory_growth / 1024 / 1024:.2f} MB ({growth_percent:.1f}%)'
                )

                # Fail if memory growth is too high
                assert memory_growth < memory_limit, (
                    f'Memory growth exceeded limit after {i} edits. '
                    f'Growth: {memory_growth / 1024 / 1024:.2f} MB'
                )

                # Check for consistent growth pattern
                if len(memory_readings) >= 3:
                    # Calculate growth rate between last 3 readings
                    growth_rate = (memory_readings[-1] - memory_readings[-3]) / 2
                    print(f'Recent growth rate: {growth_rate:.2f} MB per 50 edits')

                    # Fail if we see consistent growth above a threshold
                    # Allow more growth for initial allocations
                    max_growth = 2 if i < 100 else 1  # MB per 50 edits
                    if growth_rate > max_growth:
                        pytest.fail(
                            f'Consistent memory growth detected: {growth_rate:.2f} MB '
                            f'per 50 edits after {i} edits'
                        )

    except MemoryError:
        pytest.fail('Memory limit exceeded - possible memory leak detected')
    except Exception as e:
        if 'Cannot allocate memory' in str(e):
            pytest.fail('Memory limit exceeded - possible memory leak detected')
        print(f'\nFinal file size: {file_size_mb:.2f} MB')
        raise

    # Print final statistics
    print('\nMemory usage statistics:')
    print(f'Initial memory: {memory_readings[0]:.2f} MB')
    print(f'Final memory: {memory_readings[-1]:.2f} MB')
    print(f'Total growth: {(memory_readings[-1] - memory_readings[0]):.2f} MB')
    print(f'Final file size: {file_size_mb:.2f} MB')
