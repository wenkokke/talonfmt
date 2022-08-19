import pytest

from . import (
    format_smart80,
    format_smart80_align_dynamic,
    format_smart80_align_fixed32,
    golden_path,
)


@pytest.mark.golden_test("data/golden/smart80/default/*.yml")
def test_smart80_idempotent(golden):
    assert golden["input"] is not None
    output = format_smart80(golden["output"], filename=golden_path(golden))
    assert (
        output == golden.out["output"]
    ), "Formatter with default options is not idempotent"


@pytest.mark.golden_test("data/golden/smart80/align/dynamic/*.yml")
def test_smart80_align_dynamic_idempotent(golden):
    assert golden["input"] is not None
    output = format_smart80_align_dynamic(
        golden["output"], filename=golden_path(golden)
    )
    assert (
        output == golden.out["output"]
    ), "Formatter with dynamic alignment is not idempotent"


@pytest.mark.golden_test("data/golden/smart80/align/fixed32/*.yml")
def test_smart80_align_fixed32_idempotent(golden):
    assert golden["input"] is not None
    output = format_smart80_align_fixed32(
        golden["output"], filename=golden_path(golden)
    )
    assert (
        output == golden.out["output"]
    ), "Formatter with fixed alignment is not idempotent"