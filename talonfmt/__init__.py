import io
import sys
import tokenize
from pathlib import Path
from typing import Optional, Union

import click
import tree_sitter_talon
from doc_printer import DocRenderer, SimpleDocRenderer, SimpleLayout, SmartDocRenderer

from talonfmt.formatter import ParseError, TalonFormatter


def talonfmt(
    contents: str,
    *,
    encoding: str = "utf-8",
    indent_size: int = 4,
    max_line_width: Optional[int] = None,
    align_match_context: bool = False,
    align_match_context_at: Optional[int] = None,
    align_short_commands: bool = False,
    align_short_commands_at: Optional[int] = None,
    format_comments: bool = True,
) -> str:
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
        format_comments=format_comments,
    )

    # Create an instance of DocRenderer
    doc_renderer: DocRenderer
    if max_line_width:
        doc_renderer = SmartDocRenderer(max_line_width=max_line_width)
    else:
        simple_layout: SimpleLayout
        if align_match_context is not False or align_short_commands is not False:
            simple_layout = SimpleLayout.LongestLines
        else:
            simple_layout = SimpleLayout.ShortestLines
        doc_renderer = SimpleDocRenderer(simple_layout=simple_layout)

    ast = tree_sitter_talon.parse(contents, encoding=encoding)
    doc = talon_formatter.format(ast)
    return doc_renderer.to_str(doc)


@click.command(name="talonfmt")
@click.argument(
    "path",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, readable=True, path_type=Path
    ),
)
@click.option("--indent-size", type=int, default=4, show_default=True)
@click.option("--max-line-width", type=int, show_default=True)
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
    "--format-comments/--no-format-comments",
    default=True,
    show_default=True,
)
@click.option(
    "--in-place/--stdout",
    default=False,
    show_default=True,
)
@click.option(
    "--fail-on-change/--no-fail-on-change",
    default=False,
    show_default=True,
)
@click.option(
    "--fail-on-error/--no-fail-on-error",
    default=False,
    show_default=True,
)
@click.option(
    "--verbose/--quiet",
    default=True,
    show_default=True,
)
def cli(
    *,
    path: tuple[Path, ...],
    indent_size: int,
    max_line_width: Optional[int],
    align_match_context: bool,
    align_match_context_at: Optional[int],
    align_short_commands: bool,
    align_short_commands_at: Optional[int],
    format_comments: bool,
    in_place: bool,
    fail_on_change: bool,
    fail_on_error: bool,
    verbose: bool,
):
    files_changed: list[str] = []

    def readfile(filename: Path) -> tuple[str, str]:
        with filename.open(mode="rb") as fp:
            bytes_on_disk = fp.read()
        encoding, _ = tokenize.detect_encoding(io.BytesIO(bytes_on_disk).readline)
        with io.TextIOWrapper(io.BytesIO(bytes_on_disk), encoding) as wrapper:
            contents = wrapper.read()
        return (contents, encoding)

    def format(
        contents: str, *, encoding: str, filename: Optional[str] = None
    ) -> Optional[str]:
        try:
            if verbose:
                sys.stderr.write(f"Formatting {filename}...\n")
            output = talonfmt(
                contents,
                encoding=encoding,
                indent_size=indent_size,
                max_line_width=max_line_width,
                align_match_context=align_match_context,
                align_match_context_at=align_match_context_at,
                align_short_commands=align_short_commands,
                align_short_commands_at=align_short_commands_at,
                format_comments=format_comments,
            )
            if contents != output and filename:
                if fail_on_change and verbose:
                    sys.stderr.write(f"File changed!")
                files_changed.append(filename)
            return output
        except ParseError as e:
            sys.stderr.write(e.message(contents=contents, filename=filename))
            if fail_on_error:
                exit(1)
        return None

    def format_file(filename: Path):
        contents, encoding = readfile(filename)
        output = format(contents, encoding=encoding, filename=str(filename))
        if output:
            if in_place:
                with filename.open(mode="w") as handle:
                    handle.write(output)
            else:
                sys.stdout.write(output)

    if path:
        for file_or_dir in path:
            if file_or_dir.is_file():
                format_file(file_or_dir)
            if file_or_dir.is_dir():
                for file in file_or_dir.glob("**/*.talon"):
                    format_file(file)
    else:
        contents = "\n".join(sys.stdin.readlines())
        encoding = sys.stdin.encoding
        output = format(contents, encoding=encoding)
        if output:
            sys.stdout.write(output)

    if fail_on_change and files_changed:
        exit(2)
    else:
        exit(0)


def main():
    cli(prog_name="talonfmt")


if __name__ == "__main__":
    main()
