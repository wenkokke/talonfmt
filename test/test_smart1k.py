from . import *


@pytest.mark.golden_test("golden/smart1k/default/*.yml")
def test_smart1k(golden):
    output = format_smart1k(golden["input"])
    assert output == golden.out["output"]


@pytest.mark.golden_test("golden/smart1k/align/dynamic/*.yml")
def test_smart1k_align_dynamic(golden):
    output = format_smart1k_align_dynamic(golden["input"])
    assert output == golden.out["output"]


@pytest.mark.golden_test("golden/smart1k/align/fixed32/*.yml")
def test_smart1k_align_fixed32(golden):
    output = format_smart1k_align_fixed32(golden["input"])
    assert output == golden.out["output"]
