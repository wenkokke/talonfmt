import pytest
import tree_sitter_talon

from . import node_dict_simplify


@pytest.mark.golden_test("data/golden/simple/default/*.yml")
def test_simple_preserves_ast(golden):
    exp = node_dict_simplify(tree_sitter_talon.parse(golden["input"]).to_dict())
    act = node_dict_simplify(tree_sitter_talon.parse(golden["output"]).to_dict())
    assert exp == act, f"Formatter with default options does not preserve the AST"


# @pytest.mark.golden_test("data/golden/simple/align/dynamic/*.yml")
# def test_simple_align_dynamic_preserves_ast(golden):
#     output = format_simple_align_dynamic(golden["output"], filename=golden_path(golden))
#     assert_preserves_ast(golden["input"], output, "with dynamic alignment")


# @pytest.mark.golden_test("data/golden/simple/align/fixed32/*.yml")
# def test_simple_align_fixed32_preserves_ast(golden):
#     output = format_simple_align_fixed32(golden["input"], filename=golden_path(golden))
#     assert_preserves_ast(golden["input"], output, "with fixed alignment")
