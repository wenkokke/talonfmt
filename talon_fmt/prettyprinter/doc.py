from abc import ABC
from dataclasses import dataclass
from itertools import chain, filterfalse, repeat
from typing import (
    Generator,
    Iterable,
    Iterator,
    Optional,
    Tuple,
    Type,
    TypeAlias,
    Union,
    cast,
)
from py_singleton import singleton
from overrides import overrides
from more_itertools import intersperse


DocLike: TypeAlias = Union[str, "Doc"]


def to_doc(doc_like: DocLike) -> "Doc":
    if isinstance(doc_like, str):
        lines = doc_like.splitlines()
        if len(lines) > 1:
            return cat(lines, separator=Line)
        else:
            return Text(doc_like)
    else:
        return doc_like


DocLikes: TypeAlias = Union[DocLike, Iterable[DocLike]]


def to_docs(
    doc_likes: DocLikes,
) -> Generator["Doc", None, None]:
    if isinstance(doc_likes, (str, Doc)):
        yield to_doc(doc_likes)
    else:
        for doc_like in doc_likes:
            yield to_doc(doc_like)


def flatten(
    doc_likes: Iterable[DocLike],
    unpack_cls: Optional[Type[Iterable["Doc"]]] = None,
) -> Generator["Doc", None, None]:
    for doc_like in doc_likes:
        if unpack_cls and isinstance(doc_like, unpack_cls):
            for doc in iter(doc_like):
                yield doc
        else:
            yield to_doc(doc_like)


def cat(
    doc_likes: Iterable[DocLike],
    separator: Optional[DocLike] = None,
) -> "Doc":
    docs = flatten(doc_likes, unpack_cls=Cat)
    if docs:
        if separator:
            return Cat(intersperse(to_doc(separator), docs))
        else:
            return Cat(docs)
    else:
        return Empty


def row(doc_likes: Iterable[DocLike]) -> "Row":
    return Row(flatten(doc_likes, unpack_cls=Row))


def alt(doc_likes: Iterable[DocLike]) -> "Alt":
    return Alt(flatten(doc_likes, unpack_cls=Alt))


class Doc(ABC):
    def then(self, other: DocLike) -> "Doc":
        """
        Compose two documents.
        """
        return cat((self, other))

    def join(self, others: DocLikes) -> "Doc":
        """
        Compose a series of documents separated by this document.
        """
        return cat(to_docs(others), separator=self)

    def nest(self, indent: int) -> "Doc":
        """
        Indent a document.
        """
        if indent <= 0:
            return self
        else:
            return Nest(indent=indent, doc=self)

    def __truediv__(self, other: DocLike) -> "Doc":
        """
        Compose two documents.
        """
        return self.then(other)

    def __rtruediv__(self, other: DocLike) -> "Doc":
        """
        Compose two documents.
        """
        return to_doc(other).__truediv__(self)

    def __floordiv__(self, other: DocLike) -> "Doc":
        """
        Compose two documents, separated by a space.
        """
        other_doc = to_doc(other)
        if other_doc is Space or other_doc is Empty:
            return self.then(other_doc)
        else:
            return self.then(Space).then(other_doc)

    def __rfloordiv__(self, other: DocLike) -> "Doc":
        """
        Compose two documents, separated by a space.
        """
        return to_doc(other).__floordiv__(self)

    def __and__(self, other: DocLike) -> "Row":
        """
        Compose two documents, as columns in a row.
        """
        return row((self, other))

    def __rand__(self, other: DocLike) -> "Row":
        """
        Compose two documents, as columns in a row.
        """
        return to_doc(other).__and__(self)

    def __or__(self, other: DocLike) -> "Alt":
        """
        Combine two documents as alternatives.
        """
        return alt((self, other))

    def __ror__(self, other: DocLike) -> "Alt":
        """
        Combine two documents as alternatives.
        """
        return to_doc(other).__or__(self)


@singleton
@dataclass
class EmptyType(Doc):
    """
    The empty document.
    """

    @overrides
    def nest(self, indent: int) -> Doc:
        return self

    def __bool__(self) -> bool:
        return False

    def __repr__(self):
        return "Empty"


@singleton
@dataclass
class LineType(Doc):
    """
    A line break.
    """

    def __repr__(self):
        return "Line"


@dataclass
class Text(Doc):
    """
    A single line of text.
    """

    text: str

    @classmethod
    def intern(cls, name: str, text: str) -> "Text":
        if not hasattr(cls, name):
            obj = super().__new__(Text)
            obj.text = text
            setattr(cls, name, obj)
        return getattr(cls, name)

    def __new__(cls, text: str) -> "Text":
        if text:
            if text == " ":
                return cls.intern("Space", " ")
            instance = super().__new__(Text)
            instance.text = text
            return instance
        else:
            return cast(Text, Empty)

    def __init__(self, text: str) -> None:
        # Invariant: The text does not contain newlines.
        assert "\n" not in self.text

    def __mul__(self, times: int) -> Doc:
        return cat(repeat(self, times))

    def __rmul__(self, times: int) -> Doc:
        return self.__mul__(times)


