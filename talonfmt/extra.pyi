import collections.abc
import dataclasses
import typing

from tree_sitter_talon import AnyListValue, AnyTalonRule, Branch
from tree_sitter_talon import TalonComment as TalonComment
from tree_sitter_talon import TalonDeclaration
from tree_sitter_talon import TalonImplicitString as TalonImplicitString
from tree_sitter_talon import TalonKeyAction, TalonMatch, TalonRule, TalonStatement

@dataclasses.dataclass
class TalonBlock(Branch):
    children: collections.abc.Sequence[typing.Union[TalonStatement, TalonComment]]

    def with_comments(
        self, comments: collections.abc.Iterable[TalonComment]
    ) -> TalonBlock: ...

@dataclasses.dataclass
class TalonCommandDeclaration(Branch, TalonDeclaration):
    children: collections.abc.Sequence[TalonComment]
    left: TalonRule
    right: TalonBlock

    @property
    def rule(self) -> TalonRule: ...
    @property
    def script(self) -> TalonBlock: ...
    def get_docstring(self) -> typing.Optional[str]: ...
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def is_short(self) -> bool: ...

@dataclasses.dataclass
class TalonMatches(Branch):
    children: collections.abc.Sequence[typing.Union[TalonMatch, TalonComment]]

    def is_explicit(self) -> bool: ...

@dataclasses.dataclass
class TalonKeyBindingDeclaration(Branch, TalonDeclaration):
    children: collections.abc.Sequence[TalonComment]
    left: TalonKeyAction
    right: TalonBlock

    @property
    def key(self) -> TalonKeyAction: ...
    @property
    def script(self) -> TalonBlock: ...
    def is_short(self) -> bool: ...
