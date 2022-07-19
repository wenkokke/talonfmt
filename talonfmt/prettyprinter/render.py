from functools import singledispatchmethod
from itertools import chain

from .doc import *

import typing

Token: typing.TypeAlias = Text
TokenStream: typing.TypeAlias = Iterator[Text]


class RenderError(Exception):
    pass


T = typing.TypeVar("T")


@dataclass
class SimpleDocRenderer:
    @singledispatchmethod
    def render(self, doc: Doc) -> TokenStream:
        raise TypeError(type(doc))

    @render.register
    def _(self, doc: Text) -> TokenStream:
        return iter([doc])

    @render.register
    def _(self, doc: Alt) -> TokenStream:
        if doc.alts:
            return self.render(doc.alts[0])
        else:
            raise RenderError(doc)

    @render.register
    def _(self, doc: Cat) -> TokenStream:
        return chain.from_iterable(self.render(subdoc) for subdoc in doc.docs)

    @render.register
    def _(self, doc: Row) -> TokenStream:
        # Calculate the number of columns
        number_of_cols = len(doc.cols)

        token_buffer: list[Token] = []

        # Emit the contents of each cell:
        for j, cell in enumerate(doc.cols):
            token_buffer.extend(self.render(cell))

            # Emit the column separator, if required:
            if j < number_of_cols - 1:
                token_buffer.append(doc.info.hsep)

        return iter(token_buffer)

    @render.register
    def _(self, doc: Table) -> TokenStream:
        # Calculate the number of columns
        number_of_cols = max(len(row.cols) for row in doc.rows)

        # Render cells, and calculate the width of each column
        table: list[list[tuple[RowInfo, tuple[Token, ...]]]] = []
        col_width: list[int] = []
        for i, row in enumerate(doc.rows):
            table[i] = []
            col_width[i] = 0
            for j in range(0, number_of_cols):
                if j < len(row.cols):
                    col_tokens = tuple(self.render(row.cols[j]))
                    table[i][j] = (row.info, col_tokens)
                    col_width[i] = max(col_width[i], sum(map(length_hint, col_tokens)))
                else:
                    table[i][j] = (row.info, (Empty,))

        # For each row and each cell:
        token_buffer: list[Token] = []
        for i in range(0, len(table)):
            for j in range(0, number_of_cols):
                info, cell, = table[
                    i
                ][j]
                # Emit the contents of that cell:
                cell_width: int = 0
                for token in cell:
                    assert token is not Line
                    cell_width += len(token)
                    token_buffer.append(token)
                # Emit padding to up to the required width:
                token_buffer.extend(repeat(info.hpad, col_width[j] - cell_width))
                # Emit the column separator, if required:
                if j < number_of_cols - 1:
                    token_buffer.append(info.hsep)
        return iter(token_buffer)

    @render.register
    def _(self, doc: Nest) -> TokenStream:
        has_content: bool = False
        line_indent: int = 0
        token_buffer: list[Token] = []
        for token in self.render(doc.doc):
            if token is Line:
                has_content = False
                token_buffer.append(Line)
            else:
                if has_content:
                    token_buffer.append(token)
                else:
                    if token is Space:
                        line_indent += 1
                    else:
                        has_content = True
                        token_buffer.extend(repeat(Space, line_indent + doc.indent))
                        token_buffer.append(token)
        return iter(token_buffer)
