from abc import ABC
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import chain, repeat
from typing import Optional, TypeAlias, Union, cast
from overrides import overrides
from more_itertools import intersperse

import re


DocLike: TypeAlias = Union[str, "Doc", Iterable["DocLike"]]  # type: ignore

DocClassWithUnpack: TypeAlias = type[Iterable["Doc"]]


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


def cat(*doclike: DocLike) -> "Cat":
    return Cat(tuple(splat(doclike, unpack=Cat)))


def row(*doclike: DocLike) -> "Row":
    return Row(tuple(splat(doclike, unpack=Row)))


def alt(*doclike: DocLike) -> "Alt":
    return Alt(tuple(splat(doclike, unpack=Alt)))


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

    def __and__(self, other: DocLike) -> "Row":
        """
        Compose two documents, as columns in a row.
        """
        return row(self, other)

    def __rand__(self, other: DocLike) -> "Row":
        """
        Compose two documents, as columns in a row.
        """
        return row(other, self)

    def __or__(self, other: DocLike) -> "Alt":
        """
        Combine two documents as alternatives.
        """
        return alt(self, other)

    def __ror__(self, other: DocLike) -> "Alt":
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

    def __new__(cls, text: str) -> "Text":
        if text == "":
            return cls.intern("Empty", "")
        if text == " ":
            return cls.intern("Space", " ")
        if text == "\n":
            return cls.intern("Line", "\n")
        instance = super().__new__(Text)
        instance.text = text
        return instance

    def __init__(self, text: str) -> None:
        # Invariant: The text does not contain whitespace.
        assert (
            re.match(r"\S+", self.text)
            or self is getattr(self, "Empty", None)
            or self is getattr(self, "Space", None)
            or self is getattr(self, "Line", None)
        )

    def __repr__(self) -> str:
        if self is getattr(self, "Empty", None):
            return "Empty"
        if self is getattr(self, "Space", None):
            return "Space"
        if self is getattr(self, "Line", None):
            return "Line"
        return f"Text(text={self.text})"

    def __mul__(self, times: int) -> Doc:
        return cat(repeat(self, times))

    def __rmul__(self, times: int) -> Doc:
        return cat(repeat(self, times))


@dataclass
class HStretch(Doc):
    doc: Doc


@dataclass
class VStretch(Doc):
    doc: Doc


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


@dataclass
class Alt(Doc, Iterable[Doc]):
    """
    Alternatives for the document layout.
    """

    # Assume: The alternatives are listed in increasing order of width.
    docs: tuple[Doc, ...]

    def __post_init__(self, **rest):
        # Invariant: None of docs is an instance of Alt.
        assert all(not isinstance(doc, Alt) for doc in self.docs)

    def __iter__(self) -> Iterator[Doc]:
        return iter(self.docs)


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


@dataclass
class Row(Doc, Iterable[Doc]):
    cols: tuple[Doc, ...]

    def __post_init__(self, **rest) -> None:
        # Invariant: None of cols is an instance of Row.
        assert all(not isinstance(col, Row) for col in self.cols)

    def __iter__(self) -> Iterator[Doc]:
        return iter(self.cols)


@dataclass
class Table(Doc, Iterable[Row]):
    rows: tuple[Row, ...]

    def __post_init__(self, **rest) -> None:
        # Invariant: All of rows are an instance of Table.
        assert all(isinstance(row, Row) for row in self.rows)

    def __iter__(self) -> Iterator[Row]:
        return iter(self.rows)


Empty = Text("")

Line = Text("\n")

SoftLine = Empty | Line

Space = Text(" ")


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
