from talon_fmt.formatter import TalonFormatter
from talon_fmt.prettyprinter.doc import *
from tree_sitter_talon import Node as Node, Point as Point, NodeTransformer
from typing import Dict, Generic, Sequence, Union

import tree_sitter_talon as talon


def format(contents: Union[str, bytes], has_header: Optional[bool] = None) -> Doc:
    node = talon.parse(contents)
    formatter = TalonFormatter()
    doc = formatter.transform(node)
    return doc
