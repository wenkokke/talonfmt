import pytest

from . import format_smart80, format_smart80_align_dynamic, format_smart80_align_fixed32


@pytest.mark.golden_test("golden/smart80/default/*.yml")
def test_smart80_idempotent(golden):
    assert golden["input"] is not None
    output = format_smart80(golden["output"])
    assert (
        output == golden.out["output"]
    ), "Formatter with default options is not idempotent"


@pytest.mark.golden_test("golden/smart80/align/dynamic/*.yml")
def test_smart80_align_dynamic_idempotent(golden):
    assert golden["input"] is not None
    output = format_smart80_align_dynamic(golden["output"])
    assert (
        output == golden.out["output"]
    ), "Formatter with dynamic alignment is not idempotent"


@pytest.mark.golden_test("golden/smart80/align/fixed32/*.yml")
def test_smart80_align_fixed32_idempotent(golden):
    assert golden["input"] is not None
    output = format_smart80_align_fixed32(golden["output"])
    assert (
        output == golden.out["output"]
    ), "Formatter with fixed alignment is not idempotent"
