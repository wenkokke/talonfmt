from pathlib import Path
from typing import Any, Dict

import pytest
import talon_fmt


# @pytest.mark.golden_test("golden/*.yml")
# @pytest.mark.golden_test("golden/knausj_talon_text_generic_editor.yml")
# def test_golden(golden):
#     doc = talon_fmt.format(golden["input"])
#     assert doc == golden.out["output"]
