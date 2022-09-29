import dataclasses
import enum
import typing
from collections.abc import Iterable, Iterator
from functools import singledispatchmethod
from typing import Optional, TypeVar, Union

from doc_printer import (
    Doc,
    DocLike,
    Fail,
    Line,
    Space,
    Text,
    alt,
    angles,
    braces,
    brackets,
    cat,
    create_table,
    inline,
    nest,
    parens,
    row,
    smart_quote,
)
from doc_printer.doc import splat
from tree_sitter_talon import (
    Node,
    TalonAction,
    TalonArgumentList,
    TalonAssignmentStatement,
    TalonBinaryOperator,
    TalonBlock,
    TalonCapture,
    TalonChoice,
    TalonCommandDeclaration,
    TalonComment,
    TalonDeclaration,
    TalonDeclarations,
    TalonEndAnchor,
    TalonExpressionStatement,
    TalonFloat,
    TalonIdentifier,
    TalonImplicitString,
    TalonInteger,
    TalonInterpolation,
    TalonKeyAction,
    TalonKeyBindingDeclaration,
    TalonList,
    TalonMatch,
    TalonMatches,
    TalonMatchModifier,
    TalonOperator,
    TalonOptional,
    TalonParenthesizedExpression,
    TalonParenthesizedRule,
    TalonRepeat,
    TalonRepeat1,
    TalonRule,
    TalonSeq,
    TalonSettingsDeclaration,
    TalonSleepAction,
    TalonSourceFile,
    TalonStartAnchor,
    TalonStatement,
    TalonString,
    TalonStringContent,
    TalonStringEscapeSequence,
    TalonTagImportDeclaration,
    TalonUnaryOperator,
    TalonVariable,
    TalonWord,
)

from .assert_equivalent import *

TalonBlockLevel = Union[
    TalonSourceFile,
    TalonMatches,
    TalonMatch,
    TalonDeclarations,
    TalonDeclaration,
    TalonBlock,
    TalonStatement,
    TalonComment,
]

NodeVar = TypeVar("NodeVar", bound=Node)


class EmptyMatchContext(enum.IntEnum):
    Show = 0
    Keep = 1
    Hide = 2


