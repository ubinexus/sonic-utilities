from __future__ import print_function

import os
import re
import subprocess
import sys
import time

# TODO: Remove this check once we no longer support Python 2
if sys.version_info.major == 3:
    import configparser
    from urllib.request import urlopen, urlretrieve
else:
    import ConfigParser as configparser
    from urllib import urlopen, urlretrieve

import click
from sonic_py_common import logger
from swsscommon.swsscommon import SonicV2Connector

from .bootloader import get_bootloader
from .common import run_command, run_command_or_raise
from .exception import SonicRuntimeException

SYSLOG_IDENTIFIER = "sonic-installer"

# Global Config object
_config = None

# Global logger instance
log = logger.Logger(SYSLOG_IDENTIFIER)

# This is from the aliases example:
# https://github.com/pallets/click/blob/57c6f09611fc47ca80db0bd010f05998b3c0aa95/examples/aliases/aliases.py
class Config(object):
    """Object to hold CLI config"""

    def __init__(self):
        self.path = os.getcwd()
        self.aliases = {}

    def read_config(self, filename):
        parser = configparser.RawConfigParser()
        parser.read([filename])
        try:
            self.aliases.update(parser.items('aliases'))
        except configparser.NoSectionError:
            pass


class AliasedGroup(click.Group):
    """This subclass of click.Group supports abbreviations and
       looking up aliases in a config file with a bit of magic.
    """

    def get_command(self, ctx, cmd_name):
        global _config

        # If we haven't instantiated our global config, do it now and load current config
        if _config is None:
            _config = Config()

            # Load our config file
            cfg_file = os.path.join(os.path.dirname(__file__), 'aliases.ini')
            _config.read_config(cfg_file)

        # Try to get builtin commands as normal
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        # No builtin found. Look up an explicit command alias in the config
        if cmd_name in _config.aliases:
            actual_cmd = _config.aliases[cmd_name]
            return click.Group.get_command(self, ctx, actual_cmd)

        # Alternative option: if we did not find an explicit alias we
        # allow automatic abbreviation of the command.  "status" for
        # instance will match "st".  We only allow that however if
        # there is only one command.
        matches = [x for x in self.list_commands(ctx)
                   if x.lower().startswith(cmd_name.lower())]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


#
# Helper functions
#

_start_time = None
_last_time = None
def reporthook(count, block_size, total_size):
    global _start_time, _last_time
    cur_time = int(time.time())
    if count == 0:
        _start_time = cur_time
        _last_time = cur_time
        return

    if cur_time == _last_time:
        return

    _last_time = cur_time

    duration = cur_time - _start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = int(count * block_size * 100 / total_size)
    time_left = (total_size - progress_size) / speed / 1024
    sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds left...   " %
                     (percent, progress_size / (1024 * 1024), speed, time_left))
    sys.stdout.flush()


# TODO: Embed tag name info into docker image meta data at build time,
# and extract tag name from docker image file.
def get_docker_tag_name(image):
    # Try to get tag name from label metadata
    cmd = "docker inspect --format '{{.ContainerConfig.Labels.Tag}}' " + image
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (out, _) = proc.communicate()
    if proc.returncode != 0:
        return "unknown"
    tag = out.rstrip()
    if tag == "<no value>":
        return "unknown"
    return tag


# Function which validates whether a given URL specifies an existent file
# on a reachable remote machine. Will abort the current operation if not
def validate_url_or_abort(url):
    # Attempt to retrieve HTTP response code
    try:
        urlfile = urlopen(url)
        response_code = urlfile.getcode()
        urlfile.close()
    except IOError:
        response_code = None

    if not response_code:
        click.echo("Did not receive a response from remote machine. Aborting...")
        raise click.Abort()
    else:
        # Check for a 4xx response code which indicates a nonexistent URL
        if response_code / 100 == 4:
            click.echo("Image file not found on remote machine. Aborting...")
            raise click.Abort()


