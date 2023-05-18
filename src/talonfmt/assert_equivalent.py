import ast
import re

from tree_sitter_talon import Node, TalonComment, TalonImplicitString, TalonString


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _TalonComment_assert_equivalent(self: TalonComment, other: Node):
    assert isinstance(other, TalonComment)
    assert _collapse_whitespace(self.text) == _collapse_whitespace(other.text)


setattr(TalonComment, "assert_equivalent", _TalonComment_assert_equivalent)


def _TalonImplicitString_assert_equivalent(self: TalonImplicitString, other: Node):
    assert isinstance(other, TalonImplicitString)
    assert self.text.strip() == other.text.strip()


setattr(
    TalonImplicitString, "assert_equivalent", _TalonImplicitString_assert_equivalent
)


def _TalonString_assert_equivalent(self: TalonString, other: Node):
    assert isinstance(other, TalonString)
    # NOTE: use the Python parser to normalise strings
    # TODO: write custom logic to normalise strings?
    try:
        ast1 = ast.parse("f" + self.text)
        ast2 = ast.parse("f" + other.text)
    except SyntaxError:
        ast1 = ast.parse(self.text)
        ast2 = ast.parse(other.text)
    assert ast.unparse(ast1) == ast.unparse(ast2)


setattr(TalonString, "assert_equivalent", _TalonString_assert_equivalent)
