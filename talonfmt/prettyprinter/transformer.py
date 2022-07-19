# from abc import abstractmethod
# from typing import Generic, TypeVar

# from .doc import *


# Result = TypeVar("Result")


# class DocTransformer(Generic[Result]):
#     def transform(self, doc: Doc) -> Result:
#         if doc is Empty:
#             yield from self.transform_Empty()
#         if doc is Space:
#             yield from self.transform_Space()
#         if doc is Line:
#             yield from self.transform_Line()
#         if isinstance(doc, Text):
#             yield from self.transform_Text(text=doc.text)
#         if isinstance(doc, Nest):
#             subdoc = self.transform(doc.doc)
#             yield from self.transform_Nest(doc.indent, subdoc, doc_hist=doc.doc)
#         if isinstance(doc, Alt):
#             # NOTE: Don't automatically recurse under alternatives.
#             yield from self.transform_Alt(docs_hist=doc.docs)
#         if isinstance(doc, Cat):
#             docs = self.transform_all(doc.docs)
#             yield from self.transform_Cat(docs=docs, docs_hist=doc.docs)
#         if isinstance(doc, Row):
#             cols = self.transform_all(doc.cols)
#             yield from self.transform_Row(cols=cols, cols_hist=doc.cols)
#         if isinstance(doc, Table):
#             rows = self.transform_all(doc.rows)
#             yield from self.transform_Table(rows=rows, rows_hist=doc.rows)
#         if isinstance(doc, HStretch):
#             subdoc = self.transform(doc.doc)
#             yield from self.transform_HStretch(doc=subdoc, doc_hist=doc.doc)
#         if isinstance(doc, VStretch):
#             subdoc = self.transform(doc.doc)
#             yield from self.transform_VStretch(doc=subdoc, doc_hist=doc.doc)
#         raise ValueError(doc)

#     def transform_all(self, docs: tuple[Doc, ...]) -> Iterator[Result]:
#         yield from map(self.transform, docs)

#     @abstractmethod
#     def transform_Empty(self) -> Result:
#         """
#         Transform a Empty document.
#         """

#     @abstractmethod
#     def transform_Line(self) -> Result:
#         """
#         Transform a Line document.
#         """

#     @abstractmethod
#     def transform_Space(self) -> Result:
#         """
#         Transform a Space document.
#         """

#     @abstractmethod
#     def transform_Text(self, text: str) -> Result:
#         """
#         Transform a Text document.
#         """

#     @abstractmethod
#     def transform_Nest(self, indent: int, doc: Result, *, doc_hist: Doc) -> Result:
#         """
#         Transform a Nest document.
#         """

#     @abstractmethod
#     def transform_Alt(self, *, docs_hist: tuple[Doc, ...]) -> Result:
#         """
#         Transform a Alt document.
#         """

#     @abstractmethod
#     def transform_Cat(
#         self, docs: Iterator[Result], *, docs_hist: tuple[Doc, ...]
#     ) -> Result:
#         """
#         Transform a Cat document.
#         """

#     @abstractmethod
#     def transform_Row(
#         self, cols: Iterator[Result], *, cols_hist: tuple[Doc, ...]
#     ) -> Result:
#         """
#         Transform a Row document.
#         """

#     @abstractmethod
#     def transform_Table(
#         self, rows: Iterator[Result], *, rows_hist: tuple[Row, ...]
#     ) -> Result:
#         """
#         Transform a Table document.
#         """

#     @abstractmethod
#     def transform_HStretch(self, doc: Result, *, doc_hist: Doc) -> Result:
#         """
#         Transform a HStretch document.
#         """

#     @abstractmethod
#     def transform_VStretch(self, doc: Result, *, doc_hist: Doc) -> Result:
#         """
#         Transform a VStretch document.
#         """
