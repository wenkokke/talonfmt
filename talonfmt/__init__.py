from doc_printer import SmartDocRenderer, TokenStream
from pathlib import Path
from talonfmt.formatter import TalonFormatter
from typing import Optional, Union

import click
import io
import sys
import tokenize
import tree_sitter_talon


@click.command(name="talonfmt")
@click.argument(
    "input",
    required=False,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, readable=True, path_type=Path
    ),
)
@click.option("--indent-size", type=int, default=4, show_default=True)
@click.option(
    "--align-match-context/--no-align-match-context",
    default=False,
    show_default=True,
)
@click.option(
    "--align-match-context-at",
    type=int,
)
@click.option(
    "--align-short-commands/--no-align-short-commands",
    default=False,
    show_default=True,
)
@click.option(
    "--align-short-commands-at",
    type=int,
)
@click.option(
    "--in-place/--stdout",
    default=False,
    show_default=True,
)
@click.option("--max-line-width", type=int, default=80, show_default=True)
def cli(
    *,
    input: Optional[Path],
    indent_size: int,
    max_line_width: int,
    align_match_context: bool,
    align_match_context_at: Optional[int],
    align_short_commands: bool,
    align_short_commands_at: Optional[int],
    in_place: bool,
):
    # Enable align_match_context if align_match_context_at is set:
    merged_match_context: Union[bool, int]
    if isinstance(align_match_context_at, int):
        merged_match_context = align_match_context_at
    else:
        merged_match_context = align_match_context

    # Enable align_short_commands if align_short_commands_at is set:
    merged_short_commands: Union[bool, int]
    if isinstance(align_short_commands_at, int):
        merged_short_commands = align_short_commands_at
    else:
        merged_short_commands = align_short_commands

    # Create an instance of TalonFormatter
    talon_formatter = TalonFormatter(
        indent_size=indent_size,
        align_match_context=merged_match_context,
        align_short_commands=merged_short_commands,
    )

    # Create an instance of DocRenderer
    doc_renderer = SmartDocRenderer(
        max_line_width=max_line_width,
    )

    # Create a formatting function
    def talon_format(contents: str, *, encoding: str = "utf-8") -> None:
        ast = tree_sitter_talon.parse(contents, encoding=encoding)
        doc = talon_formatter.format(ast)
        if in_place:
            with filename.open(mode="w", encoding=encoding) as fp:
                for token in doc_renderer.render(doc):
                    fp.write(token.text)
        else:
            for token in doc_renderer.render(doc):
                sys.stdout.write(token.text)

    def talon_format_file(filename: Path) -> None:
        with filename.open(mode="rb") as fp:
            bytes_on_disk = fp.read()
        encoding, _ = tokenize.detect_encoding(io.BytesIO(bytes_on_disk).readline)
        with io.TextIOWrapper(io.BytesIO(bytes_on_disk), encoding) as wrapper:
            contents = wrapper.read()
        talon_format(contents, encoding=encoding)

    if input:
        if input.is_file():
            talon_format_file(input)
        if input.is_dir():
            for filename in input.glob("**/*.talon"):
                talon_format_file(filename)
    else:
        contents = "\n".join(sys.stdin.readlines())
        talon_format(contents, encoding=sys.stdin.encoding)


def main():
    cli(prog_name="talonfmt")


if __name__ == "__main__":
    main()
