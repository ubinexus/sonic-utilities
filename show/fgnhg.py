import ipaddress
from collections import OrderedDict

import click
import utilities_common.cli as clicommon
from swsscommon.swsscommon import SonicV2Connector, ConfigDBConnector
from tabulate import tabulate


@click.group(cls=clicommon.AliasedGroup)
def fgnhg():
    """Show FGNHG information"""
    pass


@fgnhg.command()
@click.argument('nhg', required=False)
def active_hops(nhg):
    config_db = ConfigDBConnector()
    config_db.connect()

    fg_nhg_alias_dict = config_db.get_table('FG_NHG')
    fg_nhg_alias_list = []
    for alias, value in fg_nhg_alias_dict.items():
        fg_nhg_alias_list.append(alias)

    state_db = SonicV2Connector(host='127.0.0.1')
    state_db.connect(state_db.STATE_DB, False)  # Make one attempt only STATE_DB

    TABLE_NAME_SEPARATOR = '|'
    prefix = 'FG_ROUTE_TABLE' + TABLE_NAME_SEPARATOR
    _hash = '{}{}'.format(prefix, '*')
    table_keys = []
    table_keys = state_db.keys(state_db.STATE_DB, _hash)
    t_dict = {}
    header = ["FG_NHG_PREFIX", "Active Next Hops"]
    table = []
    output_dict = {}

    if nhg is None:
        for nhg_prefix in table_keys:
            t_dict = state_db.get_all(state_db.STATE_DB, nhg_prefix)
            vals = sorted(set([val for val in t_dict.values()]))
            for nh_ip in vals:
                if nhg_prefix in output_dict:
                    output_dict[nhg_prefix].append(nh_ip.split("@")[0])
                else:
                    output_dict[nhg_prefix] = [nh_ip.split("@")[0]]

            nhg_prefix_report = (nhg_prefix.split("|")[1])
            formatted_nhps = ','.replace(',', ', ').join(output_dict[nhg_prefix])
            table.append([nhg_prefix_report, formatted_nhps])

        click.echo(tabulate(table, header))

    else:
        header = ["Alias", "Active Next Hops"]
        fg_nhg_member_table = config_db.get_table('FG_NHG_MEMBER')
        alias_list = []
        nexthop_alias = {}
        nhg_prefix_report = nhg
        output_list = []

        for nexthop, nexthop_metadata in fg_nhg_member_table.items():
            alias_list.append(nexthop_metadata['FG_NHG'])
            nexthop_alias[nexthop] = nexthop_metadata['FG_NHG']

        if nhg not in alias_list:
            print ("Please provide a valid NHG alias")

        else:
            for nhg_prefix in table_keys:
                t_dict = state_db.get_all(state_db.STATE_DB, nhg_prefix)
                vals = sorted(set([val for val in t_dict.values()]))

                for nh_ip in vals:
                    if nexthop_alias[nh_ip.split("@")[0]] == nhg:
                        output_list.append(nh_ip)

                output_list = sorted(output_list)


            formatted_output_list = ','.replace(',', ', ').join(output_list)
            table.append([nhg_prefix_report, formatted_output_list])

            click.echo(tabulate(table, header))

@fgnhg.command()
@click.argument('nhg', required=False)
def hash_view(nhg):
    config_db = ConfigDBConnector()
    config_db.connect()

    fg_nhg_alias_dict = config_db.get_table('FG_NHG')
    fg_nhg_alias_list = []
    for alias, value in fg_nhg_alias_dict.items():
        fg_nhg_alias_list.append(alias)

    state_db = SonicV2Connector(host='127.0.0.1')
    state_db.connect(state_db.STATE_DB, False)  # Make one attempt only STATE_DB

    TABLE_NAME_SEPARATOR = '|'
    prefix = 'FG_ROUTE_TABLE' + TABLE_NAME_SEPARATOR
    _hash = '{}{}'.format(prefix, '*')
    table_keys = []
    table_keys = state_db.keys(state_db.STATE_DB, _hash)
    t_dict = {}
    header = ["FG_NHG_PREFIX", "Next Hop", "Hash buckets"]
    table = []
    output_dict = {}
    bank_dict = {}

    if nhg is None:
        for nhg_prefix in table_keys:
            bank_dict = {}
            t_dict = state_db.get_all(state_db.STATE_DB, nhg_prefix)
            vals = sorted(set([val for val in t_dict.values()]))

            for nh_ip in vals:
                bank_ids = sorted([int(k) for k, v in t_dict.items() if v == nh_ip])

                bank_ids = [str(x) for x in bank_ids]

                if nhg_prefix in output_dict:
                    output_dict[nhg_prefix].append(nh_ip.split("@")[0])
                else:
                    output_dict[nhg_prefix] = [nh_ip.split("@")[0]]
                bank_dict[nh_ip.split("@")[0]] = bank_ids

            bank_dict = OrderedDict(sorted(bank_dict.items()))
            nhg_prefix_report = (nhg_prefix.split("|")[1])

            for nhip, val in bank_dict.items():
                formatted_banks = ','.replace(',', ', ').join(bank_dict[nhip])
                table.append([nhg_prefix_report, nhip, formatted_banks])

        click.echo(tabulate(table, header))

    else:
        header = ["Alias", "Next Hop", "Hash buckets"]
        fg_nhg_member_table = config_db.get_table('FG_NHG_MEMBER')
        alias_list = []
        nexthop_alias = {}

        for nexthop, nexthop_metadata in fg_nhg_member_table.items():
            alias_list.append(nexthop_metadata['FG_NHG'])
            nexthop_alias[nexthop] = nexthop_metadata['FG_NHG']

        if nhg not in alias_list:
            print ("Please provide a valid NHG alias")

        else:
            for nhg_prefix in table_keys:
                bank_dict = {}
                t_dict = state_db.get_all(state_db.STATE_DB, nhg_prefix)
                vals = sorted(set([val for val in t_dict.values()]))

                for nh_ip in vals:
                    bank_ids = sorted([int(k) for k, v in t_dict.items() if v == nh_ip])

                    bank_ids = [str(x) for x in bank_ids]

                    if nhg_prefix in output_dict:
                        output_dict[nhg_prefix].append(nh_ip.split("@")[0])
                    else:
                        output_dict[nhg_prefix] = [nh_ip.split("@")[0]]
                    bank_dict[nh_ip.split("@")[0]] = bank_ids

                bank_dict = OrderedDict(sorted(bank_dict.items()))
                output_bank_dict = {}
                for nexthop, banks  in bank_dict.items():
                    if nexthop_alias[nexthop] == nhg:
                        output_bank_dict[nexthop] = banks

                nhg_prefix_report = nhg

                for nhip, val in output_bank_dict.items():
                    formatted_banks = ','.replace(',', ', ').join(bank_dict[nhip])
                    table.append([nhg_prefix_report, nhip, formatted_banks])

            click.echo(tabulate(table, header))
