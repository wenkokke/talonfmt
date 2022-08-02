import dataclasses
from collections.abc import Iterator
from typing import Optional, Sequence

from tree_sitter_talon import Point, TalonError


@dataclasses.dataclass
class ParseError(Exception):
    start_position: Point
    end_position: Point

    def __init__(self, talon_error: TalonError):
        self.start_position = talon_error.start_position
        self.end_position = talon_error.end_position

    @staticmethod
    def point_to_str(point: Point) -> str:
        return f"line {point.row}, column {point.column}"

    def range(self) -> str:
        if self.start_position.row == self.end_position.row:
            return f"on line {self.start_position.row} between column {self.start_position.column} and {self.end_position.column}"
        else:
            return f" between {self.point_to_str(self.start_position)} and {self.point_to_str(self.end_position)}"

    def annotated_region(self, contents: str) -> str:
        def annotated_lines(lines: Sequence[str]) -> Iterator[str]:
            for l, line in enumerate(lines):
                yield line
                is_first_line = l == 0
                is_last_line = l == len(lines) - 1
                start = self.start_position.column if is_first_line else 0
                end = self.end_position.column if is_last_line else len(line)
                annotation: list[str] = []
                for c, _ in enumerate(line):
                    if c <= start or end < c:
                        annotation.append(" ")
                    else:
                        annotation.append("^")
                yield "".join(annotation)

        lines = contents.splitlines()
        lines = lines[self.start_position.row : self.end_position.row + 1]
        return "\n".join(annotated_lines(lines))

    def message(self, *, contents: str, filename: Optional[str] = None) -> str:
        return "".join(
            (
                f"Parse error ",
                f"in {filename} " if filename else "",
                f"{self.range()}:\n",
                f"{self.annotated_region(contents)}\n",
            )
        )