@dataclass
class HStretch(Doc):
    char: Text

    def __init__(self, char: DocLike) -> None:
        char = to_doc(char)

        # Invariant: The document is Text.
        assert isinstance(char, Text)

        self.char = char

        # Invariant: The text is one character.
        assert len(self.char.text) == 1


@dataclass
class VStretch(Doc):
    doc: Doc

    def __init__(self, doc: DocLike) -> None:
        self.doc = to_doc(doc)


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

    def __init__(self, indent: int, doc: DocLike) -> None:
        if isinstance(doc, Nest):
            self.indent = indent + doc.indent
            self.doc = doc.doc
        else:
            self.indent = indent
            self.doc = to_doc(doc)

        # Invariant: The doc is not Nest
        assert not isinstance(self.doc, Nest)
        # Invariant: The indent is greater than zero.
        assert self.indent > 0

    @overrides
    def nest(self, indent: int) -> Doc:
        indent = self.indent + indent
        if indent <= 0:
            return self.doc
        else:
            return Nest(indent=indent, doc=self.doc)


@dataclass
class Alt(Doc, Iterable[Doc]):
    """
    Alternatives for the document layout.
    """

    docs: Tuple[Doc, ...]

    @classmethod
    def intern(cls, name: str, docs: Tuple[Doc, ...]) -> "Alt":
        if not hasattr(cls, name):
            obj = super().__new__(Alt)
            obj.docs = docs
            setattr(cls, name, obj)
        return getattr(cls, name)

    def __new__(cls, doc_likes: Iterable[DocLike]) -> "Alt":
        docs = tuple(flatten(doc_likes, unpack_cls=Alt))
        if docs:
            if docs == (Empty, Line):
                return cls.intern("SoftLine", (Empty, Line))
            instance = super().__new__(Alt)
            instance.docs = docs
            return instance
        else:
            return cast(Alt, Empty)

    def __init__(self, doc_likes: Iterable[DocLike]):
        # Invariant: None of docs is an instance of Alt.
        assert all(not isinstance(doc, Alt) for doc in self.docs)
        # Invariant: The alternatives should be listed in increasing order of width.
        # TODO: not asserted

    def __iter__(self) -> Iterator[Doc]:
        return iter(self.docs)

    def __repr__(self) -> str:
        if self is SoftLine:
            return "SoftLine"
        else:
            return " | ".join(map(repr, self.docs))


@dataclass
class Cat(Doc, Iterable[Doc]):
    """
    Concatenated documents.
    """

    docs: Tuple[Doc, ...]

    def __init__(self, doc_likes: Iterable[DocLike]) -> None:
        self.docs = tuple(filterfalse(bool, flatten(doc_likes, unpack_cls=Cat)))

        # Invariant: None of docs is an instance of Cat.
        assert all(not isinstance(doc, Cat) for doc in self.docs)
        # Invariant: None of docs is Empty.
        assert all(doc is not Empty for doc in self.docs)

    def __iter__(self) -> Iterator[Doc]:
        return iter(self.docs)


@dataclass
class Row(Doc, Iterable[Doc]):
    """
    Multicolumn documents.
    """

    docs: Tuple[Doc, ...]

    def __init__(self, doc_likes: Iterable[DocLike]) -> None:
        self.docs = tuple(flatten(doc_likes, unpack_cls=Row))

        # Invariant: None of docs is an instance of Row.
        assert all(not isinstance(doc, Row) for doc in self.docs)

    def __iter__(self) -> Iterator[Doc]:
        return iter(self.docs)


Empty = EmptyType()

Line = LineType()

SoftLine = Empty | Line

Space = Text(" ")


def between(
    open: DocLike,
    doc_like_or_doc_likes: DocLike | Iterable[DocLike],
    close: DocLike,
    *,
    separator: Optional[DocLike] = None
) -> Doc:

    return cat(
        chain((open,), to_docs(doc_like_or_doc_likes), (close,)),
        separator=separator,
    )


def parens(
    doc_likes: DocLike | Iterable[DocLike], *, separator: Optional[DocLike] = None
) -> Doc:
    return between("(", doc_likes, ")", separator=separator)


def brackets(
    doc_likes: DocLike | Iterable[DocLike], *, separator: Optional[DocLike] = None
) -> Doc:
    return between("[", doc_likes, "]", separator=separator)


def braces(
    doc_likes: DocLike | Iterable[DocLike], *, separator: Optional[DocLike] = None
) -> Doc:
    return between("{", doc_likes, "}", separator=separator)


def angles(
    doc_likes: DocLike | Iterable[DocLike], *, separator: Optional[DocLike] = None
) -> Doc:
    return between("<", doc_likes, ">", separator=separator)
