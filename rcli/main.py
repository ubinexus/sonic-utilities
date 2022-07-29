import click


#
# 'rcli' group (root group)
#

# This is our entrypoint - the main "show" command
@click.group()
# @click.pass_context
def cli():
    """SONiC command line - 'rcli' command"""
    pass