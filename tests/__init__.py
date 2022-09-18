import pathlib
import typing

import pytest

pytest.register_assert_rewrite("talonfmt")
pytest.register_assert_rewrite("talonfmt.main")
pytest.register_assert_rewrite("talonfmt.formatter")
pytest.register_assert_rewrite("tree_sitter_type_provider")
pytest.register_assert_rewrite("tree_sitter_type_provider.node_types")

import tree_sitter_talon

import talonfmt


def golden_path(golden) -> str:
    return str(golden.path.relative_to(pathlib.Path(__file__).parent))


def format_simple(contents: str, **kwargs) -> typing.Union[typing.NoReturn, str]:
    try:
        return talonfmt.talonfmt(contents=contents, **kwargs)
    except tree_sitter_talon.ParseError as e:
        return pytest.fail(str(e))


KWARGS_ALIGN_DYNAMIC: dict[str, bool] = {
    "align_match_context": True,
    "align_short_commands": True,
}


def format_simple_align_dynamic(contents: str, **kwargs) -> str:
    return format_simple(contents, **(KWARGS_ALIGN_DYNAMIC | kwargs))


KWARGS_ALIGN_FIXED32: dict[str, typing.Union[int, bool]] = {
    "align_match_context": True,
    "align_match_context_at": 32,
    "align_short_commands": True,
    "align_short_commands_at": 32,
}


def format_simple_align_fixed32(contents: str, **kwargs) -> str:
    return format_simple(contents, **(KWARGS_ALIGN_FIXED32 | kwargs))


KWARGS_MAX_LINE_WIDTH_1K: dict[str, int] = {"max_line_width": 1000}


def format_smart1k(contents: str, **kwargs) -> str:
    return format_simple(contents, **(KWARGS_MAX_LINE_WIDTH_1K | kwargs))


def format_smart1k_align_dynamic(contents: str, **kwargs) -> str:
    return format_simple_align_dynamic(contents, **(KWARGS_MAX_LINE_WIDTH_1K | kwargs))


def format_smart1k_align_fixed32(contents: str, **kwargs) -> str:
    return format_simple_align_fixed32(contents, **(KWARGS_MAX_LINE_WIDTH_1K | kwargs))


KWARGS_MAX_LINE_WIDTH_80: dict[str, int] = {"max_line_width": 80}


def format_smart80(contents: str, **kwargs) -> str:
    return format_simple(contents, **(KWARGS_MAX_LINE_WIDTH_80 | kwargs))


def format_smart80_align_dynamic(contents: str, **kwargs) -> str:
    return format_simple_align_dynamic(contents, **(KWARGS_MAX_LINE_WIDTH_80 | kwargs))


def format_smart80_align_fixed32(contents: str, **kwargs) -> str:
    return format_simple_align_fixed32(contents, **(KWARGS_MAX_LINE_WIDTH_80 | kwargs))
