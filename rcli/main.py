import click
import execute
import shell

#
# 'rcli' group (root group)
#

# This is our entrypoint - the main "show" command
@click.group()
# @click.pass_context
def cli():
    """SONiC command line - 'rcli' command"""
    pass

cli.add_command(execute.execute)
cli.add_command(shell.shell)
