import sys
from typing import Optional, Union

from doc_printer import DocRenderer, SimpleDocRenderer, SimpleLayout, SmartDocRenderer
from tree_sitter_talon import Node, parse

from .formatter import EmptyMatchContext, TalonFormatter

__version__: str = "1.8.1"


def talonfmt(
    contents: Union[str, bytes, Node],
    *,
    filename: Optional[str] = None,
    encoding: str = "utf-8",
    safe: Optional[bool] = None,
    indent_size: int = 4,
    max_line_width: Optional[int] = None,
    align_match_context: bool = False,
    align_match_context_at: Optional[int] = None,
    align_short_commands: bool = False,
    align_short_commands_at: Optional[int] = None,
    simple_layout: Optional[str] = None,
    format_comments: bool = False,
    empty_match_context: str = "keep",
    preserve_blank_lines: tuple[str, ...] = ("body", "command"),
):
    # Parse (if necessary):
    if isinstance(contents, Node):
        ast = contents
        # If the contents are already an AST node, we must disable the
        # safety tests, as we don't know if they parse as source code.
        safe = safe or False
    elif isinstance(contents, (str, bytes)):
        ast = parse(contents, encoding=encoding, raise_parse_error=True)
    else:
        raise TypeError(type(contents))

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

    # Interpret the empty_match_context setting
    empty_match_context_options: dict[str, EmptyMatchContext] = {
        "show": EmptyMatchContext.Show,
        "keep": EmptyMatchContext.Keep,
        "hide": EmptyMatchContext.Hide,
    }

    # Create an instance of TalonFormatter
    talon_formatter = TalonFormatter(
        indent_size=indent_size,
        align_match_context=merged_match_context,
        align_short_commands=merged_short_commands,
        empty_match_context=empty_match_context_options[empty_match_context],
        format_comments=format_comments,
        preserve_blank_lines_in_header="header" in preserve_blank_lines,
        preserve_blank_lines_in_body="body" in preserve_blank_lines,
        preserve_blank_lines_in_command="command" in preserve_blank_lines,
    )

    # Create an instance of DocRenderer
    def create_doc_renderer(*, verbose: bool = True) -> DocRenderer:
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
                    if verbose and incompatible_options:
                        sys.stderr.write(
                            f"Warning: incompatible options '--simple-layout=shortest' and {incompatible_options}\n"
                        )
                simple_layout_value = SimpleLayout.LongestLines
            else:
                simple_layout_value = SimpleLayout.ShortestLines
            doc_renderer = SimpleDocRenderer(simple_layout=simple_layout_value)
        else:
            # Resolve --simple-layout
            if verbose and simple_layout is not None:
                sys.stderr.write(
                    f"Warning: incompatible options '--max-line-width' and '--simple-layout'\n"
                )
            doc_renderer = SmartDocRenderer(max_line_width=max_line_width)
        return doc_renderer

    def render(ast: Node, *, verbose: bool) -> str:
        doc = talon_formatter.format(ast)
        return create_doc_renderer(verbose=verbose).to_str(doc)

    formatted = render(ast, verbose=True)

    # safety tests:
    if safe or (safe is None and __debug__):

        ast_for_formatted = parse(formatted, encoding=encoding, raise_parse_error=True)
        # assert: parsing output results in a similar AST
        ast.assert_equivalent(ast_for_formatted)

        # assert: formatting twice results in the same output
        assert formatted == render(
            ast_for_formatted, verbose=False
        ), f"Formatting {filename or 'input'} twice gives a differrent result."

    return formatted
