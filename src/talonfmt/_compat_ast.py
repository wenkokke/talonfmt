import sys
from typing import List

__all__: List[str] = ["astparse", "astunparse"]

from ast import parse as astparse

if sys.version_info < (3, 9):
    from astunparse import unparse as astunparse
else:
    from ast import unparse as astunparse
