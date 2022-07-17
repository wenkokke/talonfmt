from itertools import chain
from talon_fmt.prettyprinter.doc import *
from tree_sitter_talon import Node as Node, Point as Point, NodeTransformer
from typing import Dict, Generic, Sequence, Union

import tree_sitter_talon as talon


@dataclass
class TalonFormatter(NodeTransformer[Doc]):
    indent_size: int = 4

    @overrides
    def transform_Action(
        self,
        *,
        action_name: Doc,
        arguments: Doc,
        **rest,
    ) -> Doc:
        return action_name / parens(arguments)

    @overrides
    def transform_And(
        self,
        *,
        children: Sequence[Doc],
        **rest,
    ) -> Doc:
        separator = Line / "and" / Space
        return separator.join(children)

    @overrides
    def transform_ArgumentList(
        self,
        *,
        children: Sequence[Doc],
        **rest,
    ) -> Doc:
        separator = "," / Space
        return parens(separator.join(children))

    @overrides
    def transform_Assignment(
        self,
        *,
        left: Doc,
        right: Doc,
        **rest,
    ) -> Doc:
        return Space.join((left, "=", right))

    @overrides
    def transform_BinaryOperator(
        self,
        *,
        left: Doc,
        operator: Doc,
        right: Doc,
        **rest,
    ) -> Doc:
        return Space.join((left, operator, right))

    @overrides
    def transform_Block(
        self,
        *,
        children: Sequence[Doc],
        **rest,
    ) -> Doc:
        return Line.join(children)

    @overrides
    def transform_Capture(
        self,
        *,
        capture_name: Doc,
        **rest,
    ) -> Doc:
        return angles(capture_name)

    @overrides
    def transform_Choice(
        self,
        *,
        children: Sequence[Doc],
        **rest,
    ) -> Doc:
        operator = Space / "|" / Space
        return operator.join(children)

    @overrides
    def transform_Command(
        self,
        *,
        rule: Doc,
        script: Doc,
        **rest,
    ) -> Doc:
        return rule / ":" / Line / script.nest(self.indent_size)

    @overrides
    def transform_Comment(
        self,
        *,
        text: str,
        **rest,
    ) -> Doc:
        return VStretch("#") & text

    @overrides
    def transform_Context(
        self,
        *,
        children: Sequence[Doc],
        **rest,
    ) -> Doc:
        return Line.join(chain(children, ("-",)))

    @overrides
    def transform_Docstring(
        self,
        *,
        text: str,
        **rest,
    ) -> Doc:
        return VStretch("###") & text

    @overrides
    def transform_ERROR(
        self,
        *,
        start_position: Point,
        end_position: Point,
        **rest,
    ) -> Doc:
        raise ValueError(start_position, end_position)

    @overrides
    def transform_EndAnchor(
        self,
        **rest,
    ) -> Doc:
        return Text("$")

    @overrides
    def transform_Expression(
        self,
        *,
        expression: Doc,
        **rest,
    ) -> Doc:
        return expression

    @overrides
    def transform_Float(
        self,
        *,
        text: str,
        **rest,
    ) -> Doc:
        return Text(text)

    @overrides
    def transform_Identifier(
        self,
        *,
        text: str,
        **rest,
    ) -> Doc:
        return Text(text)

    @overrides
    def transform_ImplicitString(
        self,
        *,
        text: str,
        **rest,
    ) -> Doc:
        return Text(text)

    @overrides
    def transform_IncludeTag(
        self,
        *,
        tag: Doc,
        **rest,
    ) -> Doc:
        return "tag():" // tag

    @overrides
    def transform_Integer(
        self,
        *,
        text: str,
        **rest,
    ) -> Doc:
        return Text(text)

    @overrides
    def transform_Interpolation(
        self,
        *,
        children: Doc,
        **rest,
    ) -> Doc:
        return children

    @overrides
    def transform_KeyAction(
        self,
        *,
        arguments: Doc,
        **rest,
    ) -> Doc:
        return "key" / parens(arguments)

    @overrides
    def transform_List(
        self,
        *,
        list_name: Doc,
        **rest,
    ) -> Doc:
        return braces(list_name)

    @overrides
    def transform_Match(
        self,
        *,
        key: Doc,
        pattern: Doc,
        **rest,
    ) -> Doc:
        return key / ":" // pattern

    @overrides
    def transform_Not(
        self,
        *,
        children: Doc,
        **rest,
    ) -> Doc:
        return "not" // children

    @overrides
    def transform_Number(
        self,
        *,
        children: Doc,
        **rest,
    ) -> Doc:
        return children

    @overrides
    def transform_Operator(
        self,
        *,
        text: str,
        **rest,
    ) -> Doc:
        return Text(text)

    @overrides
    def transform_Optional(
        self,
        *,
        children: Sequence[Doc],
        **rest,
    ) -> Doc:
        return brackets(Space.join(children))

    @overrides
    def transform_Or(
        self,
        *,
        children: Sequence[Doc],
        **rest,
    ) -> Doc:
        return Line.join(children)

    @overrides
    def transform_ParenthesizedExpression(
        self,
        *,
        children: Doc,
        **rest,
    ) -> Doc:
        return parens(children)

    @overrides
    def transform_ParenthesizedRule(
        self,
        *,
        children: Sequence[Doc],
        **rest,
    ) -> Doc:
        return parens(Space.join(children))

    @overrides
    def transform_RegexEscapeSequence(
        self,
        *,
        children: Doc,
        **rest,
    ) -> Doc:
        return braces(children)

    @overrides
    def transform_Repeat(
        self,
        *,
        children: Doc,
        **rest,
    ) -> Doc:
        return children / "*"

    @overrides
    def transform_Repeat1(
        self,
        *,
        children: Doc,
        **rest,
    ) -> Doc:
        return children / "+"

    @overrides
    def transform_Rule(
        self,
        *,
        children: Sequence[Doc],
        **rest,
    ) -> Doc:
        return Space.join(children)

    @overrides
    def transform_Seq(
        self,
        *,
        children: Sequence[Doc],
        **rest,
    ) -> Doc:
        return Space.join(children)

    @overrides
    def transform_Settings(
        self,
        *,
        children: Doc,
        **rest,
    ) -> Doc:
        return "settings():" / Line / children.nest(self.indent_size)

    @overrides
    def transform_SleepAction(
        self,
        *,
        arguments: Doc,
        **rest,
    ) -> Doc:
        return "sleep" / parens(arguments)

    @overrides
    def transform_SourceFile(
        self,
        *,
        children: Sequence[Doc],
        **rest,
    ) -> Doc:
        return Line.join(children)

    @overrides
    def transform_StartAnchor(
        self,
        **rest,
    ) -> Doc:
        return Text("^")

    @overrides
    def transform_String(
        self,
        *,
        children: Sequence[Doc],
        **rest,
    ) -> Doc:
        return between('"', children, '"')

    @overrides
    def transform_StringContent(
        self,
        *,
        text: str,
        **rest,
    ) -> Doc:
        return Text(text)

    @overrides
    def transform_StringEscapeSequence(
        self,
        *,
        text: str,
        **rest,
    ) -> Doc:
        return Text(text)

    @overrides
    def transform_Variable(
        self,
        *,
        variable_name: Doc,
        **rest,
    ) -> Doc:
        return variable_name

    @overrides
    def transform_Word(
        self,
        *,
        text: str,
        **rest,
    ) -> Doc:
        return Text(text)
