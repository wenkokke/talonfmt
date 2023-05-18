from pytest import mark
from pytest_benchmark.fixture import BenchmarkFixture
from pytest_golden.plugin import GoldenTestFixture

from . import (
    format_smart80,
    format_smart80_align_dynamic,
    format_smart80_align_fixed32,
    golden_path,
)


@mark.golden_test("data/golden/smart80/default/*.yml")
def test_smart80(golden: GoldenTestFixture, benchmark: BenchmarkFixture) -> None:
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_smart80(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]


@mark.golden_test("data/golden/smart80/align/dynamic/*.yml")
def test_smart80_align_dynamic(
    golden: GoldenTestFixture, benchmark: BenchmarkFixture
) -> None:
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_smart80_align_dynamic(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]


@mark.golden_test("data/golden/smart80/align/fixed32/*.yml")
def test_smart80_align_fixed32(
    golden: GoldenTestFixture, benchmark: BenchmarkFixture
) -> None:
    filename = golden_path(golden)
    contents = golden["input"]

    def format() -> str:
        return format_smart80_align_fixed32(contents, filename=filename)

    assert benchmark(format) == golden.out["output"]
