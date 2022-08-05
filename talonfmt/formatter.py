import dataclasses
import itertools
from collections.abc import Iterable, Iterator
from functools import singledispatchmethod
from typing import Optional, TypeVar, Union

from doc_printer import (
    Doc,
    DocLike,
    Empty,
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
    TalonAnd,
    TalonArgumentList,
    TalonAssignment,
    TalonBinaryOperator,
    TalonBlock,
    TalonCapture,
    TalonChoice,
    TalonCommand,
    TalonComment,
    TalonContext,
    TalonDocstring,
    TalonEndAnchor,
    TalonError,
    TalonExpression,
    TalonFloat,
    TalonIdentifier,
    TalonImplicitString,
    TalonIncludeTag,
    TalonInteger,
    TalonInterpolation,
    TalonKeyAction,
    TalonList,
    TalonMatch,
    TalonNot,
    TalonNumber,
    TalonOperator,
    TalonOptional,
    TalonOr,
    TalonParenthesizedExpression,
    TalonParenthesizedRule,
    TalonRegexEscapeSequence,
    TalonRepeat,
    TalonRepeat1,
    TalonRule,
    TalonSeq,
    TalonSettings,
    TalonSleepAction,
    TalonSourceFile,
    TalonStartAnchor,
    TalonString,
    TalonStringContent,
    TalonStringEscapeSequence,
    TalonVariable,
    TalonWord,
)

from .parse_error import ParseError

TalonBlockLevelMatch = Union[
    TalonAnd,
    TalonNot,
    TalonMatch,
    TalonOr,
]

TalonBlockLevel = Union[
    TalonSourceFile,
    TalonContext,
    TalonIncludeTag,
    TalonSettings,
    TalonCommand,
    TalonBlock,
    TalonAssignment,
    TalonExpression,
    TalonComment,
    TalonDocstring,
]

NodeVar = TypeVar("NodeVar", bound=Node)


def is_short_command(node: TalonCommand) -> bool:
    return len(node.children) + len(node.script.children) == 1


def block_with_comments(
    comments: Iterable[TalonComment], block: TalonBlock
) -> TalonBlock:
    return TalonBlock(
        text=block.text,
        type_name=block.type_name,
        start_position=block.start_position,
        end_position=block.end_position,
        children=[*comments, *block.children],
    )


