"""Tests for basic file editor operations."""

from openhands_aci.editor import file_editor

from .conftest import parse_result


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
    result_json = parse_result(result)
    assert (
        "Here's the result of running `cat -n`"
        in result_json['formatted_output_and_error']
    )
    assert 'line 1' in result_json['formatted_output_and_error']

    # Test str_replace
    result = file_editor(
        command='str_replace',
        path=temp_file,
        old_str='line 2',
        new_str='replaced line',
        enable_linting=False,
    )
    result_json = parse_result(result)
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
    result_json = parse_result(result)
    assert 'has been edited' in result_json['formatted_output_and_error']
    assert 'inserted line' in result_json['formatted_output_and_error']

    # Test undo
    result = file_editor(
        command='undo_edit',
        path=temp_file,
        enable_linting=False,
    )
    result_json = parse_result(result)
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
    result_json = parse_result(result)
    # Tabs should be expanded to spaces in output
    assert '    indented' in result_json['formatted_output_and_error']
    assert 'line    with    tabs' in result_json['formatted_output_and_error']

    # Test str_replace with tabs in old_str
    result = file_editor(
        command='str_replace',
        path=temp_file,
        old_str='line\twith\ttabs',
        new_str='replaced line',
        enable_linting=False,
    )
    result_json = parse_result(result)
    assert 'replaced line' in result_json['formatted_output_and_error']

    # Test str_replace with tabs in new_str
    result = file_editor(
        command='str_replace',
        path=temp_file,
        old_str='replaced line',
        new_str='new\tline\twith\ttabs',
        enable_linting=False,
    )
    result_json = parse_result(result)
    # Tabs should be expanded in the output
    assert 'new     line    with    tabs' in result_json['formatted_output_and_error']

    # Test insert with tabs
    result = file_editor(
        command='insert',
        path=temp_file,
        insert_line=1,
        new_str='\tindented\tline',
        enable_linting=False,
    )
    result_json = parse_result(result)
    # Tabs should be expanded in the output
    assert '        indented        line' in result_json['formatted_output_and_error']
