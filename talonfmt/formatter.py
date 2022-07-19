from collections.abc import Sequence
from functools import singledispatchmethod
from itertools import chain
from talonfmt.prettyprinter.doc import *
from tree_sitter_talon import *


@dataclass
class TalonFormatter:
    indent_size: int = 4

    @singledispatchmethod
    def format(self, node: Node) -> Doc:
        raise TypeError(type(node))

    def format_list(self, children: Sequence[Node]) -> Iterator[Doc]:
        yield from map(self.format, children)

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
        alt2: Doc
        if len(node.script.children) == 1:
            alt2 = row(cat(rule, ":"), script)
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
        return Text(node.text)

    @format.register
    def _(self, node: TalonIdentifier) -> Doc:
        return Text(node.text)

    @format.register
    def _(self, node: TalonImplicitString) -> Doc:
        return Text.words(node.text)

    @format.register
    def _(self, node: TalonIncludeTag) -> Doc:
        tag = self.format(node.tag)
        return "tag():" // tag

    @format.register
    def _(self, node: TalonInteger) -> Doc:
        return Text(node.text)

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
        return key / ":" // pattern

    @format.register
    def _(self, node: TalonNot) -> Doc:
        children = self.format(node.children)
        return "not" // children

    @format.register
    def _(self, node: TalonNumber) -> Doc:
        children = self.format(node.children)
        return children

    @format.register
    def _(self, node: TalonOperator) -> Doc:
        return Text(node.text)

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
        children = self.format(node.children)
        return children / "*"

    @format.register
    def _(self, node: TalonRepeat1) -> Doc:
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
        children = self.format(node.children)
        return "settings():" / Line / Nest(self.indent_size, children)

    @format.register
    def _(self, node: TalonSleepAction) -> Doc:
        arguments = self.format(node.arguments)
        return "sleep" / parens(arguments)

    @format.register
    def _(self, node: TalonSourceFile) -> Doc:
        children: list[Doc] = []
        table_buffer: list[Row] = []  # Keep all rows
        child_buffer: list[Doc] = []  # Keep other alts
        found_row: bool
        for child in self.format_list(node.children):

            # If child is a row, build a table:
            found_row = False

            if isinstance(child, Row):
                table_buffer.append(child)
                found_row = True

            if isinstance(child, Alt):
                # Traverse the alternatives, looking for a Row.
                # If we find it, we add it to the table_buffer.
                for child_alt in child.alts:
                    if not found_row:
                        if isinstance(child_alt, Row):
                            table_buffer.append(child_alt)
                            found_row = True

            # If we didn't find a row, but there are some rows in the table_buffer,
            # add the table as an alternative layout:
            if not found_row:
                if table_buffer:
                    plain = Line.join(child_buffer)
                    table = Table(tuple(table_buffer))
                    children.append(plain | table)
                    table_buffer.clear()
                    child_buffer.clear()

            # Add the child to the child_buffer as-is:
            child_buffer.append(child)

        return Line.join(children)

    @format.register
    def _(self, node: TalonStartAnchor) -> Doc:
        return Text("^")

    @format.register
    def _(self, node: TalonString) -> Doc:
        children = self.format_list(node.children)
        return quote(children)

    @format.register
    def _(self, node: TalonStringContent) -> Doc:
        return Text(node.text)

    @format.register
    def _(self, node: TalonStringEscapeSequence) -> Doc:
        return Text(node.text)

    @format.register
    def _(self, node: TalonVariable) -> Doc:
        variable_name = self.format(node.variable_name)
        return variable_name

    @format.register
    def _(self, node: TalonWord) -> Doc:
        return Text(node.text)
