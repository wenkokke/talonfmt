import pytest

from . import (
    format_smart1k,
    format_smart1k_align_dynamic,
    format_smart1k_align_fixed32,
    golden_path,
)


@pytest.mark.golden_test("data/golden/smart1k/default/*.yml")
def test_smart1k(golden):
    output = format_smart1k(golden["input"], filename=golden_path(golden))
    assert output == golden.out["output"]


@pytest.mark.golden_test("data/golden/smart1k/align/dynamic/*.yml")
def test_smart1k_align_dynamic(golden):
    output = format_smart1k_align_dynamic(golden["input"], filename=golden_path(golden))
    assert output == golden.out["output"]


@pytest.mark.golden_test("data/golden/smart1k/align/fixed32/*.yml")
def test_smart1k_align_fixed32(golden):
    output = format_smart1k_align_fixed32(golden["input"], filename=golden_path(golden))
    assert output == golden.out["output"]