# Callback for confirmation prompt. Aborts if user enters "n"
def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


def get_container_image_name(container_name):
    # example image: docker-lldp-sv2:latest
    cmd = "docker inspect --format '{{.Config.Image}}' " + container_name
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (out, _) = proc.communicate()
    if proc.returncode != 0:
        sys.exit(proc.returncode)
    image_latest = out.rstrip()

    # example image_name: docker-lldp-sv2
    cmd = "echo " + image_latest + " | cut -d ':' -f 1"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    image_name = proc.stdout.read().rstrip()
    return image_name


def get_container_image_id(image_tag):
    # TODO: extract commond docker info fetching functions
    # this is image_id for image with tag, like 'docker-teamd:latest'
    cmd = "docker images --format '{{.ID}}' " + image_tag
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    image_id = proc.stdout.read().rstrip()
    return image_id


def get_container_image_id_all(image_name):
    # All images id under the image name like 'docker-teamd'
    cmd = "docker images --format '{{.ID}}' " + image_name
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    image_id_all = proc.stdout.read()
    image_id_all = image_id_all.splitlines()
    image_id_all = set(image_id_all)
    return image_id_all


def hget_warm_restart_table(db_name, table_name, warm_app_name, key):
    db = SonicV2Connector()
    db.connect(db_name, False)
    _hash = table_name + db.get_db_separator(db_name) + warm_app_name
    client = db.get_redis_client(db_name)
    return client.hget(_hash, key)


def hdel_warm_restart_table(db_name, table_name, warm_app_name, key):
    db = SonicV2Connector()
    db.connect(db_name, False)
    _hash = table_name + db.get_db_separator(db_name) + warm_app_name
    client = db.get_redis_client(db_name)
    return client.hdel(_hash, key)


def print_deprecation_warning(deprecated_cmd_or_subcmd, new_cmd_or_subcmd):
    click.secho("Warning: '{}' {}command is deprecated and will be removed in the future"
                .format(deprecated_cmd_or_subcmd, "" if deprecated_cmd_or_subcmd == "sonic_installer" else "sub"),
                fg="red", err=True)
    click.secho("Please use '{}' instead".format(new_cmd_or_subcmd), fg="red", err=True)

def update_sonic_environment(click, binary_image_version):
    """Prepare sonic environment variable using incoming image template file. If incoming image template does not exist
       use current image template file.
    """
    def mount_next_image_fs(squashfs_path, mount_point):
        run_command_or_raise(["mkdir", "-p", mount_point])
        run_command_or_raise(["mount", "-t", "squashfs", squashfs_path, mount_point])

    def umount_next_image_fs(mount_point):
        run_command_or_raise(["umount", "-rf", mount_point])
        run_command_or_raise(["rm", "-rf", mount_point])

    SONIC_ENV_TEMPLATE_FILE = os.path.join("usr", "share", "sonic", "templates", "sonic-environment.j2")
    SONIC_VERSION_YML_FILE = os.path.join("etc", "sonic", "sonic_version.yml")

    sonic_version = re.sub("SONiC-OS-", '', binary_image_version)
    new_image_dir = os.path.join('/', "host", "image-{0}".format(sonic_version))
    new_image_squashfs_path = os.path.join(new_image_dir, "fs.squashfs")
    new_image_mount = os.path.join('/', "tmp", "image-{0}-fs".format(sonic_version))
    env_dir = os.path.join(new_image_dir, "sonic-config")
    env_file = os.path.join(env_dir, "sonic-environment")

    try:
        mount_next_image_fs(new_image_squashfs_path, new_image_mount)

        next_sonic_env_template_file = os.path.join(new_image_mount, SONIC_ENV_TEMPLATE_FILE)
        next_sonic_version_yml_file = os.path.join(new_image_mount, SONIC_VERSION_YML_FILE)

        sonic_env = run_command_or_raise([
                "sonic-cfggen",
                "-d",
                "-y",
                next_sonic_version_yml_file,
                "-t",
                next_sonic_env_template_file,
        ])
        os.mkdir(env_dir, 0o755)
        with open(env_file, "w+") as ef:
            print(sonic_env, file=ef)
        os.chmod(env_file, 0o644)
    except SonicRuntimeException as ex:
        click.secho("Warning: SONiC environment variables are not supported for this image: {0}".format(str(ex)),
                    fg="red", err=True)
        if os.path.exists(env_file):
            os.remove(env_file)
            os.rmdir(env_dir)
    finally:
        umount_next_image_fs(new_image_mount)

