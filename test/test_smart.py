from . import *


@pytest.mark.golden_test("golden/smart/default/*.yml")
def test_smart(golden):
    output = format_smart(golden["input"])
    assert output == golden.out["output"]


@pytest.mark.golden_test("golden/smart/align/dynamic/*.yml")
def test_smart_align_dynamic(golden):
    output = format_smart_align_dynamic(golden["input"])
    assert output == golden.out["output"]


@pytest.mark.golden_test("golden/smart/align/fixed32/*.yml")
def test_smart_align_fixed32(golden):
    output = format_smart_align_fixed32(golden["input"])
    assert output == golden.out["output"]
