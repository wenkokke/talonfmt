from dataclasses import field
from functools import cache, singledispatchmethod
from itertools import chain
import operator

from .doc import *

import typing


class RenderError(Exception):
    pass


Token: typing.TypeAlias = Text
TokenStream: typing.TypeAlias = Iterator[Token]
TokenBuffer: typing.TypeAlias = list[Token]


@dataclass
class CellBuffer:
    min_width: int = 0
    buffer: TokenBuffer = field(default_factory=list)


@dataclass
class RowBuffer:
    info: RowInfo
    buffer: list[CellBuffer] = field(default_factory=list)


@dataclass
class TableBuffer:
    buffer: list[RowBuffer] = field(default_factory=list)

    def col_width(self, j: int) -> int:
        return max(row_buffer.buffer[j].min_width for row_buffer in self.buffer)


@dataclass
class SimpleDocRenderer:
    def to_str(self, doc: Doc) -> str:
        return "".join(token.text for token in self.render(doc))

    @singledispatchmethod
    def render(self, doc: Doc) -> TokenStream:
        raise TypeError(type(doc))

    def render_stream(self, docs: Iterator[Doc]) -> TokenStream:
        for token_stream in map(self.render, docs):
            yield from token_stream

    @render.register
    def _(self, doc: Text) -> TokenStream:
        yield doc

    @render.register
    def _(self, doc: Alt) -> TokenStream:
        if doc.alts:
            yield from self.render(doc.alts[0])
        else:
            return RenderError(doc)

    @render.register
    def _(self, doc: Cat) -> TokenStream:
        yield from self.render_stream(iter(doc.docs))

    @render.register
    def _(self, doc: Row) -> TokenStream:
        n_cols = len(doc.cells)
        for j in range(0, n_cols):
            yield from self.render(doc.cells[j])
            if j < n_cols - 1:
                yield doc.info.hsep
            else:
                yield Line

    @render.register
    def _(self, doc: Table) -> TokenStream:
        n_rows = len(doc.rows)
        n_cols = max(len(row.cells) for row in doc.rows)

        table_buffer = TableBuffer()
        for i in range(0, n_rows):
            row = doc.rows[i]
            row_buffer = RowBuffer(row.info)
            for j in range(0, n_cols):
                cell = row.cells[j]
                cell_buffer = CellBuffer()
                for token in self.render(cell):
                    cell_buffer.min_width += len(token)
                    cell_buffer.buffer.append(token)
                row_buffer.buffer.append(cell_buffer)
            table_buffer.buffer.append(row_buffer)

        buffer: TokenBuffer = []
        for i in range(0, n_rows):
            info = table_buffer.buffer[i].info
            for j in range(0, n_cols):
                cell_buffer = table_buffer.buffer[i].buffer[j]
                yield from cell_buffer.buffer
                yield from repeat(
                    info.hpad, table_buffer.col_width(j) - cell_buffer.min_width
                )
                if j < n_cols - 1:
                    yield info.hsep
                else:
                    yield Line

    @render.register
    def _(self, doc: Nest) -> TokenStream:
        has_content: bool = False
        line_indent: int = 0
        for token in self.render(doc.doc):
            if token is Line:
                has_content = False
                yield Line
            else:
                if has_content:
                    yield token
                else:
                    if token is Space:
                        line_indent += 1
                    else:
                        has_content = True
                        yield from repeat(Space, line_indent + doc.indent)
                        yield token
