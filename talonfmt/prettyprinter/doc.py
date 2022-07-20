from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import chain, repeat
from operator import length_hint
from typing import Optional, TypeAlias, Union, cast
from overrides import overrides
from more_itertools import intersperse

import re


DocLike: TypeAlias = Union[str, "Doc", Iterable["DocLike"]]  # type: ignore

DocClassWithUnpack: TypeAlias = type[Iterable["Doc"]]


class Doc(ABC):
    def then(self, other: DocLike) -> "Doc":
        """
        Compose two documents.
        """
        return cat(self, other)

    def join(self, *others: DocLike) -> "Doc":
        """
        Compose a series of documents separated by this document.
        """
        # NOTE: The first 'splat' is to ensure that a separator is
        #       inserted between any two of the top-level Docs, but
        #       not between Docs which are already part of a Cat.
        #       The call to cat then flattens out any existing Cats,
        #       without inserting additional separators.
        return cat(intersperse(self, splat(others)))

    @abstractmethod
    def __length_hint__(self) -> int:
        pass

    def __truediv__(self, other: DocLike) -> "Doc":
        """
        Compose two documents.
        """
        return self.then(other)

    def __rtruediv__(self, other: DocLike) -> "Doc":
        """
        Compose two documents.
        """
        return cat(other).then(self)

    def __floordiv__(self, other: DocLike) -> "Doc":
        """
        Compose two documents, separated by a space.
        """
        return self.then(Space).then(other)

    def __rfloordiv__(self, other: DocLike) -> "Doc":
        """
        Compose two documents, separated by a space.
        """
        return cat(other).then(Space).then(self)

    def __or__(self, other: DocLike) -> "Doc":
        """
        Combine two documents as alternatives.
        """
        return alt(self, other)

    def __ror__(self, other: DocLike) -> "Doc":
        """
        Combine two documents as alternatives.
        """
        return alt(other, self)


@dataclass
class Text(Doc):
    """
    A single line of text.
    """

    text: str

    @staticmethod
    def words(text: str) -> Doc:
        return Space.join(map(Text, text.split()))

    @staticmethod
    def lines(text: str) -> Doc:
        return Line.join(map(Text.words, text.splitlines()))

    @classmethod
    def intern(cls, name: str, text: str) -> "Text":
        if not hasattr(cls, name):
            instance = super().__new__(Text)
            instance.text = text
            setattr(cls, name, instance)
        return getattr(cls, name)

    @classmethod
    def intern_Empty(cls) -> "Text":
        return cls.intern("Empty", "")

    def is_Empty(self) -> bool:
        return self is self.__class__.intern_Empty()

    @classmethod
    def intern_Space(cls) -> "Text":
        return cls.intern("Space", " ")

    def is_Space(self) -> bool:
        return self is self.__class__.intern_Space()

    @classmethod
    def intern_Line(cls) -> "Text":
        return cls.intern("Line", "\n")

    def is_Line(self) -> bool:
        return self is self.__class__.intern_Line()

    def __new__(cls, text: str) -> "Text":
        if text == cls.intern_Empty().text:
            return cls.intern_Empty()
        if text == cls.intern_Space().text:
            return cls.intern_Space()
        if text == cls.intern_Line().text:
            return cls.intern_Line()
        instance = super().__new__(Text)
        instance.text = text
        return instance

    def __init__(self, text: str) -> None:
        # Invariant: The text does not contain whitespace.
        assert (
            re.match(r"\S+", self.text)
            or self.is_Empty()
            or self.is_Space()
            or self.is_Line()
        )

    def __repr__(self) -> str:
        if self.is_Empty():
            return "Empty"
        if self.is_Space():
            return "Space"
        if self.is_Line():
            return "Line"
        return f"Text(text={self.text})"

    @overrides
    def __length_hint__(self) -> int:
        return len(self.text)

    def __len__(self) -> int:
        return len(self.text)


Empty = Text.intern_Empty()

Space = Text.intern_Space()

Line = Text.intern_Line()


@dataclass
class Alt(Doc, Iterable[Doc]):
    """
    Alternatives for the document layout.
    """

    # Assume: The alternatives are listed in increasing order of width.
    alts: tuple[Doc, ...]

    @classmethod
    def intern(cls, name: str, alts: tuple[Doc, ...]) -> "Alt":
        if not hasattr(cls, name):
            instance = super().__new__(Alt)
            instance.alts = alts
            setattr(cls, name, instance)
        return getattr(cls, name)

    @classmethod
    def intern_Fail(cls) -> "Alt":
        return cls.intern("Fail", ())

    def is_Fail(self) -> bool:
        return self is self.__class__.intern_Fail()

    @classmethod
    def intern_SoftLine(cls) -> "Alt":
        return cls.intern("SoftLine", (Line, Empty))

    def is_SoftLine(self) -> bool:
        return self is self.__class__.intern_SoftLine()

    def __new__(cls, alts: tuple[Doc, ...]) -> "Alt":
        if alts == cls.intern_Fail().alts:
            return cls.intern_Fail()
        if alts == cls.intern_SoftLine().alts:
            return cls.intern_SoftLine()
        instance = super().__new__(Alt)
        instance.alts = alts
        return instance

    def __init__(self, alts: tuple[Doc, ...]):
        # Invariant: None of alts is an instance of Alt.
        assert all(not isinstance(doc, Alt) for doc in self.alts)

    def __repr__(self) -> str:
        if self.is_Fail():
            return "Fail"
        if self.is_SoftLine():
            return "SoftLine"
        return f"Alt(alts={self.alts})"

    def __iter__(self) -> Iterator[Doc]:
        return iter(self.alts)

    @overrides
    def __length_hint__(self) -> int:
        if self.alts:
            return length_hint(self.alts[0])
        else:
            return 0


