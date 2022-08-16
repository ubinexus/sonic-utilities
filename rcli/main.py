import click


#
# 'rcli' group (root group)
#

# This is our entrypoint - the main "show" command
@click.command()
# @click.pass_context
def cli():
    """
    SONiC command line - 'rcli' command.

    Usage: rexec LINECARDS -c \"COMMAND\"
    or rshell LINECARD
    """
    print(cli.__doc__)