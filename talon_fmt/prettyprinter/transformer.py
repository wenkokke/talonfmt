from abc import abstractmethod
from typing import Generic, TypeVar

from .doc import *


Result = TypeVar("Result")


class DocTransformer(Generic[Result]):
    def transform(self, doc: Doc) -> Result:
        if doc is Empty:
            return self.transform_Empty()
        if doc is Line:
            return self.transform_Line()
        if isinstance(doc, Text):
            return self.transform_Text(text=doc.text)
        if isinstance(doc, Nest):
            return self.transform_Nest(
                indent=doc.indent, doc=self.transform(doc.doc), doc_hist=doc.doc
            )
        if isinstance(doc, Alt):
            # NOTE: Don't automatically recurse under alternatives
            return self.transform_Alt(docs_hist=doc.docs)
        if isinstance(doc, Cat):
            return self.transform_Cat(
                docs=self.transform_all(doc.docs), docs_hist=doc.docs
            )
        if isinstance(doc, Row):
            return self.transform_Row(
                cols=self.transform_all(doc.cols), cols_hist=doc.cols
            )
        if isinstance(doc, Table):
            return self.transform_Table(
                rows=self.transform_all(doc.rows), rows_hist=doc.rows
            )
        if isinstance(doc, HStretch):
            return self.transform_HStretch(
                char=self.transform(doc.char), char_hist=doc.char
            )
        if isinstance(doc, VStretch):
            return self.transform_VStretch(
                doc=self.transform(doc.doc), doc_hist=doc.doc
            )
        raise ValueError(doc)

    def transform_all(self, docs: tuple[Doc, ...]) -> Iterator[Result]:
        return map(self.transform, docs)

    @abstractmethod
    def transform_Empty(self) -> Result:
        """
        Transform a Empty document.
        """

    @abstractmethod
    def transform_Line(self) -> Result:
        """
        Transform a Line document.
        """

    @abstractmethod
    def transform_Text(self, text: str) -> Result:
        """
        Transform a Text document.
        """

    @abstractmethod
    def transform_Nest(self, indent: int, doc: Result, *, doc_hist: Doc) -> Result:
        """
        Transform a Nest document.
        """

    @abstractmethod
    def transform_Alt(self, *, docs_hist: tuple[Doc, ...]) -> Result:
        """
        Transform a Alt document.
        """

    @abstractmethod
    def transform_Cat(
        self, docs: Iterator[Result], *, docs_hist: tuple[Doc, ...]
    ) -> Result:
        """
        Transform a Cat document.
        """

    @abstractmethod
    def transform_Row(
        self, cols: Iterator[Result], *, cols_hist: tuple[Doc, ...]
    ) -> Result:
        """
        Transform a Row document.
        """

    @abstractmethod
    def transform_Table(
        self, rows: Iterator[Result], *, rows_hist: tuple[Row, ...]
    ) -> Result:
        """
        Transform a Table document.
        """

    @abstractmethod
    def transform_HStretch(self, char: Result, *, char_hist: Text) -> Result:
        """
        Transform a HStretch document.
        """

    @abstractmethod
    def transform_VStretch(self, doc: Result, *, doc_hist: Doc) -> Result:
        """
        Transform a VStretch document.
        """
