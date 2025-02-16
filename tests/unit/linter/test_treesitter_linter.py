from openhands_aci.linter import DefaultLinter, LintResult
from openhands_aci.linter.impl.treesitter import TreesitterBasicLinter


def test_syntax_error_py_file(syntax_error_py_file):
    linter = TreesitterBasicLinter()
    result = linter.lint(syntax_error_py_file)
    print(result)
    assert isinstance(result, list) and len(result) == 1
    assert result[0] == LintResult(
        file=syntax_error_py_file,
        line=5,
        column=5,
        message='Syntax error',
    )

    assert (
        result[0].visualize()
        == (
            '2|    def foo():\n'
            '3|        print("Hello, World!")\n'
            '4|    print("Wrong indent")\n'
            '\033[91m5|    foo(\033[0m\n'  # color red
            '      ^ ERROR HERE: Syntax error\n'
            '6|'
        )
    )
    print(result[0].visualize())

    general_linter = DefaultLinter()
    general_result = general_linter.lint(syntax_error_py_file)
    # NOTE: general linter returns different result
    # because it uses flake8 first, which is different from treesitter
    assert general_result != result
