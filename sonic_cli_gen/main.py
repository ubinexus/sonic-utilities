#!/usr/bin/env python

import click
from sonic_cli_gen.generator import CliGenerator

@click.group()
@click.pass_context
def cli(ctx):
    """ SONiC CLI generator """
    pass

@cli.command()
@click.argument('yang_model_name')
@click.pass_context
def generate_config(ctx, yang_model_name):
    """ Generate CLI plugin (click) for 'config' CLI group. """
    gen = CliGenerator()
    gen.generate_cli_plugin(cli_group='config', plugin_name=yang_model_name)

@cli.command()
@click.argument('yang_model_name')
@click.pass_context
def generate_show(ctx, yang_model_name):
    """ Generate CLI plugin (click) for 'show' CLI group. """
    gen = CliGenerator()
    gen.generate_cli_plugin(cli_group='show', plugin_name=yang_model_name)

if __name__ == '__main__':
    cli()