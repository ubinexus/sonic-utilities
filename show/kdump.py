import click
import itertools
from tabulate import tabulate
import utilities_common.cli as clicommon
from swsscommon.swsscommon import ConfigDBConnector


#
# 'kdump command ("show kdump ...")
#
@click.group(cls=clicommon.AliasedGroup, name="kdump")
def kdump():
    """Show kdump configuration, status and information """
    pass


def get_kdump_admin_mode():
    """Fetches the administrative mode of Kdump from `CONFIG_DB`.

    Args:
      None.

    Returns:
      admin_mode: If Kdump is enabled, returns "Enabled"; If Kdump is disabled,
      returns "Disabled"; Otherwise, returns "Unknown".
    """
    admin_mode = "Unknown"
    config_db = ConfigDBConnector()
    if config_db:
        config_db.connect()
        kdump_table = config_db.get_table("KDUMP")
        if kdump_table and "config" in kdump_table and "enabled" in kdump_table["config"]:
            if kdump_table["config"]["enabled"] == "true":
                admin_mode = "Enabled"
            else:
                admin_mode = "Disabled"

    return admin_mode


def get_kdump_oper_mode():
    """Fetches the operational mode of Kdump from the result of ommand
    `/usr/sbin/kdump-config status`.

    Args:
      None.

    Returns:
      admin_mode: If Kdump is ready, returns "Ready"; If Kdump is not ready,
      returns "Unready"; Otherwise, returns "Unknown".
    """
    oper_mode = "Unready"
    command_stdout, command_stderr, exit_code = clicommon.run_command("/usr/sbin/kdump-config status",
                                                                      return_cmd=True)
    if exit_code != 0:
        oper_mode = "Unknown"
        return oper_mode

    for line in command_stdout.splitlines():
        if ": ready to kdump" in line:
            oper_mode = "Ready"
            break

    return oper_mode


def get_kdump_memory_config():
    """Fetches the memory configuration of Kdump from `CONFIG_DB`.

    Args:
      None.

    Returns:
      mem_config: If memory was configured, returns the configuration information;
      Otherwise, returns "Unknown".
    """
    mem_config = "Unknown"
    config_db = ConfigDBConnector()

    if config_db:
        config_db.connect()
        kdump_table = config_db.get_table("KDUMP")
        if kdump_table and "config" in kdump_table and "memory" in kdump_table["config"]:
            mem_config = kdump_table["config"]["memory"]

    return mem_config


def get_kdump_num_files():
    """Fetches the maximum number of Kdump files configured in `CONFIG_DB`.

    Args:
      None.

    Returns:
      num_files_config: If the number of Kdump files was configured, returns the
      configuration information; Otherwise, returns "Unknown".
    """
    num_files_config = "Unknown"
    config_db = ConfigDBConnector()

    if config_db:
        config_db.connect()
        kdump_table = config_db.get_table("KDUMP")
        if kdump_table and "config" in kdump_table and "num_dumps" in kdump_table["config"]:
            num_files_config = kdump_table["config"]["num_dumps"]

    return num_files_config


@kdump.command(name="config", short_help="Show the configuration of Linux kernel dump")
def config():
    admin_mode = get_kdump_admin_mode()
    oper_mode = get_kdump_oper_mode()

    click.echo("Kdump administrative mode: {}".format(admin_mode))
    if admin_mode == "enabled" and oper_mode == "unready":
        click.echo("Kdump operational mode: Ready after reboot")
    else:
        click.echo("Kdump operational mode: {}".format(oper_mode))

    mem_config = get_kdump_memory_config()
    click.echo("Kdump memory researvation: {}".format(mem_config))

    num_files_config = get_kdump_num_files()
    click.echo("Maximum number of Kdump files: {}".format(num_files_config))


def get_kdump_core_files():
    """Retrieves the kernel core dump files from directory /var/crash/.

    Args:
      None.

    Returns:
      dump_file_list: A list contains kernel core dump files or error messages.
    """
    find_core_dump_files = "find /var/crash -name 'kdump.*'"
    dump_file_list = []
    command_stdout, command_stderr, exit_code = clicommon.run_command(find_core_dump_files,
                                                                      return_cmd=True)
    if exit_code != 0:
        dump_file_list.append("Failed to retrieve kernel core dump files!")

    if not command_stdout.splitlines():
        dump_file_list.append("No kernel core dump file available!")
    else:
        dump_file_list = command_stdout.splitlines()

    return dump_file_list


def get_kdump_dmesg_files():
    """Retrieves the kernel dmesg files from directory /var/crash/.

    Args:
      None.

    Returns:
      dmesg_file_list: A list contains kernel dmesg files or error messages.
    """
    find_dmesg_files = "find /var/crash -name 'dmesg.*'"
    dmesg_file_list = []
    command_stdout, command_stderr, exit_code = clicommon.run_command(find_dmesg_files,
                                                                      return_cmd=True)
    if exit_code != 0:
        dmesg_file_list.append("Failed to retrieve kernel dmesg files!")

    if not command_stdout.splitlines():
        dmesg_file_list.append("No kernel dmesg file available!")
    else:
        dmesg_file_list = command_stdout.splitlines()

    return dmesg_file_list


@kdump.command(name="files", short_help="Show kernel core dump and dmesg files")
def files():
    core_file_list = []
    dmesg_file_list = []
    body = []

    core_file_list = get_kdump_core_files()
    dmesg_file_list = get_kdump_dmesg_files()

    header = ["Kernel core dump files", "Kernel dmesg files"]

    for (core_file, dmesg_file) in itertools.zip_longest(core_file_list, dmesg_file_list, fillvalue=""):
        body.append([core_file, dmesg_file])

    click.echo(tabulate(body, header))


@kdump.command()
@click.argument('record', required=True)
@click.argument('lines', metavar='<lines>', required=False)
def log(record, lines):
    """Show kdump kernel core dump file kernel log"""
    cmd = "sonic-kdump-config --file {}".format(record)
    if lines is not None:
        cmd += " --lines {}".format(lines)

    clicommon.run_command(cmd)
