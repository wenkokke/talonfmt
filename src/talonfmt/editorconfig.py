from pathlib import Path
from typing import Dict, Optional, cast

try:
    from editorconfig import EditorConfigError, get_properties

    def get_editorconfig(file: str) -> Dict[str, str]:
        try:
            return cast(Dict[str, str], get_properties(Path(file).absolute()) or {})
        except EditorConfigError:
            return {}

except ModuleNotFoundError as e:
    if e.name != "editorconfig":
        raise e

    def get_editorconfig(file: str) -> Dict[str, str]:
        return {}


def get_indent_size(file: str) -> Optional[int]:
    indent_size = get_editorconfig(file).get("indent_size", None)
    if indent_size is not None:
        return int(indent_size)
    else:
        return None


def get_max_line_length(file: str) -> Optional[int]:
    max_line_length = get_editorconfig(file).get("max_line_length", None)
    if max_line_length is not None:
        return int(max_line_length)
    else:
        return None
