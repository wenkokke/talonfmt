from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from functools import reduce, singledispatchmethod
from itertools import chain, repeat
import operator
from typing import Any, Iterable, NewType, Optional, TypeVar, Union, cast
from doc_printer import *
from tree_sitter_talon import *

import dataclasses


class FormatError(Exception):
    pass


@dataclasses.dataclass
class TalonFormatter:
    indent_size: int
    align_match_context: Union[bool, int]
    align_short_commands: Union[bool, int]

    @singledispatchmethod
    def format(self, node: Node) -> Doc:
        raise TypeError(type(node))

    def format_children(self, children: Iterable[Node]) -> Iterator[Doc]:
        for child in self.store_comments(children):
            if isinstance(child, Iterable):
                yield from self.format_children(child)
            else:
                yield self.format(child)

    @format.register
    def _(self, node: TalonError) -> Doc:
        raise ValueError(node.start_position, node.end_position)

    ###########################################################################
    # Documents
    ###########################################################################

    @format.register
    def _(self, node: TalonSourceFile) -> Doc:
        header: list[Doc] = []
        body: list[Doc] = []
        for child in self.store_comments(node.children):
            if isinstance(child, TalonContext):
                header.extend(self.get_comments())
                context = self.format(child)
                if context:
                    header.append(context)
            else:
                body.extend(self.get_comments())
                body.append(self.format(child))
        body_with_tables = create_tables(iter(body))
        return Line.join(header, "-", body_with_tables)

    ###########################################################################
    # Tag Includes
    ###########################################################################

    @format.register
    def _(self, node: TalonIncludeTag) -> Doc:
        # NOTE: top-level constructs should not include a trailing newline
        self.only_comment_children(node)
        include_tag = "tag():" // self.format(node.tag)
        return Line.join(self.get_comments(), include_tag)

    ###########################################################################
    # Settings
    ###########################################################################

    @format.register
    def _(self, node: TalonSettings) -> Doc:
        # NOTE: top-level constructs should not include a trailing newline
        settings = (
            "settings():"
            / Line
            / Nest(self.indent_size, self.format(self.get_only_child(node)))
        )
        return Line.join(self.get_comments(), settings)

    ###########################################################################
    # Commands
    ###########################################################################

    @format.register
    def _(self, node: TalonCommand) -> Doc:
        # NOTE: top-level constructs should not include a trailing newline

        rule_doc = self.format(node.rule)
        rule_comments = list(self.get_comments())
        script_doc = self.format(node.script)
        script_comments = list(self.get_comments())
        # (1): a line-break after the rule, e.g.,
        #
        # select camel left:
        #     user.extend_camel_left()
        #
        alt1 = Line.join(
            rule_doc / ":",
            Nest(
                self.indent_size,
                Line.join(script_comments, script_doc),
            ),
        )

        # (2): the rule and a single-line talon script on the same line, e.g.,
        #
        # select camel left: user.extend_camel_left()
        #
        alt2 = self.aligned_command(
            rule_doc / ":",
            Line.join(script_comments, script_doc),
            multiline=len(script_comments) + len(node.script.children) > 1,
        )

        alts = alt1 | alt2
        return Line.join(rule_comments, alts) if rule_comments else alts

    def aligned_command(self, *doclike: DocLike, multiline: bool) -> Doc:
        if self.align_short_commands and not multiline:
            if self.align_short_commands is True:
                return row(*doclike, table_type="command")
            else:
                return row(
                    *doclike,
                    table_type="command",
                    min_col_widths=(self.align_short_commands,),
                )
        else:
            return Fail

    ###########################################################################
    # Statements and Blocks
    ###########################################################################

    @format.register
    def _(self, node: TalonBlock) -> Doc:
        docs: list[Doc] = []
        for stmt in node.children:
            doc = self.format(stmt)
            docs.extend(self.get_comments())
            docs.append(doc)
        return Line.join(docs)

    @format.register
    def _(self, node: TalonAssignment) -> Doc:
        self.only_comment_children(node)
        left = self.format(node.left)
        right = self.format(node.right)
        return Space.join(left, "=", right)

    @format.register
    def _(self, node: TalonComment) -> Doc:
        comment = node.text.strip().lstrip("#").lstrip()
        return "#" // Text.words(comment)

    @format.register
    def _(self, node: TalonDocstring) -> Doc:
        comment = node.text.strip().lstrip("#").lstrip()
        return "###" // Text.words(comment)

    @format.register
    def _(self, node: TalonExpression) -> Doc:
        self.only_comment_children(node)
        expression = self.format(node.expression)
        return expression

    ###########################################################################
    # Expressions
    ###########################################################################

    @format.register
    def _(self, node: TalonAction) -> Doc:
        self.only_comment_children(node)
        action_name = self.format(node.action_name)
        arguments = self.format(node.arguments)
        return action_name / parens(arguments)

    @format.register
    def _(self, node: TalonArgumentList) -> Doc:
        separator = "," / Space
        children = self.format_children(node.children)
        return separator.join(children)

    @format.register
    def _(self, node: TalonBinaryOperator) -> Doc:
        self.only_comment_children(node)
        left = self.format(node.left)
        operator = self.format(node.operator)
        right = self.format(node.right)
        return Space.join(left, operator, right)

    @format.register
    def _(self, node: TalonFloat) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonIdentifier) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonImplicitString) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonInteger) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonInterpolation) -> Doc:
        return self.format(self.get_only_child(node))

    @format.register
    def _(self, node: TalonKeyAction) -> Doc:
        self.only_comment_children(node)
        return "key" / parens(self.format(node.arguments))

    @format.register
    def _(self, node: TalonNumber) -> Doc:
        return self.format(self.get_only_child(node))

    @format.register
    def _(self, node: TalonOperator) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonParenthesizedExpression) -> Doc:
        return parens(self.format(self.get_only_child(node)))

    @format.register
    def _(self, node: TalonRegexEscapeSequence) -> Doc:
        if node.children:
            return braces(self.format_children(node.children))
        else:
            return braces(Empty)

    @format.register
    def _(self, node: TalonSleepAction) -> Doc:
        self.only_comment_children(node)
        return "sleep" / parens(self.format(node.arguments))

    @format.register
    def _(self, node: TalonString) -> Doc:
        return quote(self.format_children(node.children))

    @format.register
    def _(self, node: TalonStringContent) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonStringEscapeSequence) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonVariable) -> Doc:
        self.only_comment_children(node)
        return self.format(node.variable_name)

    ###########################################################################
    # Rules
    ###########################################################################

    @format.register
    def _(self, node: TalonCapture) -> Doc:
        self.only_comment_children(node)
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
        self.only_comment_children(node)
        return braces(self.format(node.list_name))

    @format.register
    def _(self, node: TalonOptional) -> Doc:
        child = self.get_only_child(node)
        return brackets(self.format(child))

    @format.register
    def _(self, node: TalonParenthesizedRule) -> Doc:
        child = self.get_only_child(node)
        return parens(self.format(child))

    @format.register
    def _(self, node: TalonRepeat) -> Doc:
        child = self.get_only_child(node)
        return self.format(child) / "*"

    @format.register
    def _(self, node: TalonRepeat1) -> Doc:
        return self.format(self.get_only_child(node)) / "+"

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
    # Comments
    ###########################################################################

    # Used to buffer comments encountered inline, e.g., inside a binary operator
    _comment_buffer: list[TalonComment] = dataclasses.field(
        default_factory=list, init=False
    )

    def store_comments(self, children: Iterable[Node]) -> Iterator[Node]:
        for child in children:
            if isinstance(child, TalonComment):
                self._comment_buffer.append(child)
            else:
                yield child

    def get_comments(self) -> Iterator[Doc]:
        try:
            for comment in self._comment_buffer:
                yield self.format(comment)
        finally:
            self._comment_buffer.clear()

    def only_comment_children(self, branch: Branch) -> None:
        if isinstance(branch.children, list):
            rest = tuple(self.store_comments(branch.children))
            assert (
                len(rest) == 0
            ), f"There should be no non-comment children, found {tuple(node.type_name for node in rest)} in {branch.type_name}:\n{branch}"

    def get_only_child(self, branch: Branch) -> Node:
        assert branch.children is not None
        if isinstance(branch.children, Sequence):
            rest = tuple(self.store_comments(branch.children))
            assert (
                len(rest) == 1
            ), f"There should be only one non-comment child, found {tuple(node.type_name for node in rest)} in {branch.type_name}:\n{branch}"
            return rest[0]
        else:
            return branch.children

    ###########################################################################
    # Context Header
    ###########################################################################

    @format.register
    def _(self, node: TalonContext) -> Doc:
        docstrings: list[Doc] = []
        buffer: list[Doc] = []
        for child in node.children:
            if isinstance(child, TalonDocstring):
                docstrings.append(self.format(child))
            elif isinstance(child, TalonComment):
                buffer.append(self.format(child))
            else:
                buffer.extend(self.format_matches(child, False, False))
        if not docstrings and not buffer:
            return Empty
        else:
            return Line.join(docstrings, buffer)

    @singledispatchmethod
    def format_matches(
        self,
        match: Union[TalonAnd, TalonNot, TalonMatch, TalonOr],
        *,
        under_and: bool,
        under_not: bool,
    ) -> Iterator[Doc]:
        raise TypeError(type(match))

    @format_matches.register
    def _(self, match: TalonAnd, under_and: bool, under_not: bool) -> Iterator[Doc]:
        for child in match.children:
            if isinstance(child, TalonComment):
                yield self.format(child)
            else:
                yield from self.format_matches(child, under_and, under_not)
                under_and = True

    @format_matches.register
    def _(self, match: TalonNot, under_and: bool, under_not: bool) -> Iterator[Doc]:
        for child in match.children:
            if isinstance(child, TalonComment):
                yield self.format(child)
            else:
                yield from self.format_matches(child, under_and, under_not)
                under_not = True

    @format_matches.register
    def _(self, match: TalonOr, under_and: bool, under_not: bool) -> Iterator[Doc]:
        for child in match.children:
            if isinstance(child, TalonComment):
                yield self.format(child)
            else:
                yield from self.format_matches(child, under_and, under_not)

    @format_matches.register
    def _(self, match: TalonMatch, under_and: bool, under_not: bool) -> Iterator[Doc]:
        kwds = self.match_keywords(under_and, under_not)
        key = cat(kwds, self.format(match.key), ":")
        pattern = self.format(match.pattern)
        yield alt(self.create_match_alts(key, pattern))

    def match_keywords(self, under_and: bool, under_not: bool) -> Iterator[Doc]:
        if under_and:
            yield Text("and")
            yield Space
        if under_not:
            yield Text("not")
            yield Space

    def create_match_alts(self, *doclike: DocLike) -> Iterator[Doc]:
        # Standard
        yield Space.join(doclike)

        # Aligned alternative
        if self.align_match_context:
            if self.align_match_context is True:
                yield row(*doclike, table_type="match")
            else:
                yield row(
                    *doclike,
                    table_type="match",
                    min_col_widths=(self.align_match_context,),
                )
