import pytest

from . import (
    format_simple,
    format_simple_align_dynamic,
    format_simple_align_fixed32,
    golden_path,
)


@pytest.mark.golden_test("data/golden/simple/default/*.yml")
def test_simple(golden, benchmark):
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_simple(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]


@pytest.mark.golden_test("data/golden/simple/align/dynamic/*.yml")
def test_simple_align_dynamic(golden, benchmark):
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_simple_align_dynamic(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]


@pytest.mark.golden_test("data/golden/simple/align/fixed32/*.yml")
def test_simple_align_fixed32(golden, benchmark):
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_simple_align_fixed32(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]
