import pytest

from . import (
    format_smart1k,
    format_smart1k_align_dynamic,
    format_smart1k_align_fixed32,
    golden_path,
)


@pytest.mark.golden_test("data/golden/smart1k/default/*.yml")
def test_smart1k_idempotent(golden):
    assert golden["input"] is not None
    output = format_smart1k(golden["output"], filename=golden_path(golden))
    assert (
        output == golden.out["output"]
    ), "Formatter with default options is not idempotent"


@pytest.mark.golden_test("data/golden/smart1k/align/dynamic/*.yml")
def test_smart1k_align_dynamic_idempotent(golden):
    assert golden["input"] is not None
    output = format_smart1k_align_dynamic(
        golden["output"], filename=golden_path(golden)
    )
    assert (
        output == golden.out["output"]
    ), "Formatter with dynamic alignment is not idempotent"


@pytest.mark.golden_test("data/golden/smart1k/align/fixed32/*.yml")
def test_smart1k_align_fixed32_idempotent(golden):
    assert golden["input"] is not None
    output = format_smart1k_align_fixed32(
        golden["output"], filename=golden_path(golden)
    )
    assert (
        output == golden.out["output"]
    ), "Formatter with fixed alignment is not idempotent"
