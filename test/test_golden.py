import pytest
import talonfmt


@pytest.mark.golden_test("golden/default/*.yml")
def test_golden_default(golden):
    output1 = talonfmt.talonfmt(contents=golden["input"])
    assert output1 == golden.out["output"]
    output2 = talonfmt.talonfmt(contents=output1)
    assert output2 == output1, f"Default formatting is not idempodent"


@pytest.mark.golden_test("golden/align/dynamic/*.yml")
def test_golden_align_dynamic(golden):
    output1 = talonfmt.talonfmt(
        contents=golden["input"], align_match_context=True, align_short_commands=True
    )
    assert output1 == golden.out["output"]
    output2 = talonfmt.talonfmt(
        contents=output1, align_match_context=True, align_short_commands=True
    )
    assert output2 == output1, f"Dynamic alignment is not idempodent"


@pytest.mark.golden_test("golden/align/fixed32/*.yml")
def test_golden_align_fixed32(golden):
    output1 = talonfmt.talonfmt(
        contents=golden["input"],
        align_match_context=True,
        align_match_context_at=32,
        align_short_commands=True,
        align_short_commands_at=32,
    )
    assert output1 == golden.out["output"]
    output2 = talonfmt.talonfmt(
        contents=output1,
        align_match_context=True,
        align_match_context_at=32,
        align_short_commands=True,
        align_short_commands_at=32,
    )
    assert output2 == output1, f"Fixed alignment is not idempodent"
