import os
import click

from linecard import Linecard
from rich.console import Console

console = Console()

@click.command()
@click.argument('linecards', nargs=-1, required=True)
@click.argument('command')
def execute(linecards, command):
    """Execute a command on one (or many) linecards."""
    for linecard_name in (linecards):
        lc = Linecard(linecard_name, os.getlogin(), console, print_login=False)
        console.print(f"{linecard_name} output: ")
        print(lc.execute_cmd(command))


if __name__=="__main__":
    execute(prog_name='execute')
