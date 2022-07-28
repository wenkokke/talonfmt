import pytest
import talonfmt


@pytest.mark.golden_test("golden/default/*.yml")
def test_golden_default(golden):
    output = talonfmt.talonfmt(
        contents=golden["input"]
    )
    assert output == golden.out["output"]


# @pytest.mark.golden_test("golden/align/dynamic/*.yml")
# def test_golden_align_dynamic(golden):
#     output = talonfmt.talonfmt(
#         contents=golden["input"],
#         align_match_context=True,
#         align_short_commands=True
#     )
#     assert output == golden.out["output"]


# @pytest.mark.golden_test("golden/align/fixed32/*.yml")
# def test_golden_align_fixed32(golden):
#     output = talonfmt.talonfmt(
#         contents=golden["input"],
#         align_match_context=True,
#         align_match_context_at=32,
#         align_short_commands=True,
#         align_short_commands_at=32,
#     )
#     assert output == golden.out["output"]
