from typing import Optional
import pytest
from talonfmt import ParseError
import talonfmt


def format(contents: str, **kwargs) -> str:
    try:
        return talonfmt.talonfmt(contents=contents, **kwargs)
    except ParseError as e:
        pytest.fail(e.message(contents=contents))


@pytest.mark.golden_test("golden/default/*.yml")
def test_formatter_default_golden(golden):
    output = format(golden["input"])
    assert output == golden.out["output"]


@pytest.mark.golden_test("golden/default/*.yml")
def test_formatter_default_idempotent(golden):
    assert golden["input"] is not None
    output = format(golden["output"])
    assert output == golden.out["output"], "Default formatter is not idempotent"


@pytest.mark.golden_test("golden/align/dynamic/*.yml")
def test_formatter_align_dynamic_golden(golden):
    output = format(
        golden["input"],
        align_match_context=True,
        align_short_commands=True,
    )
    assert output == golden.out["output"]


@pytest.mark.golden_test("golden/align/dynamic/*.yml")
def test_formatter_align_dynamic_idempotent(golden):
    assert golden["input"] is not None
    output = format(
        golden["output"],
        align_match_context=True,
        align_short_commands=True,
    )
    assert (
        output == golden.out["output"]
    ), "Dynamic alignment formatter is not idempotent"


@pytest.mark.golden_test("golden/align/fixed32/*.yml")
def test_formatter_align_fixed32_golden(golden):
    output = format(
        golden["input"],
        align_match_context=True,
        align_match_context_at=32,
        align_short_commands=True,
        align_short_commands_at=32,
    )
    assert output == golden.out["output"]


@pytest.mark.golden_test("golden/align/fixed32/*.yml")
def test_formatter_align_fixed32_idempotent(golden):
    assert golden["input"] is not None
    output = format(
        golden["output"],
        align_match_context=True,
        align_match_context_at=32,
        align_short_commands=True,
        align_short_commands_at=32,
    )
    assert output == golden.out["output"], "Fixed alignment formatter is not idempotent"