# Main entrypoint
@click.group(cls=AliasedGroup)
def sonic_installer():
    """ SONiC image installation manager """
    if os.geteuid() != 0:
        exit("Root privileges required for this operation")

    # Warn the user if they are calling the deprecated version of the command (with an underscore instead of a hyphen)
    if os.path.basename(sys.argv[0]) == "sonic_installer":
        print_deprecation_warning("sonic_installer", "sonic-installer")


# Install image
@sonic_installer.command('install')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False, prompt='New image will be installed, continue?')
@click.option('-f', '--force', is_flag=True,
              help="Force installation of an image of a type which differs from that of the current running image")
@click.option('--skip_migration', is_flag=True,
              help="Do not migrate current configuration to the newly installed image")
@click.argument('url')
def install(url, force, skip_migration=False):
    """ Install image from local binary or URL"""
    bootloader = get_bootloader()

    if url.startswith('http://') or url.startswith('https://'):
        click.echo('Downloading image...')
        validate_url_or_abort(url)
        try:
            urlretrieve(url, bootloader.DEFAULT_IMAGE_PATH, reporthook)
            click.echo('')
        except Exception as e:
            click.echo("Download error", e)
            raise click.Abort()
        image_path = bootloader.DEFAULT_IMAGE_PATH
    else:
        image_path = os.path.join("./", url)

    binary_image_version = bootloader.get_binary_image_version(image_path)
    if not binary_image_version:
        click.echo("Image file does not exist or is not a valid SONiC image file")
        raise click.Abort()

    # Is this version already installed?
    if binary_image_version in bootloader.get_installed_images():
        click.echo("Image {} is already installed. Setting it as default...".format(binary_image_version))
        if not bootloader.set_default_image(binary_image_version):
            click.echo('Error: Failed to set image as default')
            raise click.Abort()
    else:
        # Verify that the binary image is of the same type as the running image
        if not bootloader.verify_binary_image(image_path) and not force:
            click.echo("Image file '{}' is of a different type than running image.\n".format(url) +
                "If you are sure you want to install this image, use -f|--force.\n" +
                "Aborting...")
            raise click.Abort()

        click.echo("Installing image {} and setting it as default...".format(binary_image_version))
        bootloader.install_image(image_path)
        # Take a backup of current configuration
        if skip_migration:
            click.echo("Skipping configuration migration as requested in the command option.")
        else:
            run_command('config-setup backup')

        update_sonic_environment(click, binary_image_version)

    # Finally, sync filesystem
    run_command("sync;sync;sync")
    run_command("sleep 3")  # wait 3 seconds after sync
    click.echo('Done')


# List installed images
@sonic_installer.command('list')
def list_command():
    """ Print installed images """
    bootloader = get_bootloader()
    images = bootloader.get_installed_images()
    curimage = bootloader.get_current_image()
    nextimage = bootloader.get_next_image()
    click.echo("Current: " + curimage)
    click.echo("Next: " + nextimage)
    click.echo("Available: ")
    for image in images:
        click.echo(image)


# Set default image for boot
@sonic_installer.command('set-default')
@click.argument('image')
def set_default(image):
    """ Choose image to boot from by default """
    # Warn the user if they are calling the deprecated version of the subcommand (with an underscore instead of a hyphen)
    if "set_default" in sys.argv:
        print_deprecation_warning("set_default", "set-default")

    bootloader = get_bootloader()
    if image not in bootloader.get_installed_images():
        click.echo('Error: Image does not exist')
        raise click.Abort()
    bootloader.set_default_image(image)


