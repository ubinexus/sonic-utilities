import os
import click

from linecard import Linecard
from rich.console import Console

console = Console()

@click.command()
@click.argument('linecard_name')
def shell(linecard_name):
    """Open interactive shell for one linecard."""
    lc = Linecard(linecard_name, os.getlogin(), console)
    lc.start_shell()


if __name__=="__main__":
    shell(prog_name='shell')
