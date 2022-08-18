import pytest

from . import (
    format_smart80,
    format_smart80_align_dynamic,
    format_smart80_align_fixed32,
    format_smart80_knausj,
    golden_path,
)


@pytest.mark.golden_test("data/golden/smart80/default/*.yml")
def test_smart80(golden, benchmark):
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_smart80(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]


@pytest.mark.golden_test("data/golden/smart80/align/dynamic/*.yml")
def test_smart80_align_dynamic(golden, benchmark):
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_smart80_align_dynamic(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]


@pytest.mark.golden_test("data/golden/smart80/align/fixed32/*.yml")
def test_smart80_align_fixed32(golden, benchmark):
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_smart80_align_fixed32(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]


@pytest.mark.golden_test("data/golden/smart80/knausj/*.yml")
def test_smart80_knausj(golden, benchmark):
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_smart80_knausj(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]