Fail = Alt.intern_Fail()


SoftLine = Alt.intern_SoftLine()


@dataclass
class Cat(Doc, Iterable[Doc]):
    """
    Concatenated documents.
    """

    docs: tuple[Doc, ...]

    def __post_init__(self, **rest) -> None:
        # Invariant: None of docs is an instance of Cat.
        assert all(not isinstance(doc, Cat) for doc in self.docs)
        # Invariant: None of docs is Empty.
        assert all(doc is not Empty for doc in self.docs)

    def __iter__(self) -> Iterator[Doc]:
        return iter(self.docs)

    @overrides
    def __length_hint__(self) -> int:
        return sum(map(length_hint, self.docs))


@dataclass
class RowInfo:
    hpad: Text
    hsep: Text


@dataclass
class Row(Doc, Iterable[Doc]):
    cells: tuple[Doc, ...]
    info: RowInfo

    def __post_init__(self, **rest) -> None:
        # Invariant: None of cells is an instance of Row.
        assert all(not isinstance(cell, Row) for cell in self.cells)
        # Invariant: The hpad text has width 1.
        assert len(self.info.hpad.text) == 1

    def __iter__(self) -> Iterator[Doc]:
        return iter(self.cells)

    @overrides
    def __length_hint__(self) -> int:
        return sum(
            intersperse(length_hint(self.info.hsep), map(length_hint, self.cells))
        )


@dataclass
class Table(Doc, Iterable[Row]):
    rows: tuple[Row, ...]

    def __post_init__(self, **rest) -> None:
        # Invariant: All of rows are an instance of Table.
        assert all(isinstance(row, Row) for row in self.rows)

    def __iter__(self) -> Iterator[Row]:
        return iter(self.rows)

    @overrides
    def __length_hint__(self) -> int:
        return max(map(length_hint, self.rows))


@dataclass
class Nest(Doc):
    """
    Indented documents.

    Note:
        The Nest constructor cannot guarantee that the indent is positive,
        so it is better to call the Doc.nest function.
    """

    indent: int
    doc: Doc

    def __init__(self, indent: int, doc: Doc) -> None:
        if isinstance(doc, Nest):
            self.indent = indent + doc.indent
            self.doc = doc.doc
        else:
            self.indent = indent
            self.doc = doc

        # Invariant: The doc is not Nest
        assert not isinstance(self.doc, Nest)
        # Invariant: The indent is greater than zero.
        assert self.indent > 0

    @overrides
    def __length_hint__(self) -> int:
        return self.indent + length_hint(self.doc)


def splat(
    doclike: DocLike,
    unpack: DocClassWithUnpack | tuple[DocClassWithUnpack, ...] = (),
) -> Iterator["Doc"]:
    """
    Iterate over the elements any document-like object.
    """
    if not isinstance(unpack, tuple):
        unpack = (unpack,)
    if isinstance(doclike, str):
        yield from splat(Text.lines(doclike), unpack=unpack)
    elif isinstance(doclike, Doc):
        if isinstance(doclike, unpack):
            yield from cast(Iterable["Doc"], doclike)
        else:
            yield doclike
    else:
        for smaller_doclike in doclike:
            yield from splat(smaller_doclike, unpack=unpack)


def cat(*doclike: DocLike) -> "Doc":
    return Cat(tuple(splat(doclike, unpack=Cat)))


def row(
    *doclike: DocLike,
    hpad: str | Text = Space,
    hsep: str | Text = Space,
) -> "Doc":
    # Ensure padding and separators are Text
    if isinstance(hpad, str):
        hpad = Text(hpad)
    if isinstance(hsep, str):
        hsep = Text(hsep)
    info = RowInfo(hpad=hpad, hsep=hsep)
    # Ensure Row settings are preserved
    cells: list[Doc] = []
    for cell_or_row in splat(doclike):
        if isinstance(cell_or_row, Row):
            assert cell_or_row.info == info
            cells.extend(cell_or_row.cells)
        else:
            cells.append(cell_or_row)
    return Row(tuple(cells), info=info)


def table(rows: Iterator[Row]) -> Doc:
    return Table(tuple(rows))


def alt(*doclike: DocLike) -> Doc:
    alts = tuple(splat(doclike, unpack=Alt))
    if len(alts) == 1:
        return alts[0]
    else:
        return Alt(alts)


def parens(*doclike: DocLike) -> Doc:
    return cat("(", doclike, ")")


def brackets(*doclike: DocLike) -> Doc:
    return cat("[", doclike, "]")


def braces(*doclike: DocLike) -> Doc:
    return cat("{", doclike, "}")


def angles(*doclike: DocLike) -> Doc:
    return cat("<", doclike, ">")


def quote(*doclike: DocLike) -> Doc:
    return cat('"', doclike, '"')