# Set image for next boot
@sonic_installer.command('set-next-boot')
@click.argument('image')
def set_next_boot(image):
    """ Choose image for next reboot (one time action) """
    # Warn the user if they are calling the deprecated version of the subcommand (with underscores instead of hyphens)
    if "set_next_boot" in sys.argv:
        print_deprecation_warning("set_next_boot", "set-next-boot")

    bootloader = get_bootloader()
    if image not in bootloader.get_installed_images():
        click.echo('Error: Image does not exist')
        sys.exit(1)
    bootloader.set_next_image(image)


# Uninstall image
@sonic_installer.command('remove')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False, prompt='Image will be removed, continue?')
@click.argument('image')
def remove(image):
    """ Uninstall image """
    bootloader = get_bootloader()
    images = bootloader.get_installed_images()
    current = bootloader.get_current_image()
    if image not in images:
        click.echo('Image does not exist')
        sys.exit(1)
    if image == current:
        click.echo('Cannot remove current image')
        sys.exit(1)
    # TODO: check if image is next boot or default boot and fix these
    bootloader.remove_image(image)


# Retrieve version from binary image file and print to screen
@sonic_installer.command('binary-version')
@click.argument('binary_image_path')
def binary_version(binary_image_path):
    """ Get version from local binary image file """
    # Warn the user if they are calling the deprecated version of the subcommand (with an underscore instead of a hyphen)
    if "binary_version" in sys.argv:
        print_deprecation_warning("binary_version", "binary-version")

    bootloader = get_bootloader()
    version = bootloader.get_binary_image_version(binary_image_path)
    if not version:
        click.echo("Image file does not exist or is not a valid SONiC image file")
        sys.exit(1)
    else:
        click.echo(version)


# Remove installed images which are not current and next
@sonic_installer.command('cleanup')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False, prompt='Remove images which are not current and next, continue?')
def cleanup():
    """ Remove installed images which are not current and next """
    bootloader = get_bootloader()
    images = bootloader.get_installed_images()
    curimage = bootloader.get_current_image()
    nextimage = bootloader.get_next_image()
    image_removed = 0
    for image in images:
        if image != curimage and image != nextimage:
            click.echo("Removing image %s" % image)
            bootloader.remove_image(image)
            image_removed += 1

    if image_removed == 0:
        click.echo("No image(s) to remove")


DOCKER_CONTAINER_LIST = [
    "bgp",
    "dhcp_relay",
    "lldp",
    "nat",
    "pmon",
    "radv",
    "restapi",
    "sflow",
    "snmp",
    "swss",
    "syncd",
    "teamd",
    "telemetry"
]

# Upgrade docker image
@sonic_installer.command('upgrade-docker')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False, prompt='New docker image will be installed, continue?')
@click.option('--cleanup_image', is_flag=True, help="Clean up old docker image")
@click.option('--skip_check', is_flag=True, help="Skip task check for docker upgrade")
@click.option('--tag', type=str, help="Tag for the new docker image")
@click.option('--warm', is_flag=True, help="Perform warm upgrade")
@click.argument('container_name', metavar='<container_name>', required=True,
                type=click.Choice(DOCKER_CONTAINER_LIST))
