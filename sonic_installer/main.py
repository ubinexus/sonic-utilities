#! /usr/bin/python -u

import sys
import click
import urllib
import subprocess

MACHINE_PATH = '/host'
IMAGE_PREFIX = 'SONiC-OS'
IMAGE_DIR_PREFIX = 'image'
DEFAULT_IMAGE_PATH = '/tmp/sonic_installer'


# Run bash command and print output to stdout
def run_command(command, pager=False):
    click.echo(click.style("Command: ", fg='cyan') + click.style(command, fg='green'))
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    if pager is True:
        click.echo_via_pager(p.stdout.read())
    else:
        click.echo(p.stdout.read())
    p.wait()
    if p.returncode != 0:
        sys.exit(p.returncode)


# Returns list of installed images
def get_installed_images():
    images = []
    config = open(MACHINE_PATH + '/grub/grub.cfg', 'r')
    for line in config:
        if line.startswith('menuentry'):
            image = line.split()[1].strip("'")
            if image != 'ONIE':
                images.append(image)
    config.close()
    return images


# Returns name of current image
def get_current_image():
    images = get_installed_images()
    current = ''
    cmdline = open('/proc/cmdline', 'r')
    for line in cmdline:
        for image in images:
            image_dir = image.replace(IMAGE_PREFIX, IMAGE_DIR_PREFIX)
            if line.find(image_dir):
                current = image
                break
    cmdline.close()
    return current


# Callback for confirmation prompt. Aborts if user enters "n"
def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


# Main entrypoint
@click.group()
def cli():
    """ SONiC image installation manager """
    pass


# Install image
@cli.command()
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
        expose_value=False, prompt='New image will be installed, continue?')
@click.argument('url')
def install(url):
    """ Install image from local binary or URL"""
    cleanup_image = False
    if url.startswith('http://') or url.startswith('https://'):
        click.echo('Downloading image...')
        urllib.urlretrieve(url, DEFAULT_IMAGE_PATH)
        image_path = DEFAULT_IMAGE_PATH
    else:
        image_path = url

    run_command("sh " + image_path)
    run_command("cp /etc/sonic/minigraph.xml /host/")
    run_command('grub-set-default --boot-directory=' + MACHINE_PATH + ' 0')
    click.echo('Done')


# List installed images
@cli.command()
def list():
    """ Print installed images """
    for image in get_installed_images():
        click.echo(image)


# Set default image for boot
@cli.command()
@click.argument('image')
def set_default(image):
    """ Choose image to boot from by default """
    images = get_installed_images()
    if image not in images:
        click.echo('Image does not exist')
        sys.exit(1)
    command = 'grub-set-default --boot-directory=' + MACHINE_PATH + ' ' + str(images.index(image))
    run_command(command)


# Set image for next boot
@cli.command()
@click.argument('image')
def set_next_boot(image):
    """ Choose image for next reboot (one time action) """
    images = get_installed_images()
    if image not in images:
        click.echo('Image does not exist')
        sys.exit(1)
    command = 'grub-reboot --boot-directory=' + MACHINE_PATH + ' ' + str(images.index(image))
    run_command(command)


# Uninstall image
@cli.command()
@click.option('-y', '--yes', is_flag=True, callback=abort_if_false,
        expose_value=False, prompt='Image will be removed, continue?')
@click.argument('image')
def remove(image):
    """ Uninstall image """
    images = get_installed_images()
    current = get_current_image()
    if image not in images:
        click.echo('Image does not exist')
        sys.exit(1)
    if image == current:
        click.echo('Cannot remove current image')
        sys.exit(1)

    click.echo('Updating GRUB...')
    config = open(MACHINE_PATH + '/grub/grub.cfg', 'r')
    new_config = ''
    entry_found = False
    for line in config:
        if not entry_found and image in line:
            entry_found = True
        elif entry_found and line.startswith('}'):
            click.echo('FOUND!!!')
            entry_found = False
        elif not entry_found:
            new_config += line
    config.close()
    config = open(MACHINE_PATH + '/grub/grub.cfg', 'w')
    config.write(new_config)
    config.close()

    image_dir = image.replace(IMAGE_PREFIX, IMAGE_DIR_PREFIX)
    run_command('rm -rf ' + MACHINE_PATH + '/' + image_dir)
    run_command('grub-set-default --boot-directory=' + MACHINE_PATH + ' 0')
    click.echo('Done')


if __name__ == '__main__':
    if os.geteuid() != 0:
        exit("Root privileges required for this operation")
    cli()
