import click

import utilities_common.cli as clicommon


@click.group(
    name='syslog',
    cls=clicommon.AliasedGroup
)
@click.pass_context
def syslog(ctx):
    """Syslog server configuration tasks"""
    #config_db = ConfigDBConnector()
    #config_db.connect()
    #ctx.obj = {'db': config_db}
    pass


@syslog.command('add')
#@click.argument('syslog_ip_address', metavar='<syslog_ip_address>', required=True)
@click.argument('syslog_ip_address', required=True)
@clicommon.pass_db
def add_syslog_server(db, syslog_ip_address):
    """ Add syslog server IP """
    if not clicommon.is_ipaddress(syslog_ip_address):
        ctx.fail('Invalid ip address')
    #db = ctx.obj['db']
    db = db.config_db
    syslog_servers = db.get_table("SYSLOG_SERVER")
    if syslog_ip_address in syslog_servers:
        click.echo("Syslog server {} is already configured".format(syslog_ip_address))
        return
    else:
        db.set_entry('SYSLOG_SERVER', syslog_ip_address, {'NULL': 'NULL'})
        click.echo("Syslog server {} added to configuration".format(syslog_ip_address))
        try:
            click.echo("Restarting rsyslog-config service...")
            clicommon.run_command("systemctl restart rsyslog-config", display_cmd=False)
        except SystemExit as e:
            ctx.fail("Restart service rsyslog-config failed with error {}".format(e))


@syslog.command('del')
@click.argument('syslog_ip_address', metavar='<syslog_ip_address>', required=True)
#@click.pass_context
@clicommon.pass_db
def del_syslog_server(db, syslog_ip_address):
    """ Delete syslog server IP """
    if not clicommon.is_ipaddress(syslog_ip_address):
        ctx.fail('Invalid IP address')
    
    #db = ctx.obj['db']
    db = db.config_db
    syslog_servers = db.get_table("SYSLOG_SERVER")
    if syslog_ip_address in syslog_servers:
        db.set_entry('SYSLOG_SERVER', '{}'.format(syslog_ip_address), None)
        click.echo("Syslog server {} removed from configuration".format(syslog_ip_address))
    else:
        ctx.fail("Syslog server {} is not configured.".format(syslog_ip_address))
    try:
        click.echo("Restarting rsyslog-config service...")
        clicommon.run_command("systemctl restart rsyslog-config", display_cmd=False)
    except SystemExit as e:
        ctx.fail("Restart service rsyslog-config failed with error {}".format(e))
