import io
import sys
import tokenize
from pathlib import Path
from typing import Optional, Union

import click
import tree_sitter_talon
from doc_printer import DocRenderer, SimpleDocRenderer, SimpleLayout, SmartDocRenderer

from talonfmt.formatter import ParseError, TalonFormatter

__version__: str = "1.5.1"


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
    simple_layout: Optional[str] = None,
    format_comments: bool = True,
    preserve_blank_lines: tuple[str, ...] = ("body", "command"),
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
        preserve_blank_lines_in_header="header" in preserve_blank_lines,
        preserve_blank_lines_in_body="body" in preserve_blank_lines,
        preserve_blank_lines_in_command="command" in preserve_blank_lines,
    )

    # Create an instance of DocRenderer
    doc_renderer: DocRenderer
    if max_line_width is None:
        # Resolve --simple-layout
        simple_layout_value: SimpleLayout
        if (
            simple_layout == "longtest"
            or align_match_context is not False
            or align_short_commands is not False
        ):
            if simple_layout == "shortest":
                incompatible_options: list[str]
                if align_match_context is not False:
                    incompatible_options.append("--align-match-context")
                if align_short_commands is not False:
                    incompatible_options.append("--align-short-commands")
                sys.stderr.write(
                    f"Warning: incompatible options '--simple-layout=shortest' and {incompatible_options}\n"
                )
            simple_layout_value = SimpleLayout.LongestLines
        else:
            simple_layout_value = SimpleLayout.ShortestLines
        doc_renderer = SimpleDocRenderer(simple_layout=simple_layout_value)
    else:
        # Resolve --simple-layout
        if simple_layout is not None:
            sys.stderr.write(
                f"Warning: incompatible options '--max-line-width' and '--simple-layout'\n"
            )
        doc_renderer = SmartDocRenderer(max_line_width=max_line_width)

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
@click.option(
    "--indent-size",
    type=int,
    default=4,
    show_default=True,
)
@click.option(
    "--max-line-width",
    type=int,
    show_default=True,
)
@click.option(
    "--simple-layout",
    type=click.Choice(["shortest", "longest"], case_sensitive=False),
    default=None,
    show_default=False,
)
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
    "--preserve-blank-lines",
    type=click.Choice(["header", "body", "command"], case_sensitive=False),
    multiple=True,
    default=("body", "command"),
    show_default=True,
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
@click.version_option(
    version=__version__,
    prog_name="talonfmt",
    message=f"%(prog)s, version %(version)s (with tree-sitter-talon, version {tree_sitter_talon.__grammar_version__})",
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
    preserve_blank_lines: tuple[str, ...],
    simple_layout: Optional[str],
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
            output = talonfmt(
                contents,
                encoding=encoding,
                indent_size=indent_size,
                max_line_width=max_line_width,
                align_match_context=align_match_context,
                align_match_context_at=align_match_context_at,
                align_short_commands=align_short_commands,
                align_short_commands_at=align_short_commands_at,
                simple_layout=simple_layout,
                format_comments=format_comments,
                preserve_blank_lines=preserve_blank_lines,
            )
            if contents != output and filename:
                if verbose:
                    sys.stderr.write(f"Fixed {filename}\n")
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
        contents = "".join(sys.stdin.readlines())
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
