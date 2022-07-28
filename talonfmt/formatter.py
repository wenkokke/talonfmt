from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from functools import singledispatchmethod
from itertools import chain
from typing import Any, Iterable, TypeVar, Union, cast
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

    def format_children(
        self, children: Iterable[Node], store_comments: bool = True
    ) -> Iterator[Doc]:
        if store_comments:
            children = self.store_comments(children)
        for child in children:
            if isinstance(child, Iterable):
                yield from self.format_children(child)
            else:
                yield self.format(child)

    @format.register
    def _(self, node: TalonError) -> Doc:
        raise ValueError(node.start_position, node.end_position)

    # Source File

    @format.register
    def _(self, node: TalonSourceFile) -> Doc:
        docs = self.format_children(node.children, store_comments=False)
        docs_with_tables = create_tables(docs, separator=Line)
        return cat(docs_with_tables)

    def aligned_command(self, *doclike: DocLike, is_one_line: bool) -> Doc:
        if self.align_short_commands and is_one_line:
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

    @format.register
    def _(self, node: TalonCommand) -> Doc:
        rule_doc = self.format(node.rule)
        rule_comments = list(self.comments())
        script_doc = self.format(node.script)
        script_comments = list(self.comments())
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
            is_one_line=len(script_comments) + len(node.script.children) == 1,
        )

        alts = alt1 | alt2
        return cat(rule_comments, alts) if rule_comments else alts

    # Statements

    @format.register
    def _(self, node: TalonBlock) -> Doc:
        docs: list[Doc] = []
        for stmt in node.children:
            doc = self.format(stmt)
            docs.extend(self.comments())
            docs.append(doc)
        return Line.join(docs)

    @format.register
    def _(self, node: TalonAssignment) -> Doc:
        self.only_comment_children(node)
        left = self.format(node.left)
        right = self.format(node.right)
        return Space.join(left, "=", right)

    @format.register
    def _(self, node: TalonDocstring) -> Doc:
        comment = node.text.lstrip().lstrip("#")
        return "###" // Text.words(comment)

    @format.register
    def _(self, node: TalonExpression) -> Doc:
        self.only_comment_children(node)
        expression = self.format(node.expression)
        return expression

    @format.register
    def _(self, node: TalonAction) -> Doc:
        self.only_comment_children(node)
        action_name = self.format(node.action_name)
        arguments = self.format(node.arguments)
        return action_name / parens(arguments)

    # Expressions

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
    def _(self, node: TalonIncludeTag) -> Doc:
        self.only_comment_children(node)
        return "tag():" // self.format(node.tag)

    @format.register
    def _(self, node: TalonInteger) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonInterpolation) -> Doc:
        return self.format(self.get_noncomment_child(node))

    @format.register
    def _(self, node: TalonKeyAction) -> Doc:
        self.only_comment_children(node)
        return "key" / parens(self.format(node.arguments))

    @format.register
    def _(self, node: TalonNumber) -> Doc:
        return self.format(self.get_noncomment_child(node))

    @format.register
    def _(self, node: TalonOperator) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonParenthesizedExpression) -> Doc:
        return parens(self.format(self.get_noncomment_child(node)))

    @format.register
    def _(self, node: TalonRegexEscapeSequence) -> Doc:
        if node.children:
            return braces(self.format_children(node.children))
        else:
            return braces(Empty)

    @format.register
    def _(self, node: TalonSettings) -> Doc:
        return cat(
            "settings():",
            Line,
            Nest(self.indent_size, self.format(self.get_noncomment_child(node))),
        )

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

    # Rules

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
        child = self.get_noncomment_child(node)
        return brackets(self.format(child))

    @format.register
    def _(self, node: TalonParenthesizedRule) -> Doc:
        child = self.get_noncomment_child(node)
        return parens(self.format(child))

    @format.register
    def _(self, node: TalonRepeat) -> Doc:
        child = self.get_noncomment_child(node)
        return self.format(child) / "*"

    @format.register
    def _(self, node: TalonRepeat1) -> Doc:
        return self.format(self.get_noncomment_child(node)) / "+"

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

    # Comments

    _comment_buffer: list[TalonComment] = dataclasses.field(
        default_factory=list, init=False
    )

    def store_comments(self, children: Iterable[Node]) -> Iterator[Node]:
        for child in children:
            if isinstance(child, TalonComment):
                self._comment_buffer.append(child)
            else:
                yield child

    def comments(self) -> Iterator[Doc]:
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

    def get_noncomment_child(self, branch: Branch) -> Node:
        assert branch.children is not None
        if isinstance(branch.children, Sequence):
            rest = tuple(self.store_comments(branch.children))
            assert (
                len(rest) == 1
            ), f"There should be only one non-comment child, found {tuple(node.type_name for node in rest)} in {branch.type_name}:\n{branch}"
            return rest[0]
        else:
            return branch.children

    @format.register
    def _(self, node: TalonComment) -> Doc:
        comment = node.text.lstrip().lstrip("#")
        return "#" // Text.words(comment) / Line

    # Contexts and Matches

    @format.register
    def _(self, node: TalonAnd) -> Doc:
        first_child, *children = self.store_comments(node.children)
        first_doc = self.format(first_child)
        with self.context_and():
            docs = self.format_children(children, store_comments=False)
        return cat(first_doc, docs)

    @format.register
    def _(self, node: TalonContext) -> Doc:
        return cat(self.format_children(node.children, store_comments=False), "-", Line)

    @format.register
    def _(self, node: TalonMatch) -> Doc:
        key = self.format(node.key)
        pattern = self.format(node.pattern)
        kwds = self.context_kwds()
        alt1 = kwds // key / ":" // pattern / Line
        alt2 = self.aligned_match(kwds // key / ":", pattern)
        return alt1 | alt2

    @format.register
    def _(self, node: TalonNot) -> Doc:
        # NOTE: there should only be one non-comment child
        (match,) = list(self.store_comments(node.children))
        with self.context_not():
            return self.format(match)

    @format.register
    def _(self, node: TalonOr) -> Doc:
        docs: list[Doc] = []
        for child in self.store_comments(node.children):
            doc = self.format(child)
            docs.extend(comment / Line for comment in self.comments())
            docs.append(doc)
        return cat(create_tables(iter(docs)))

    _under_and: bool = dataclasses.field(default=False, init=False)

    @contextmanager
    def context_and(self) -> Iterator[None]:
        self._under_and = True
        try:
            yield None
        finally:
            self._under_and = False

    _under_not: bool = dataclasses.field(default=False, init=False)

    @contextmanager
    def context_not(self) -> Iterator[None]:
        self._under_not = True
        try:
            yield None
        finally:
            self._under_not = False

    def context_kwds(self) -> Doc:
        kwds = []
        if self._under_and:
            kwds.append(Text("and"))
        if self._under_not:
            kwds.append(Text("not"))
        return Space.join(kwds)

    def aligned_match(self, *doclike: DocLike) -> Doc:
        if self.align_match_context:
            if self.align_match_context is True:
                return row(*doclike, table_type="match")
            else:
                return row(
                    *doclike,
                    table_type="match",
                    min_col_widths=(self.align_match_context,),
                )
        else:
            return Fail
