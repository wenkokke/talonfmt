from pathlib import Path
from typing import Any, Dict, NoReturn, Union, cast

import pytest

pytest.register_assert_rewrite("talonfmt")
pytest.register_assert_rewrite("talonfmt.main")
pytest.register_assert_rewrite("talonfmt.formatter")
pytest.register_assert_rewrite("tree_sitter_type_provider")
pytest.register_assert_rewrite("tree_sitter_type_provider.node_types")

import tree_sitter_talon
from pytest_golden.plugin import GoldenTestFixture

import talonfmt


def golden_path(golden: GoldenTestFixture) -> str:
    return str(golden.path.relative_to(Path(__file__).parent))


def format_simple(contents: str, **kwargs: Any) -> str:  # type: ignore[return]
    try:
        return talonfmt.talonfmt(contents=contents, **kwargs)
    except tree_sitter_talon.ParseError as e:
        _: NoReturn = pytest.fail(str(e))


KWARGS_ALIGN_DYNAMIC: Dict[str, bool] = {
    "align_match_context": True,
    "align_short_commands": True,
}


def format_simple_align_dynamic(contents: str, **kwargs: Any) -> str:
    return format_simple(contents, **KWARGS_ALIGN_DYNAMIC, **kwargs)


KWARGS_ALIGN_FIXED32: Dict[str, Union[int, bool]] = {
    "align_match_context": True,
    "align_match_context_at": 32,
    "align_short_commands": True,
    "align_short_commands_at": 32,
}


def format_simple_align_fixed32(contents: str, **kwargs: Any) -> str:
    return format_simple(contents, **KWARGS_ALIGN_FIXED32, **kwargs)


KWARGS_MAX_LINE_WIDTH_1K: Dict[str, int] = {"max_line_width": 1000}


def format_smart1k(contents: str, **kwargs: Any) -> str:
    return format_simple(contents, **KWARGS_MAX_LINE_WIDTH_1K, **kwargs)


def format_smart1k_align_dynamic(contents: str, **kwargs: Any) -> str:
    return format_simple_align_dynamic(contents, **KWARGS_MAX_LINE_WIDTH_1K, **kwargs)


def format_smart1k_align_fixed32(contents: str, **kwargs: Any) -> str:
    return format_simple_align_fixed32(contents, **KWARGS_MAX_LINE_WIDTH_1K, **kwargs)


KWARGS_MAX_LINE_WIDTH_80: Dict[str, int] = {"max_line_width": 80}


def format_smart80(contents: str, **kwargs: Any) -> str:
    return format_simple(contents, **KWARGS_MAX_LINE_WIDTH_80, **kwargs)


def format_smart80_align_dynamic(contents: str, **kwargs: Any) -> str:
    return format_simple_align_dynamic(contents, **KWARGS_MAX_LINE_WIDTH_80, **kwargs)


def format_smart80_align_fixed32(contents: str, **kwargs: Any) -> str:
    return format_simple_align_fixed32(contents, **KWARGS_MAX_LINE_WIDTH_80, **kwargs)