@click.argument('url')
def upgrade_docker(container_name, url, cleanup_image, skip_check, tag, warm):
    """ Upgrade docker image from local binary or URL"""
    # Warn the user if they are calling the deprecated version of the subcommand (with an underscore instead of a hyphen)
    if "upgrade_docker" in sys.argv:
        print_deprecation_warning("upgrade_docker", "upgrade-docker")

    image_name = get_container_image_name(container_name)
    image_latest = image_name + ":latest"
    image_id_previous = get_container_image_id(image_latest)

    DEFAULT_IMAGE_PATH = os.path.join("/tmp/", image_name)
    if url.startswith('http://') or url.startswith('https://'):
        click.echo('Downloading image...')
        validate_url_or_abort(url)
        try:
            urlretrieve(url, DEFAULT_IMAGE_PATH, reporthook)
        except Exception as e:
            click.echo("Download error", e)
            raise click.Abort()
        image_path = DEFAULT_IMAGE_PATH
    else:
        image_path = os.path.join("./", url)

    # Verify that the local file exists and is a regular file
    # TODO: Verify the file is a *proper Docker image file*
    if not os.path.isfile(image_path):
        click.echo("Image file '{}' does not exist or is not a regular file. Aborting...".format(image_path))
        raise click.Abort()

    warm_configured = False
    # warm restart enable/disable config is put in stateDB, not persistent across cold reboot, not saved to config_DB.json file
    state_db = SonicV2Connector(host='127.0.0.1')
    state_db.connect(state_db.STATE_DB, False)
    TABLE_NAME_SEPARATOR = '|'
    prefix = 'WARM_RESTART_ENABLE_TABLE' + TABLE_NAME_SEPARATOR
    _hash = '{}{}'.format(prefix, container_name)
    if state_db.get(state_db.STATE_DB, _hash, "enable") == "true":
        warm_configured = True
    state_db.close(state_db.STATE_DB)

    if container_name == "swss" or container_name == "bgp" or container_name == "teamd":
        if warm_configured is False and warm:
            run_command("config warm_restart enable %s" % container_name)

    # Fetch tag of current running image
    tag_previous = get_docker_tag_name(image_latest)
    # Load the new image beforehand to shorten disruption time
    run_command("docker load < %s" % image_path)
    warm_app_names = []
    # warm restart specific procssing for swss, bgp and teamd dockers.
    if warm_configured is True or warm:
        # make sure orchagent is in clean state if swss is to be upgraded
        if container_name == "swss":
            skipPendingTaskCheck = ""
            if skip_check:
                skipPendingTaskCheck = " -s"

            cmd = "docker exec -i swss orchagent_restart_check -w 2000 -r 5 " + skipPendingTaskCheck

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()
            if proc.returncode != 0:
                if not skip_check:
                    click.echo("Orchagent is not in clean state, RESTARTCHECK failed")
                    # Restore orignal config before exit
                    if warm_configured is False and warm:
                        run_command("config warm_restart disable %s" % container_name)
                    # Clean the image loaded earlier
                    image_id_latest = get_container_image_id(image_latest)
                    run_command("docker rmi -f %s" % image_id_latest)
                    # Re-point latest tag to previous tag
                    run_command("docker tag %s:%s %s" % (image_name, tag_previous, image_latest))

                    sys.exit(proc.returncode)
                else:
                    click.echo("Orchagent is not in clean state, upgrading it anyway")
            else:
                click.echo("Orchagent is in clean state and frozen for warm upgrade")

            warm_app_names = ["orchagent", "neighsyncd"]

        elif container_name == "bgp":
            # Kill bgpd to restart the bgp graceful restart procedure
            click.echo("Stopping bgp ...")
            run_command("docker exec -i bgp pkill -9 zebra")
            run_command("docker exec -i bgp pkill -9 bgpd")
            warm_app_names = ["bgp"]
            click.echo("Stopped  bgp ...")

        elif container_name == "teamd":
            click.echo("Stopping teamd ...")
            # Send USR1 signal to all teamd instances to stop them
            # It will prepare teamd for warm-reboot
            run_command("docker exec -i teamd pkill -USR1 teamd > /dev/null")
            warm_app_names = ["teamsyncd"]
            click.echo("Stopped  teamd ...")

        # clean app reconcilation state from last warm start if exists
        for warm_app_name in warm_app_names:
            hdel_warm_restart_table("STATE_DB", "WARM_RESTART_TABLE", warm_app_name, "state")

    run_command("docker kill %s > /dev/null" % container_name)
    run_command("docker rm %s " % container_name)
    if tag is None:
        # example image: docker-lldp-sv2:latest
        tag = get_docker_tag_name(image_latest)
    run_command("docker tag %s:latest %s:%s" % (image_name, image_name, tag))
    run_command("systemctl restart %s" % container_name)

    # All images id under the image name
    image_id_all = get_container_image_id_all(image_name)

    # this is image_id for image with "latest" tag
    image_id_latest = get_container_image_id(image_latest)

    for id in image_id_all:
        if id != image_id_latest:
            # Unless requested, the previoud docker image will be preserved
            if not cleanup_image and id == image_id_previous:
                continue
            run_command("docker rmi -f %s" % id)

    exp_state = "reconciled"
    state = ""
    # post warm restart specific procssing for swss, bgp and teamd dockers, wait for reconciliation state.
    if warm_configured is True or warm:
        count = 0
        for warm_app_name in warm_app_names:
            state = ""
            # Wait up to 180 seconds for reconciled state
            while state != exp_state and count < 90:
                sys.stdout.write("\r  {}: ".format(warm_app_name))
                sys.stdout.write("[%-s" % ('='*count))
                sys.stdout.flush()
                count += 1
                time.sleep(2)
                state = hget_warm_restart_table("STATE_DB", "WARM_RESTART_TABLE", warm_app_name, "state")
                log.log_notice("%s reached %s state" % (warm_app_name, state))
            sys.stdout.write("]\n\r")
            if state != exp_state:
                click.echo("%s failed to reach %s state" % (warm_app_name, exp_state))
                log.log_error("%s failed to reach %s state" % (warm_app_name, exp_state))
    else:
        exp_state = ""  # this is cold upgrade

    # Restore to previous cold restart setting
    if warm_configured is False and warm:
        if container_name == "swss" or container_name == "bgp" or container_name == "teamd":
            run_command("config warm_restart disable %s" % container_name)

    if state == exp_state:
        click.echo('Done')
    else:
        click.echo('Failed')
        sys.exit(1)


