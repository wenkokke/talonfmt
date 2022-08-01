import pytest

from . import format_smart80, format_smart80_align_dynamic, format_smart80_align_fixed32


@pytest.mark.golden_test("golden/smart80/default/*.yml")
def test_smart80(golden):
    output = format_smart80(golden["input"])
    assert output == golden.out["output"]


@pytest.mark.golden_test("golden/smart80/align/dynamic/*.yml")
def test_smart80_align_dynamic(golden):
    output = format_smart80_align_dynamic(golden["input"])
    assert output == golden.out["output"]


@pytest.mark.golden_test("golden/smart80/align/fixed32/*.yml")
def test_smart80_align_fixed32(golden):
    output = format_smart80_align_fixed32(golden["input"])
    assert output == golden.out["output"]
