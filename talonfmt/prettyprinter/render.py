from functools import singledispatchmethod
from itertools import chain

from .doc import *

import typing

Token: typing.TypeAlias = Text
TokenStream: typing.TypeAlias = Iterator[Text]


class RenderError(Exception):
    pass


@dataclass
class CellBuffer:
    tokens: tuple[Token, ...]


@dataclass
class RowBuffer:
    info: RowInfo
    cells: tuple[CellBuffer, ...]


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
        # Calculate the number of columns and rows
        number_of_cols = max(len(row.cols) for row in doc.rows)
        number_of_rows = len(doc.rows)

        # Render cells, and calculate the width of each column
        table_buffer: list[RowBuffer] = []
        cell_widths_per_row: list[tuple[int, ...]] = []
        for row in doc.rows:
            cells: list[CellBuffer] = []
            widths: list[int] = []
            for j in range(0, number_of_cols):
                if j < len(row.cols):
                    tokens = tuple(self.render(row.cols[j]))
                    cells.append(CellBuffer(tokens=tokens))
                    widths.append(sum(map(len, tokens)))
                else:
                    cells.append(CellBuffer(tokens=(Empty,)))
                    widths.append(0)
            table_buffer.append(RowBuffer(info=row.info, cells=tuple(cells)))
            cell_widths_per_row.append(tuple(widths))

        col_widths: list[int] = []
        for n_col in range(0, number_of_cols):
            col_width: int = 0
            for n_row in range(0, number_of_rows):
                col_width = max(col_width, cell_widths_per_row[n_row][n_col])
            col_widths.append(col_width)

        # For each row, iterate over the column buffers,
        # and emit the contents of each cell for that column:
        output_buffer: list[Token] = []
        for n_row, row_buffer in enumerate(table_buffer):
            for n_col, cell_buffer in enumerate(row_buffer.cells):

                # Emit the contents of that cell:
                current_width: int = 0
                for token in cell_buffer.tokens:
                    assert token is not Line
                    current_width += len(token)
                    output_buffer.append(token)
                # Emit padding to up to the required width:
                padding_width = col_widths[n_col] - current_width
                padding = repeat(row_buffer.info.hpad, padding_width)
                output_buffer.extend(padding)
                # Emit the column separator, if required:
                if n_col < number_of_cols - 1:
                    output_buffer.append(row_buffer.info.hsep)
                else:
                    output_buffer.append(Line)
        return iter(output_buffer)

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