@dataclasses.dataclass
class TalonFormatter:
    indent_size: int
    align_match_context: Union[bool, int]
    align_short_commands: Union[bool, int]
    empty_match_context: EmptyMatchContext
    format_comments: bool
    preserve_blank_lines_in_header: bool
    preserve_blank_lines_in_body: bool
    preserve_blank_lines_in_command: bool

    @property
    def show_empty_match_context(self) -> bool:
        return self.empty_match_context is EmptyMatchContext.Show

    @property
    def keep_empty_match_context(self) -> bool:
        return self.empty_match_context is EmptyMatchContext.Keep

    @singledispatchmethod
    def format(self, node: Node) -> Doc:
        """
        Format any node as a document.
        """
        # NOTE: these should implement format_lines
        if isinstance(
            node,
            (
                TalonSourceFile,
                TalonMatches,
                TalonDeclaration,
                TalonBlock,
                TalonStatement,
                TalonComment,
            ),
        ):
            return cat(self.format_lines(node))
        else:
            raise TypeError(type(node))

    @singledispatchmethod
    def format_lines(self, node: TalonBlockLevel) -> Iterator[Doc]:
        """
        Format any block-level node as a series of lines.
        """
        if isinstance(node, TalonComment):
            yield self.format(node)
        else:
            raise TypeError(type(node))

    def format_children(self, children: Iterable[Node]) -> Iterator[Doc]:
        for child in self.store_comments_with_type(children, node_type=Node):
            if isinstance(child, Iterable):
                yield from self.format_children(child)
            else:
                yield self.format(child)

    ###########################################################################
    # Format: Source Files
    ###########################################################################

    @format_lines.register
    def _(self, node: TalonSourceFile) -> Iterator[Doc]:

        # Used to emit the match context separator.
        in_header: bool = True

        # Used to buffer comments to ensure that they're split correctly
        # between the header and body.
        match_context_comment_buffer: list[Doc] = []

        def clear_match_context_comment_buffer() -> Iterator[Doc]:
            if match_context_comment_buffer:
                yield from match_context_comment_buffer
                match_context_comment_buffer.clear()

        if self.align_short_commands is True:
            # Used to buffer short commands to group them as tables.
            short_command_buffer: list[Doc] = []

            def clear_short_command_buffer() -> Iterator[Doc]:
                if short_command_buffer:
                    table = create_table(short_command_buffer)
                    if table:
                        yield alt(cat(short_command_buffer), table)
                    else:
                        yield from short_command_buffer
                    short_command_buffer.clear()

        # Used to insert blank lines.
        previous_line: int = 0

        # Iterate over children, flatten any TalonDeclarations node
        def children() -> Iterator[
            typing.Union[TalonDeclaration, TalonMatches, TalonComment]
        ]:
            for child in node.children:
                if isinstance(child, TalonDeclarations):
                    yield from child.children
                else:
                    yield child

        for child in children():
            extra_blank_line: bool = child.start_position.line - previous_line >= 2

            # buffer comments in match context
            if in_header and isinstance(child, TalonComment):
                if self.preserve_blank_lines_in_body and extra_blank_line:
                    match_context_comment_buffer.append(Line)
                match_context_comment_buffer.append(self.format(child))

            # format the .talon file match context
            elif isinstance(child, TalonMatches):
                assert in_header  # must still be in the header
                yield from clear_match_context_comment_buffer()
                yield from self.format_lines(child)
                if (
                    bool(child.children)
                    or (child.is_explicit() and self.keep_empty_match_context)
                    or self.show_empty_match_context
                ):
                    yield Text("-") / Line
                in_header = False

            # format the .talon file body
            else:
                # for dynamic alignment:
                #   buffer short commands and clear the short command buffer
                #   when anything other kind of node is encountered
                if self.align_short_commands is True:
                    if isinstance(child, TalonCommandDeclaration) and child.is_short():
                        if self.preserve_blank_lines_in_body and extra_blank_line:
                            if not short_command_buffer:
                                yield Line
                        short_command_buffer.extend(self.format_lines(child))
                    else:
                        yield from clear_short_command_buffer()
                        if self.preserve_blank_lines_in_body and extra_blank_line:
                            yield Line
                        yield from self.format_lines(child)

                # otherwise:
                #   emit formatted nodes as they are encountered
                else:
                    if self.preserve_blank_lines_in_body and extra_blank_line:
                        yield Line
                    yield from self.format_lines(child)

            # update previous line
            previous_line = child.end_position.line

        # file ends with a short command, clear the short command buffer
        if self.align_short_commands is True:
            yield from clear_short_command_buffer()

    ###########################################################################
    # Format: Match Context
    ###########################################################################

    @format_lines.register
    def _(self, node: TalonMatches) -> Iterator[Doc]:

        # Used to insert blank lines.
        previous_line: Optional[int] = None

        for child in node.children:
            if (
                self.preserve_blank_lines_in_header
                and previous_line is not None
                and child.start_position.line - previous_line >= 2
            ):
                yield Line

            yield from self.with_comments(self.format_lines(child))

            # Update previous line.
            previous_line = child.end_position.line

    @format_lines.register
    def _(self, node: TalonMatch) -> Iterator[Doc]:
        self.assert_only_comments(node.children)
        keywords = self.format_match_modifiers(node.modifiers)
        key = self.format(node.left)
        pattern = self.format(node.right)
        if isinstance(self.align_match_context, bool):
            yield row(
                keywords / key / ":",
                pattern,
                table_type="match",
            )
        else:
            yield row(
                keywords / key / ":",
                pattern,
                table_type="match",
                min_col_widths=(self.align_match_context,),
            )

    def format_match_modifiers(
        self,
        modifiers: typing.Sequence[TalonMatchModifier],
    ) -> Iterator[Doc]:
        if any(modifier.text == "and" for modifier in modifiers):
            yield Text("and")
            yield Space
        if any(modifier.text == "not" for modifier in modifiers):
            yield Text("not")
            yield Space

    ###########################################################################
    # Format: Tag Import Declaration
    ###########################################################################

    @format_lines.register
    def _(self, node: TalonTagImportDeclaration) -> Iterator[Doc]:
        self.assert_only_comments(node.children)
        yield from self.with_comments("tag():" // self.format(node.right) / Line)

    ###########################################################################
    # Format: Settings Declaration
    ###########################################################################

    @format_lines.register
    def _(self, node: TalonSettingsDeclaration) -> Iterator[Doc]:
        assert node.children is None
        yield "settings():" / nest(
            self.indent_size,
            Line,
            self.format(node.right),
        )

    ###########################################################################
    # Format: Key Bindings
    ###########################################################################

    @format_lines.register
    def _(self, node: TalonKeyBindingDeclaration) -> Iterator[Doc]:
        assert node.children is None
        rule = self.format(node.left)
        script = self.format(node.right)
        yield from self.format_command(rule, script, node.is_short())

    ###########################################################################
    # Format: Commands
    ###########################################################################

    @format_lines.register
    def _(self, node: TalonCommandDeclaration) -> Iterator[Doc]:
        assert node.children is None
        rule = self.format(node.left)
        script = self.format(node.right)
        yield from self.format_command(rule, script, node.is_short())

    def format_command(self, rule: Doc, script: Doc, is_short: bool) -> Iterator[Doc]:
        # (1): a line-break after the rule, e.g.,
        #
        # select camel left:
        #     user.extend_camel_left()
        #
        alt1 = cat(
            rule / ":",
            nest(self.indent_size, Line, script),
        )

        # (2): the rule and a single-line talon script on the same line, e.g.,
        #
        # select camel left: user.extend_camel_left()
        #
        if is_short:
            alt2 = self.format_short_command(rule, script)
        else:
            alt2 = Fail

        yield from self.with_comments(alt1 | alt2)

    def format_short_command(self, rule: Doc, script: Doc) -> Doc:
        if isinstance(self.align_short_commands, bool):
            return row(
                rule / ":",
                inline(script),
                table_type="command",
            )
        else:
            return row(
                rule / ":",
                inline(script),
                table_type="command",
                min_col_widths=(self.align_short_commands,),
            )

    ###########################################################################
    # Format: Statements
    ###########################################################################

    @format_lines.register
    def _(self, node: TalonBlock) -> Iterator[Doc]:

        # Used to insert blank lines.
        previous_line: Optional[int] = None

        for child in node.children:
            if (
                self.preserve_blank_lines_in_command
                and previous_line is not None
                and child.start_position.line - previous_line >= 2
            ):
                yield Line

            for line in self.format_lines(child):
                yield from self.with_comments(line)

            # Update previous line.
            previous_line = child.end_position.line

    @format_lines.register
    def _(self, node: TalonAssignmentStatement) -> Iterator[Doc]:
        self.assert_only_comments(node.children)
        yield self.format(node.left) // "=" // self.format(node.right) / Line

    @format_lines.register
    def _(self, node: TalonExpressionStatement) -> Iterator[Doc]:
        self.assert_only_comments(node.children)
        yield self.format(node.expression) / Line

    ###########################################################################
    # Format: Expressions
    ###########################################################################

    @format.register
    def _(self, node: TalonAction) -> Doc:
        self.assert_only_comments(node.children)
        return self.format(node.action_name) / parens(self.format(node.arguments))

    @format.register
    def _(self, node: TalonArgumentList) -> Doc:
        return ("," / Space).join(self.format_children(node.children))

    @format.register
    def _(self, node: TalonUnaryOperator) -> Doc:
        self.assert_only_comments(node.children)
        return self.format(node.operator) / self.format(node.right)

    @format.register
    def _(self, node: TalonBinaryOperator) -> Doc:
        self.assert_only_comments(node.children)
        return (
            self.format(node.left)
            // self.format(node.operator)
            // self.format(node.right)
        )

    @format.register
    def _(self, node: TalonIdentifier) -> Doc:
        return Text.words(node.text, collapse_whitespace=True)

    @format.register
    def _(self, node: TalonKeyAction) -> Doc:
        self.assert_only_comments(node.children)
        return "key" / parens(self.format(node.arguments))

    @format.register
    def _(self, node: TalonOperator) -> Doc:
        return Text.words(node.text, collapse_whitespace=True)

    @format.register
    def _(self, node: TalonParenthesizedExpression) -> Doc:
        return parens(
            self.format(self.get_node(node.children, node_type_name=node.type_name))
        )

    @format.register
    def _(self, node: TalonSleepAction) -> Doc:
        self.assert_only_comments(node.children)
        return "sleep" / parens(self.format(node.arguments))

    @format.register
    def _(self, node: TalonVariable) -> Doc:
        self.assert_only_comments(node.children)
        return self.format(node.variable_name)

    ###########################################################################
    # Format: Numbers
    ###########################################################################

    @format.register
    def _(self, node: TalonFloat) -> Doc:
        return Text.words(node.text.strip(), collapse_whitespace=True)

    @format.register
    def _(self, node: TalonInteger) -> Doc:
        return Text.words(node.text.strip(), collapse_whitespace=True)

    ###########################################################################
    # Format: Strings
    ###########################################################################

    @format.register
    def _(self, node: TalonImplicitString) -> Doc:
        return Text.words(node.text.strip(), collapse_whitespace=True)

    @format.register
    def _(self, node: TalonInterpolation) -> Doc:
        return self.format(self.get_node(node.children, node_type_name=node.type_name))

    @format.register
    def _(self, node: TalonString) -> Doc:
        return smart_quote(self.format_children(node.children))

    @format.register
    def _(self, node: TalonStringContent) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonStringEscapeSequence) -> Doc:
        return Text.words(node.text)

    ###########################################################################
    # Format: Rules
    ###########################################################################

    @format.register
    def _(self, node: TalonCapture) -> Doc:
        self.assert_only_comments(node.children)
        return angles(self.format(node.capture_name))

    @format.register
    def _(self, node: TalonChoice) -> Doc:
        children = self.format_children(node.children)
        operator = Space / "|" / Space
        return operator.join(children)

    @format.register
    def _(self, node: TalonEndAnchor) -> Doc:
        return Text("$")

    @format.register
    def _(self, node: TalonList) -> Doc:
        self.assert_only_comments(node.children)
        return braces(self.format(node.list_name))

    @format.register
    def _(self, node: TalonOptional) -> Doc:
        child = self.get_node(node.children, node_type_name=node.type_name)
        return brackets(self.format(child))

    @format.register
    def _(self, node: TalonParenthesizedRule) -> Doc:
        child = self.get_node(node.children, node_type_name=node.type_name)
        return parens(self.format(child))

    @format.register
    def _(self, node: TalonRepeat) -> Doc:
        child = self.get_node(node.children, node_type_name=node.type_name)
        return self.format(child) / "*"

    @format.register
    def _(self, node: TalonRepeat1) -> Doc:
        return (
            self.format(self.get_node(node.children, node_type_name=node.type_name))
            / "+"
        )

    @format.register
    def _(self, node: TalonRule) -> Doc:
        return cat(self.format_children(node.children))

    @format.register
    def _(self, node: TalonSeq) -> Doc:
        return Space.join(self.format_children(node.children))

    @format.register
    def _(self, node: TalonStartAnchor) -> Doc:
        return Text("^")

    @format.register
    def _(self, node: TalonWord) -> Doc:
        return Text.words(node.text)

    ###########################################################################
    # Format: Comments
    ###########################################################################

    @format.register
    def _(self, node: TalonComment) -> Doc:
        if self.format_comments:
            # TODO: format blocks of comments so we can:
            #       1. decrease indentation consistently;
            #       2. reflow text
            return (
                "#"
                // Text.words(node.text.lstrip("#"), collapse_whitespace=False)
                / Line
            )
        else:
            return Text.words(node.text, collapse_whitespace=False) / Line

    # Used to buffer comments encountered inline, e.g., inside a binary operator
    _match_context_comment_buffer: list[TalonComment] = dataclasses.field(
        default_factory=list, init=False
    )

    def store_comments_with_type(
        self,
        children: Iterable[Union[TalonComment, NodeVar]],
        *,
        node_type: type[NodeVar],
    ) -> Iterator[NodeVar]:
        """
        Store all the comments in the iterable, yield the rest.
        """
        for child in children:
            if isinstance(child, TalonComment):
                self._match_context_comment_buffer.append(child)
            elif isinstance(child, node_type):
                yield child
            else:
                raise TypeError(type(child))

    def get_comments(self) -> Iterator[TalonComment]:
        """
        Get the buffered comments. Clear the buffer.
        """
        try:
            yield from self._match_context_comment_buffer
        finally:
            self._match_context_comment_buffer.clear()

    def with_comments(self, *doclike: DocLike) -> Iterator[Doc]:
        """
        Yield the buffered comments, formatted. Clear the buffer. Then yield the arguments.
        """
        yield from map(self.format, self.get_comments())
        yield from splat(doclike)

    def assert_only_comments(self, children: Iterable[TalonComment]) -> None:
        """
        Assert that all the nodes in the iterable are comments.
        """
        rest = tuple(self.store_comments_with_type(children, node_type=TalonComment))
        assert (
            len(rest) == 0
        ), f"There should be no non-comment nodes, found {tuple(node.type_name for node in rest)}:\n{rest}"

    def get_node(self, children: Iterable[Node], *, node_type_name: str) -> Node:
        """
        Get the single node that is not a comment. Store all the comments.
        """
        return self.get_node_with_type(
            children, node_type=Node, node_type_name=node_type_name
        )

    def get_node_with_type(
        self,
        children: Iterable[Union[NodeVar, TalonComment]],
        *,
        node_type: type[NodeVar],
        node_type_name: str,
    ) -> NodeVar:
        """
        Get the single node that is not a comment, but has type NodeVar. Store all the comments.
        """
        rest = tuple(self.store_comments_with_type(children, node_type=node_type))
        assert (
            len(rest) == 1
        ), f"There should be only one non-comment child in '{node_type_name}', found {tuple(node.type_name for node in rest)}:\n{rest}"
        return next(iter(rest))