@dataclasses.dataclass
class TalonFormatter:
    indent_size: int
    align_match_context: Union[bool, int]
    align_short_commands: Union[bool, int]
    format_comments: bool
    preserve_blank_lines_in_header: bool
    preserve_blank_lines_in_body: bool
    preserve_blank_lines_in_command: bool

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
                TalonContext,
                TalonIncludeTag,
                TalonSettings,
                TalonCommand,
                TalonBlock,
                TalonAssignment,
                TalonExpression,
            ),
        ):
            return cat(self.format_lines(node))
        elif isinstance(node, TalonError):
            raise ParseError(node)
        else:
            raise TypeError(type(node))

    @singledispatchmethod
    def format_lines(self, node: TalonBlockLevel) -> Iterator[Doc]:
        """
        Format any block-level node as a series of lines.
        """
        if isinstance(node, (TalonComment, TalonDocstring)):
            yield self.format(node)
        elif isinstance(node, (TalonAnd, TalonNot, TalonMatch, TalonOr)):
            yield from self.format_lines_match(node, under_and=False, under_not=False)
        elif isinstance(node, TalonError):
            raise ParseError(node)
        else:
            raise TypeError(type(node))

    @singledispatchmethod
    def format_lines_match(
        self,
        match: TalonBlockLevelMatch,
        *,
        under_and: bool,
        under_not: bool,
    ) -> Iterator[Doc]:
        """
        Format any match statement or comment as a series of lines.
        """
        if isinstance(match, TalonError):
            raise ParseError(match)
        else:
            raise TypeError(type(match))

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

        # Used to emit the context header separator.
        in_header: bool = True

        # Used to buffer comments to ensure that they're split correctly
        # between the header and body.
        comment_buffer: list[Doc] = []

        def clear_comment_buffer() -> Iterator[Doc]:
            if comment_buffer:
                yield from comment_buffer
                comment_buffer.clear()

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

        for child in node.children:
            extra_blank_line: bool = child.start_position.row - previous_line >= 2

            if in_header and isinstance(child, TalonComment):
                # NOTE: buffer comments in context header
                if self.preserve_blank_lines_in_body and extra_blank_line:
                    comment_buffer.append(Line)
                comment_buffer.append(self.format(child))
            elif isinstance(child, TalonContext):
                # NOTE: format context header
                assert in_header
                yield from clear_comment_buffer()
                yield from self.format_lines(child)
            else:
                # NOTE: first body-only node, end the context header
                if in_header and isinstance(
                    child, (TalonIncludeTag, TalonSettings, TalonCommand)
                ):
                    yield Text("-") / Line
                    # NOTE: no blank lines after "-"
                    if comment_buffer:
                        yield from itertools.dropwhile(
                            lambda doc: doc is Line, clear_comment_buffer()
                        )
                    else:
                        extra_blank_line = False
                    in_header = False

                if self.align_short_commands is True:
                    if isinstance(child, TalonCommand) and is_short_command(child):
                        # NOTE: buffer short command
                        short_command_buffer.extend(self.format_lines(child))
                    else:
                        # NOTE: long command or other node, clear short command buffer
                        yield from clear_short_command_buffer()
                        if self.preserve_blank_lines_in_body and extra_blank_line:
                            yield Line
                        yield from self.format_lines(child)
                else:
                    if self.preserve_blank_lines_in_body and extra_blank_line:
                        yield Line
                    yield from self.format_lines(child)

            # Update previous line.
            previous_line = child.end_position.row

        # NOTE: no body-only node, end the context header
        if in_header:
            yield Text("-") / Line
            yield from clear_comment_buffer()

        # NOTE: clear remaining short commands in buffer
        if self.align_short_commands is True:
            yield from clear_short_command_buffer()

    ###########################################################################
    # Format: Context Header
    ###########################################################################

    @format_lines.register
    def _(self, node: TalonContext) -> Iterator[Doc]:

        # Used to insert blank lines.
        previous_line: Optional[int] = None

        for child in node.children:
            if (
                self.preserve_blank_lines_in_header
                and previous_line is not None
                and child.start_position.row - previous_line >= 2
            ):
                yield Line

            yield from self.with_comments(self.format_lines(child))

            # Update previous line.
            previous_line = child.end_position.row

    @format_lines_match.register
    def _(self, match: TalonAnd, under_and: bool, under_not: bool) -> Iterator[Doc]:
        for child in match.children:
            if isinstance(child, TalonComment):
                yield from self.format_lines(child)
            else:
                yield from self.format_lines_match(child, under_and, under_not)
                under_and = True

    @format_lines_match.register
    def _(self, match: TalonNot, under_and: bool, under_not: bool) -> Iterator[Doc]:
        for child in match.children:
            if isinstance(child, TalonComment):
                yield from self.format_lines(child)
            else:
                yield from self.format_lines_match(child, under_and, under_not)
                under_not = True

    @format_lines_match.register
    def _(self, match: TalonOr, under_and: bool, under_not: bool) -> Iterator[Doc]:
        for child in match.children:
            if isinstance(child, TalonComment):
                yield from self.format_lines(child)
            else:
                yield from self.with_comments(
                    self.format_lines_match(child, under_and, under_not)
                )

    @format_lines_match.register
    def _(self, match: TalonMatch, under_and: bool, under_not: bool) -> Iterator[Doc]:
        self.assert_only_comments(match.children)
        keywords = self.format_match_keywords(under_and, under_not)
        key = self.format(match.key)
        pattern = self.format(match.pattern)
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

    def format_match_keywords(self, under_and: bool, under_not: bool) -> Iterator[Doc]:
        if under_and:
            yield Text("and")
            yield Space
        if under_not:
            yield Text("not")
            yield Space

    ###########################################################################
    # Format: Tag Includes
    ###########################################################################

    @format_lines.register
    def _(self, node: TalonIncludeTag) -> Iterator[Doc]:
        self.assert_only_comments(node.children)
        yield from self.with_comments("tag():" // self.format(node.tag) / Line)

    ###########################################################################
    # Format: Settings
    ###########################################################################

    @format_lines.register
    def _(self, node: TalonSettings) -> Iterator[Doc]:
        block = self.get_node_with_type(node.children, node_type=TalonBlock)
        block = block_with_comments(self.get_comments(), block)
        yield "settings():" / nest(
            self.indent_size,
            Line,
            self.format(block),
        )

    ###########################################################################
    # Format: Commands
    ###########################################################################

    @format_lines.register
    def _(self, node: TalonCommand) -> Iterator[Doc]:
        rule = self.format(node.rule)

        # Merge comments on this node into the block node.
        block = block_with_comments(node.children, node.script)
        script = self.format(block)

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
        if len(block.children) == 1:
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
                and child.start_position.row - previous_line >= 2
            ):
                yield Line

            for line in self.format_lines(child):
                yield from self.with_comments(line)

            # Update previous line.
            previous_line = child.end_position.row

    @format_lines.register
    def _(self, node: TalonAssignment) -> Iterator[Doc]:
        self.assert_only_comments(node.children)
        yield self.format(node.left) // "=" // self.format(node.right) / Line

    @format_lines.register
    def _(self, node: TalonExpression) -> Iterator[Doc]:
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
        return parens(self.format(self.get_node(node.children)))

    @format.register
    def _(self, node: TalonRegexEscapeSequence) -> Doc:
        if node.children:
            return braces(self.format_children(node.children))
        else:
            return braces(Empty)

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

    @format.register
    def _(self, node: TalonNumber) -> Doc:
        return self.format(self.get_node(node.children))

    ###########################################################################
    # Format: Strings
    ###########################################################################

    @format.register
    def _(self, node: TalonImplicitString) -> Doc:
        return Text.words(node.text.strip(), collapse_whitespace=True)

    @format.register
    def _(self, node: TalonInterpolation) -> Doc:
        return self.format(self.get_node(node.children))

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
        child = self.get_node(node.children)
        return brackets(self.format(child))

    @format.register
    def _(self, node: TalonParenthesizedRule) -> Doc:
        child = self.get_node(node.children)
        return parens(self.format(child))

    @format.register
    def _(self, node: TalonRepeat) -> Doc:
        child = self.get_node(node.children)
        return self.format(child) / "*"

    @format.register
    def _(self, node: TalonRepeat1) -> Doc:
        return self.format(self.get_node(node.children)) / "+"

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

    @format.register
    def _(self, node: TalonDocstring) -> Doc:
        if self.format_comments:
            # TODO: format blocks of comments so we can:
            #       1. decrease indentation consistently;
            #       2. reflow text
            return (
                "###"
                // Text.words(node.text.lstrip("#"), collapse_whitespace=False)
                / Line
            )
        else:
            return Text.words(node.text, collapse_whitespace=False) / Line

    # Used to buffer comments encountered inline, e.g., inside a binary operator
    _comment_buffer: list[TalonComment] = dataclasses.field(
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
                self._comment_buffer.append(child)
            elif isinstance(child, node_type):
                yield child
            else:
                raise TypeError(type(child))

    def get_comments(self) -> Iterator[TalonComment]:
        """
        Get the buffered comments. Clear the buffer.
        """
        try:
            yield from self._comment_buffer
        finally:
            self._comment_buffer.clear()

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

    def get_node(self, children: Iterable[Node]) -> Node:
        """
        Get the single node that is not a comment. Store all the comments.
        """
        return self.get_node_with_type(children, node_type=Node)

    def get_node_with_type(
        self,
        children: Iterable[Union[NodeVar, TalonComment]],
        *,
        node_type: type[NodeVar],
    ) -> NodeVar:
        """
        Get the single node that is not a comment, but has type NodeVar. Store all the comments.
        """
        rest = tuple(self.store_comments_with_type(children, node_type=node_type))
        assert (
            len(rest) == 1
        ), f"There should be only one non-comment child, found {tuple(node.type_name for node in rest)}:\n{rest}"
        return next(iter(rest))
