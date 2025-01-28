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


def test_file_read_memory_usage(temp_file):
    """Test that reading a large file uses memory efficiently."""
    # Create a large file (10MB)
    file_size_mb = 10
    line_size = 100  # bytes per line approximately
    num_lines = (file_size_mb * 1024 * 1024) // line_size

    with open(temp_file, 'w') as f:
        for i in range(num_lines):
            f.write(f'Line {i}: ' + 'x' * (line_size - 10) + '\n')

    # Get initial memory usage
    initial_memory = psutil.Process(os.getpid()).memory_info().rss
    print(f'\nInitial memory usage: {initial_memory / 1024 / 1024:.2f} MB')

    # Test reading specific lines
    result = file_editor(
        command='view',
        path=temp_file,
        view_range=[5000, 5100],  # Read 100 lines from middle
    )

    # Check memory usage after reading
    current_memory = psutil.Process(os.getpid()).memory_info().rss
    memory_growth = current_memory - initial_memory
    print(
        f'Memory growth after reading 100 lines: {memory_growth / 1024 / 1024:.2f} MB'
    )

    # Memory growth should be small since we're only reading 100 lines
    # Allow for some overhead but it should be much less than file size
    assert memory_growth < 1 * 1024 * 1024, (  # 1MB max growth
        f'Memory growth too high: {memory_growth / 1024 / 1024:.2f} MB'
    )

    # Parse the JSON output
    import json

    result_json = json.loads(result[result.find('{') : result.rfind('}') + 1])
    content = result_json['formatted_output_and_error']

    # Extract the actual content (skip the header)
    content_start = content.find("Here's the result of running `cat -n`")
    content_start = content.find('\n', content_start) + 1
    content = content[content_start:]

    # Verify we got the correct lines
    assert content.count('\n') >= 99, 'Should have read at least 99 lines'
    assert 'Line 5000:' in content, 'Should contain the first requested line'
    assert 'Line 5099:' in content, 'Should contain the last requested line'


def test_file_editor_memory_leak(temp_file):
    """Test to demonstrate memory growth during multiple file edits."""
    # Set memory limit to 256MB to make it more likely to catch issues
    memory_limit = 256 * 1024 * 1024  # 256MB in bytes
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

    initial_memory = psutil.Process(os.getpid()).memory_info().rss
    print(f'\nInitial memory usage: {initial_memory / 1024 / 1024:.2f} MB')

    # Create initial content that's large enough to test but not overwhelming
    content = (
        'Initial content with some reasonable length to make the file larger\n' * 100
    )
    with open(temp_file, 'w') as f:
        f.write(content)

    try:
        # Store memory readings for analysis
        memory_readings = []

        # Perform edits with reasonable content size
        for i in range(500):  # Reduced from 2000 to 500
            # Create content for each edit
            old_content = f'content_{i}\n' * 10  # Reduced from 100 to 10
            new_content = f'content_{i + 1}\n' * 10

            # Add the old content to the file
            with open(temp_file, 'a') as f:
                f.write(old_content)

            # Perform the edit
            file_editor(
                command='str_replace',
                path=temp_file,
                old_str=old_content,
                new_str=new_content,
                enable_linting=False,
            )

            if i % 50 == 0:  # Check more frequently
                current_memory = psutil.Process(os.getpid()).memory_info().rss
                memory_mb = current_memory / 1024 / 1024
                memory_readings.append(memory_mb)
                print(f'Memory usage after {i} edits: {memory_mb:.2f} MB')

                # Calculate memory growth
                memory_growth = current_memory - initial_memory

                # Print memory growth percentage
                growth_percent = (
                    (current_memory - initial_memory) / initial_memory
                ) * 100
                print(
                    f'Memory growth: {memory_growth / 1024 / 1024:.2f} MB ({growth_percent:.1f}%)'
                )

                # Fail if memory growth is too high
                assert memory_growth < memory_limit, (
                    f'Memory growth exceeded limit after {i} edits. '
                    f'Growth: {memory_growth / 1024 / 1024:.2f} MB'
                )

                # Also check for consistent growth pattern
                if len(memory_readings) >= 3:
                    # Calculate growth rate between last 3 readings
                    growth_rate = (memory_readings[-1] - memory_readings[-3]) / 2
                    print(
                        f'Recent memory growth rate: {growth_rate:.2f} MB per 100 edits'
                    )

                    # Fail if we see consistent growth above a threshold
                    if growth_rate > 5:  # More than 5MB growth per 100 edits
                        pytest.fail(
                            f'Consistent memory growth detected: {growth_rate:.2f} MB '
                            f'per 100 edits after {i} edits'
                        )

    except MemoryError:
        pytest.fail('Memory limit exceeded - possible memory leak detected')
    except Exception as e:
        if 'Cannot allocate memory' in str(e):
            pytest.fail('Memory limit exceeded - possible memory leak detected')
        raise

    # Print final statistics
    print('\nMemory usage statistics:')
    print(f'Initial memory: {memory_readings[0]:.2f} MB')
    print(f'Final memory: {memory_readings[-1]:.2f} MB')
    print(f'Total growth: {(memory_readings[-1] - memory_readings[0]):.2f} MB')
