from pathlib import Path
from typing import Any, Dict

import pytest
import talonfmt


# @pytest.mark.golden_test("golden/*.yml")
@pytest.mark.golden_test("golden/knausj_talon_text_generic_editor.yml")
def test_golden(golden):
    doc = talonfmt.format(golden["input"])
    assert doc == golden.out["output"]
