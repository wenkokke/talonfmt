import pytest

from . import (
    format_smart1k,
    format_smart1k_align_dynamic,
    format_smart1k_align_fixed32,
    golden_path,
)


@pytest.mark.golden_test("data/golden/smart1k/default/*.yml")
def test_smart1k(golden, benchmark):
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_smart1k(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]


@pytest.mark.golden_test("data/golden/smart1k/align/dynamic/*.yml")
def test_smart1k_align_dynamic(golden, benchmark):
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_smart1k_align_dynamic(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]


@pytest.mark.golden_test("data/golden/smart1k/align/fixed32/*.yml")
def test_smart1k_align_fixed32(golden, benchmark):
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_smart1k_align_fixed32(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]
