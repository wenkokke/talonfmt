import pytest

from . import (
    format_simple,
    format_simple_align_dynamic,
    format_simple_align_fixed32,
    golden_path,
)


@pytest.mark.golden_test("data/golden/simple/default/*.yml")
def test_simple_idempotent(golden):
    assert golden["input"] is not None
    output = format_simple(golden["output"], filename=golden_path(golden))
    assert (
        output == golden.out["output"]
    ), "Formatter with default options is not idempotent"


@pytest.mark.golden_test("data/golden/simple/align/dynamic/*.yml")
def test_simple_align_dynamic_idempotent(golden):
    assert golden["input"] is not None
    output = format_simple_align_dynamic(golden["output"], filename=golden_path(golden))
    assert (
        output == golden.out["output"]
    ), "Formatter with dynamic alignment is not idempotent"


@pytest.mark.golden_test("data/golden/simple/align/fixed32/*.yml")
def test_simple_align_fixed32_idempotent(golden):
    assert golden["input"] is not None
    output = format_simple_align_fixed32(golden["output"], filename=golden_path(golden))
    assert (
        output == golden.out["output"]
    ), "Formatter with fixed alignment is not idempotent"
