import click
import utilities_common.cli as clicommon
from swsscommon.swsscommon import SonicV2Connector


# Define GEARBOX commands only if GEARBOX is configured
app_db = SonicV2Connector(host='127.0.0.1')
app_db.connect(app_db.APPL_DB)

if app_db.keys(app_db.APPL_DB, '_GEARBOX_TABLE:phy:*'):
    @click.group(cls=clicommon.AliasedGroup)
    def gearbox():
        """Show gearbox info"""
        pass

    # 'phys' subcommand ("show gearbox phys")
    @gearbox.group(cls=clicommon.AliasedGroup)
    def phys():
        """Show external PHY information"""
        pass

    # 'status' subcommand ("show gearbox phys status")
    @phys.command()
    @click.pass_context
    def status(ctx):
        """Show gearbox phys status"""
        clicommon.run_command("gearboxutil phys status")

    # 'interfaces' subcommand ("show gearbox interfaces")
    @gearbox.group(cls=clicommon.AliasedGroup)
    def interfaces():
        """Show gearbox interfaces information"""
        pass

    # 'status' subcommand ("show gearbox interfaces status")
    @interfaces.command()
    @click.pass_context
    def status(ctx):
        """Show gearbox interfaces status"""
        clicommon.run_command("gearboxutil interfaces status")
