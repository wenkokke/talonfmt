import collections.abc
import dataclasses
import typing

from tree_sitter_talon import Branch
from tree_sitter_talon import TalonComment as TalonComment
from tree_sitter_talon import TalonDeclaration
from tree_sitter_talon import TalonImplicitString as TalonImplicitString
from tree_sitter_talon import TalonMatch, TalonRule, TalonStatement

@dataclasses.dataclass
class TalonBlock(Branch):
    children: typing.Sequence[typing.Union[TalonStatement, TalonComment]]

    def with_comments(
        self, comments: collections.abc.Iterable[TalonComment]
    ) -> TalonBlock: ...

@dataclasses.dataclass
class TalonCommandDeclaration(Branch, TalonDeclaration):
    children: typing.Sequence[TalonComment]
    rule: TalonRule
    script: TalonBlock

    def is_short(self) -> bool: ...

@dataclasses.dataclass
class TalonMatches(Branch):
    children: typing.Sequence[typing.Union[TalonMatch, TalonComment]]

    def is_explicit(self) -> bool: ...
