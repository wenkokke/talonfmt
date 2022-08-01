from . import *


@pytest.mark.golden_test("golden/smart/default/*.yml")
def test_smart_idempotent(golden):
    assert golden["input"] is not None
    output = format_smart(golden["output"])
    assert (
        output == golden.out["output"]
    ), "Formatter with default options is not idempotent"


@pytest.mark.golden_test("golden/smart/align/dynamic/*.yml")
def test_smart_align_dynamic_idempotent(golden):
    assert golden["input"] is not None
    output = format_smart_align_dynamic(golden["output"])
    assert (
        output == golden.out["output"]
    ), "Formatter with dynamic alignment is not idempotent"


@pytest.mark.golden_test("golden/smart/align/fixed32/*.yml")
def test_smart_align_fixed32_idempotent(golden):
    assert golden["input"] is not None
    output = format_smart_align_fixed32(golden["output"])
    assert (
        output == golden.out["output"]
    ), "Formatter with fixed alignment is not idempotent"
