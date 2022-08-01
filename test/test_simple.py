import pytest

from . import format_simple, format_simple_align_dynamic, format_simple_align_fixed32


@pytest.mark.golden_test("golden/simple/default/*.yml")
def test_simple(golden):
    output = format_simple(golden["input"])
    assert output == golden.out["output"]


@pytest.mark.golden_test("golden/simple/align/dynamic/*.yml")
def test_simple_align_dynamic(golden):
    output = format_simple_align_dynamic(golden["input"])
    assert output == golden.out["output"]


@pytest.mark.golden_test("golden/simple/align/fixed32/*.yml")
def test_simple_align_fixed32(golden):
    output = format_simple_align_fixed32(golden["input"])
    assert output == golden.out["output"]
