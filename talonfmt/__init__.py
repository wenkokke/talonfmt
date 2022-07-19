from talonfmt.formatter import TalonFormatter
from talonfmt.prettyprinter.doc import *
from tree_sitter_talon import Node as Node, Point as Point, NodeTransformer
from typing import Dict, Generic, Sequence, Union

import tree_sitter_talon as talon

from talonfmt.prettyprinter.render import SimpleDoc, SimpleDocRenderer


def format(contents: Union[str, bytes], has_header: Optional[bool] = None) -> str:
    node = talon.parse(contents, has_header)
    formatter = TalonFormatter()
    doc: SimpleDoc = formatter.format(node)
    renderer = SimpleDocRenderer()
    return renderer.render(doc)
