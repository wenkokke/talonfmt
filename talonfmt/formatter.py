from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from functools import singledispatchmethod
from itertools import chain
from typing import Union
from doc_printer import *
from tree_sitter_talon import *


@dataclass
class TalonFormatter:
    indent_size: int
    align_match_context: Union[bool, int]
    align_short_commands: Union[bool, int]

    @singledispatchmethod
    def format(self, node: Node) -> Doc:
        raise TypeError(type(node))

    def format_list(self, children: Sequence[Node]) -> Iterator[Doc]:
        for child in children:
            if isinstance(child, Sequence):
                yield from self.format_list(child)
            else:
                yield self.format(child)

    @format.register
    def _(self, node: ERROR) -> Doc:
        raise ValueError(node.start_position, node.end_position)

    @format.register
    def _(self, node: TalonAction) -> Doc:
        action_name = self.format(node.action_name)
        arguments = self.format(node.arguments)
        return action_name / parens(arguments)

    @format.register
    def _(self, node: TalonAnd) -> Doc:
        # TODO: merge "and" into row-like children
        separator = Line / "and" / Space
        children = self.format_list(node.children)
        return separator.join(children)

    @format.register
    def _(self, node: TalonArgumentList) -> Doc:
        separator = "," / Space
        children = self.format_list(node.children)
        return separator.join(children)

    @format.register
    def _(self, node: TalonAssignment) -> Doc:
        left = self.format(node.left)
        right = self.format(node.right)
        return Space.join(left, "=", right)

    @format.register
    def _(self, node: TalonBinaryOperator) -> Doc:
        left = self.format(node.left)
        operator = self.format(node.operator)
        right = self.format(node.right)
        return Space.join(left, operator, right)

    @format.register
    def _(self, node: TalonBlock) -> Doc:
        children = self.format_list(node.children)
        return Line.join(children)

    @format.register
    def _(self, node: TalonCapture) -> Doc:
        capture_name = self.format(node.capture_name)
        return angles(capture_name)

    @format.register
    def _(self, node: TalonChoice) -> Doc:
        operator = Space / "|" / Space
        children = self.format_list(node.children)
        return operator.join(children)

    @format.register
    def _(self, node: TalonCommand) -> Doc:
        rule = self.format(node.rule)
        script = self.format(node.script)
        # (1): a line-break after the rule, e.g.,
        #
        # select camel left:
        #     user.extend_camel_left()
        #
        alt1: Doc
        alt1 = cat(rule, ":", Line, Nest(self.indent_size, script), Line)

        # (2): the rule and a single-line talon script on the same line, e.g.,
        #
        # select camel left: user.extend_camel_left()
        #
        def is_one_line(command: TalonCommand) -> bool:
            if hasattr(command, "script"):
                if hasattr(command.script, "children"):
                    return len(node.script.children) == 1
            return False

        alt2: Doc
        if self.align_short_commands and is_one_line(node):
            if self.align_short_commands is True:
                alt2 = row(cat(rule, ":"), script, table_type="command")
            else:
                alt2 = row(
                    cat(rule, ":"),
                    script,
                    table_type="command",
                    min_col_widths=(self.align_short_commands,),
                )
        else:
            alt2 = Fail

        return alt(alt1, alt2)

    @format.register
    def _(self, node: TalonComment) -> Doc:
        comment = node.text.lstrip().lstrip("#")
        return "#" // Text.words(comment)

    @format.register
    def _(self, node: TalonContext) -> Doc:
        children = self.format_list(node.children)
        return Line.join(chain(children, ("-",)))

    @format.register
    def _(self, node: TalonDocstring) -> Doc:
        comment = node.text.lstrip().lstrip("#")
        return "###" // Text.words(comment)

    @format.register
    def _(self, node: TalonEndAnchor) -> Doc:
        return Text("$")

    @format.register
    def _(self, node: TalonExpression) -> Doc:
        expression = self.format(node.expression)
        return expression

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
        tag = self.format(node.tag)
        return "tag():" // tag

    @format.register
    def _(self, node: TalonInteger) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonInterpolation) -> Doc:
        children = self.format(node.children)
        return children

    @format.register
    def _(self, node: TalonKeyAction) -> Doc:
        arguments = self.format(node.arguments)
        return "key" / parens(arguments)

    @format.register
    def _(self, node: TalonList) -> Doc:
        list_name = self.format(node.list_name)
        return braces(list_name)

    @format.register
    def _(self, node: TalonMatch) -> Doc:
        key = self.format(node.key)
        pattern = self.format(node.pattern)

        alt1 = key / ":" // pattern

        if self.align_match_context:
            if self.align_match_context is True:
                alt2 = row(key / ":", pattern, table_type="match")
            else:
                alt2 = row(
                    key / ":",
                    pattern,
                    table_type="match",
                    min_col_widths=(self.align_match_context,),
                )
        else:
            alt2 = Fail
        return alt1 | alt2

    @format.register
    def _(self, node: TalonNot) -> Doc:
        # TODO: merge "not" into row-like children
        if isinstance(node.children, list):
            separator = Line / "not" / Space
            children = self.format_list(node.children)
            return separator.join(children)
        else:
            child = self.format(node.children)
            return "not" // child

    @format.register
    def _(self, node: TalonNumber) -> Doc:
        children = self.format(node.children)
        return children

    @format.register
    def _(self, node: TalonOperator) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonOptional) -> Doc:
        children = self.format_list(node.children)
        return brackets(Space.join(children))

    @format.register
    def _(self, node: TalonOr) -> Doc:
        children = self.format_list(node.children)
        return Line.join(children)

    @format.register
    def _(self, node: TalonParenthesizedExpression) -> Doc:
        children = self.format(node.children)
        return parens(children)

    @format.register
    def _(self, node: TalonParenthesizedRule) -> Doc:
        children = self.format_list(node.children)
        return parens(Space.join(children))

    @format.register
    def _(self, node: TalonRegexEscapeSequence) -> Doc:
        if node.children:
            children = self.format(node.children)
        else:
            children = Empty
        return braces(children)

    @format.register
    def _(self, node: TalonRepeat) -> Doc:
        if isinstance(node.children, list):
            children = parens(self.format_list(node.children))
        else:
            children = self.format(node.children)
        return children / "*"

    @format.register
    def _(self, node: TalonRepeat1) -> Doc:
        if isinstance(node.children, list):
            children = parens(self.format_list(node.children))
        else:
            children = self.format(node.children)
        return children / "+"

    @format.register
    def _(self, node: TalonRule) -> Doc:
        children = self.format_list(node.children)
        return Space.join(children)

    @format.register
    def _(self, node: TalonSeq) -> Doc:
        children = self.format_list(node.children)
        return Space.join(children)

    @format.register
    def _(self, node: TalonSettings) -> Doc:
        if isinstance(node.children, list):
            children = Line.join(self.format_list(node.children))
        else:
            children = self.format(node.children.children)
        return "settings():" / Line / Nest(self.indent_size, children)

    @format.register
    def _(self, node: TalonSleepAction) -> Doc:
        arguments = self.format(node.arguments)
        return "sleep" / parens(arguments)

    @format.register
    def _(self, node: TalonSourceFile) -> Doc:
        docs = self.format_list(node.children)
        docs_with_tables = create_tables(docs, separator=Line)
        return Line.join(docs_with_tables)

    @format.register
    def _(self, node: TalonStartAnchor) -> Doc:
        return Text("^")

    @format.register
    def _(self, node: TalonString) -> Doc:
        children = self.format_list(node.children)
        return quote(children)

    @format.register
    def _(self, node: TalonStringContent) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonStringEscapeSequence) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonVariable) -> Doc:
        variable_name = self.format(node.variable_name)
        return variable_name

    @format.register
    def _(self, node: TalonWord) -> Doc:
        return Text.words(node.text)
