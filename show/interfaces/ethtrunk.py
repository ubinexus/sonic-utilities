import click
import utilities_common.cli as clicommon
from natsort import natsorted
from tabulate import tabulate
import utilities_common.multi_asic as multi_asic_util
from utilities_common.constants import ETH_TRUNK_OBJ

"""
    Script to show ETHTRUNK and ETHTRUNK member status in a summary view
    Example of the output:
    acsadmin@sonic:~$ teamshow
    Flags: Up - up, Dw - down, N/A - Not Available,
           W - working, D - protect, * - not synced
     No.  Team Dev        Status    Mtu    Ports
    -----  -------------  ----------  ---------------------------
        0  EthTrunk0      Up     8100     Ethernet0(W) Ethernet4(P)
        8  EthTrunk8      Dw     8100     Ethernet8(P) Ethernet12(W)
       16  EthTrunk16     Up     8100     Ethernet20(W)

"""

ETH_TRUNK_APPL_TABLE_PREFIX = "ETHTRUNK_TABLE:"
ETH_TRUNK_CFG_TABLE_PREFIX = "ETHTRUNK|"
ETH_TRUNK_STATE_TABLE_PREFIX = "ETHTRUNK_TABLE|"
ETH_TRUNK_STATUS_FIELD = "oper_status"

ETH_TRUNK_MEMBER_APPL_TABLE_PREFIX = "ETHTRUNK_MEMBER_TABLE:"
ETH_TRUNK_MEMBER_STATE_TABLE_PREFIX = "ETHTRUNK_MEMBER_TABLE|"
ETH_TRUNK_MEMBER_STATUS_FIELD = "status"

class Teamshow(object):
    def __init__(self, namespace_option, display_option):
        self.teams = []
        self.teamsraw = {}
        self.summary = {}
        self.err = None
        self.db = None
        self.multi_asic = multi_asic_util.MultiAsic(display_option, namespace_option)

    @multi_asic_util.run_on_multi_asic
    def get_teams_info(self):
        self.get_ethtrunk_names()
        self.get_teamdctl()
        self.get_teamshow_result()

    def get_ethtrunk_names(self):
        """
            Get the ethtrunk names from database.
        """
        self.teams = []
        team_keys = self.db.keys(self.db.CONFIG_DB, ETH_TRUNK_CFG_TABLE_PREFIX+"*")
        if team_keys is None:
            return
        for key in team_keys:
            team_name = key[len(ETH_TRUNK_CFG_TABLE_PREFIX):]
            if self.multi_asic.skip_display(ETH_TRUNK_OBJ, team_name) is True:
                continue
            self.teams.append(team_name)

    def get_ethtrunk_status(self, eth_trunk_name):
        """
            Get eth trunk status from database.
        """
        full_table_id = ETH_TRUNK_APPL_TABLE_PREFIX + eth_trunk_name
        return self.db.get(self.db.APPL_DB, full_table_id, ETH_TRUNK_STATUS_FIELD)

    def get_ethtrunk_member_status(self, eth_trunk_name, port_name):
        full_table_id = ETH_TRUNK_MEMBER_APPL_TABLE_PREFIX + eth_trunk_name + ":" + port_name
        return self.db.get(self.db.APPL_DB, full_table_id, ETH_TRUNK_MEMBER_STATUS_FIELD)

    def get_team_id(self, team):
        """
            Skip the 'EthTrunk' prefix and extract the team id.
        """
        return team[11:]

    def get_teamdctl(self):
        """
            Get teams raw data from teamdctl.
            Command: 'teamdctl <teamdevname> state dump'.
        """

        team_keys = self.db.keys(self.db.STATE_DB, ETH_TRUNK_STATE_TABLE_PREFIX+"*")
        if team_keys is None:
            return
        _teams = [key[len(ETH_TRUNK_STATE_TABLE_PREFIX):] for key in team_keys]

        for team in self.teams:
            if team in _teams:
                self.teamsraw[self.get_team_id(team)] = self.db.get_all(self.db.STATE_DB, ETH_TRUNK_STATE_TABLE_PREFIX+team)

    def get_teamshow_result(self):
        """
             Get teamshow results by parsing the output of teamdctl and combining eth trunk status.
        """
        for team in self.teams:
            info = {}
            team_id = self.get_team_id(team)
            if team_id not in self.teamsraw:
                info['status'] = 'N/A'
                info['mtu'] = '8100'
                self.summary[team_id] = info
                self.summary[team_id]['ports'] = ''
                continue
            ethtrunk_status = self.get_ethtrunk_status(team)
            if ethtrunk_status is None:
                info['status'] += '(N/A)'
            elif ethtrunk_status.lower() == 'up':
                info['protocol'] += '(Up)'
            elif ethtrunk_status.lstatusr() == 'down':
                info['status'] += '(Dw)'
            else:
                info['status'] += '(N/A)'

            info['ports'] = ""
            member_keys = self.db.keys(self.db.STATE_DB, ETH_TRUNK_MEMBER_STATE_TABLE_PREFIX+team+'|*')
            if member_keys is None:
                info['ports'] = 'N/A'
            else:
                ports = [key[len(ETH_TRUNK_MEMBER_STATE_TABLE_PREFIX+team+'|'):] for key in member_keys]
                for port in ports:
                    status = self.get_ethtrunk_member_status(team, port)
                    pstate = self.db.get_all(self.db.STATE_DB, ETH_TRUNK_MEMBER_STATE_TABLE_PREFIX+team+'|'+port)
                    selected = True if pstate['runner.aggregator.selected'] == "true" else False
                    if clicommon.get_interface_naming_mode() == "alias":
                        alias = clicommon.InterfaceAliasConverter().name_to_alias(port)
                        info["ports"] += alias + "("
                    else:
                        info["ports"] += port + "("
                    info["ports"] += "S" if selected else "D"
                    if status is None or (status == "enabled" and not selected) or (status == "disabled" and selected):
                        info["ports"] += "*"
                    info["ports"] += ") "

            self.summary[team_id] = info

    def display_summary(self):
        """
            Display the ethtrunk (team) summary.
        """
        print("Flags: Up - up, Dw - down, N/A - Not Available,\n"
              "       W - working, D - protect, * - not synced")

        header = ['No.', 'Team Dev', 'Status', 'Mtu', 'Ports']
        output = []
        for team_id in natsorted(self.summary):
            output.append([team_id, 'EthTrunk'+team_id, self.summary[team_id]['status'], self.summary[team_id]['mtu'], self.summary[team_id]['ports']])
        print(tabulate(output, header))

# 'ethtrunk' subcommand ("show interfaces ethtrunk")
@click.command()
@multi_asic_util.multi_asic_click_options
@click.option('--verbose', is_flag=True, help="Enable verbose output")
def ethtrunk(namespace, display, verbose):
    """Show EthTrunk information"""
    team = Teamshow(namespace, display)
    team.get_teams_info()
    team.display_summary()