# rollback docker image
@sonic_installer.command('rollback-docker')
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
              expose_value=False, prompt='Docker image will be rolled back, continue?')
@click.argument('container_name', metavar='<container_name>', required=True,
                type=click.Choice(DOCKER_CONTAINER_LIST))
def rollback_docker(container_name):
    """ Rollback docker image to previous version"""
    # Warn the user if they are calling the deprecated version of the subcommand (with an underscore instead of a hyphen)
    if "rollback_docker" in sys.argv:
        print_deprecation_warning("rollback_docker", "rollback-docker")

    image_name = get_container_image_name(container_name)
    # All images id under the image name
    image_id_all = get_container_image_id_all(image_name)
    if len(image_id_all) != 2:
        click.echo("Two images required, but there are '{}' images for '{}'. Aborting...".format(len(image_id_all), image_name))
        raise click.Abort()

    image_latest = image_name + ":latest"
    image_id_previous = get_container_image_id(image_latest)

    version_tag = ""
    for id in image_id_all:
        if id != image_id_previous:
            version_tag = get_docker_tag_name(id)

    # make previous image as latest
    run_command("docker tag %s:%s %s:latest" % (image_name, version_tag, image_name))
    if container_name == "swss" or container_name == "bgp" or container_name == "teamd":
        click.echo("Cold reboot is required to restore system state after '{}' rollback !!".format(container_name))
    else:
        run_command("systemctl restart %s" % container_name)

    click.echo('Done')

# verify the next image
@sonic_installer.command('verify-next-image')
def verify_next_image():
    """ Verify the next image for reboot"""
    bootloader = get_bootloader()
    if not bootloader.verify_next_image():
        click.echo('Image verification failed')
        sys.exit(1)
    click.echo('Image successfully verified')

if __name__ == '__main__':
    sonic_installer()
