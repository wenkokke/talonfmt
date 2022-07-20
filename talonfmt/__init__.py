from pathlib import Path
from tree_sitter_talon import parse
from talonfmt.formatter import TalonFormatter
from prettyprinter import SmartDocRenderer

import click

@click.command(name="talonfmt")
@click.argument('filename', type=click.Path(exists=True))
@click.option('--indent-size', type=int, default=4, show_default=True)
@click.option('--max-line-width', type=int, default=80, show_default=True)
def talonfmt(filename: str, indent_size: int, max_line_width: int):
   ast = parse(Path(filename).read_bytes())
   fmt = TalonFormatter(indent_size=indent_size)
   doc = fmt.format(ast)
   ren = SmartDocRenderer(max_line_width=max_line_width)
   print(ren.to_str(doc))

def main():
   talonfmt(prog_name="talonfmt")

if __name__ == '__main__':
   main()