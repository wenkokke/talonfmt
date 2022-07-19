from functools import singledispatchmethod
from io import StringIO
from typing import TypeAlias

from .doc import *

Token: TypeAlias = Text
TokenStream: TypeAlias = Iterator[Text]


@dataclass
class SimpleDocRenderer:
    @singledispatchmethod
    def render(self, doc: Doc) -> TokenStream:
        raise ValueError(doc)

    # def render(self, simple_doc: SimpleDoc) -> str:
    #     buffer = StringIO()
    #     tokens = self.transform(simple_doc)
    #     for token in tokens:
    #         if token is not None:
    #             buffer.write(token)
    #         else:
    #             buffer.write("\n")
    #     return buffer.getvalue()

    # @overrides
    # def transform_Empty(self) -> TokenStream:
    #     pass

    # @overrides
    # def transform_Space(self) -> TokenStream:
    #     yield " "

    # @overrides
    # def transform_Line(self) -> TokenStream:
    #     yield None

    # @overrides
    # def transform_Text(self, text: str) -> TokenStream:
    #     yield text

    # @overrides
    # def transform_Nest(self, indent: int, doc: TokenStream, **rest) -> TokenStream:
    #     leading = " " * indent
    #     has_content: bool = False
    #     line_buffer: list[Token] = []
    #     for token in doc:
    #         if token is not None:
    #             if has_content:
    #                 yield token
    #             else:
    #                 if token.isspace():
    #                     line_buffer.append(token)
    #                 else:
    #                     has_content = True
    #                     yield leading
    #                     yield from line_buffer
    #                     line_buffer.clear()
    #                     yield token
    #         else:
    #             yield from line_buffer
    #             line_buffer.clear()
    #             yield token
    #             has_content = False

    # @overrides
    # def transform_Cat(self, docs: Iterator[TokenStream], **rest) -> TokenStream:
    #     for doc in docs:
    #         yield from doc

    # @overrides
    # def transform_Row(self, cols: Iterator[TokenStream], **rest) -> TokenStream:
    #     pass

    # @overrides
    # def transform_Table(self, rows: Iterator[TokenStream], **rest) -> TokenStream:
    #     pass

    # @overrides
    # def transform_HStretch(self, doc: TokenStream, **rest) -> TokenStream:
    #     yield from doc

    # @overrides
    # def transform_VStretch(self, doc: TokenStream, **rest) -> TokenStream:
    #     yield from doc

    # @overrides
    # def transform_Alt(self, *, docs_hist: tuple[Doc, ...]) -> TokenStream:
    #     yield from self.transform(docs_hist[0])
