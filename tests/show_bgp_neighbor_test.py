import os

import pytest

from click.testing import CliRunner
from .mock_tables.bgp_neighbor import *

class TestBgpNeighbors(object):

    @classmethod
    def setup_class(cls):
        print("SETUP")

    @pytest.mark.parametrize('setup_single_bgp_instance', ['bgp_v4_neighbors'],
                             indirect=['setup_single_bgp_instance'])
    def test_bgp_v4_neighbors(self, setup_bgp_commands,
                            setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ip"].commands["bgp"].commands["neighbors"], [])
        print("bgp_output {}".format(result.output))
        assert result.exit_code == 0
        assert result.output == bgp_v4_neighbors

    @pytest.mark.parametrize('setup_single_bgp_instance', ['bgp_v4_neighbors'],
                             indirect=['setup_single_bgp_instance'])
    def test_bgp_v4_neighbor(self, setup_bgp_commands,
                            setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ip"].commands["bgp"].commands["neighbors"],
            ["10.0.0.57"])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == bgp_v4_neighbors

    @pytest.mark.parametrize('setup_single_bgp_instance', ['bgp_v4_neighbor_invalid'],
                            indirect=['setup_single_bgp_instance'])
    def test_bgp_v4_invalid_neighbor(self, setup_bgp_commands,
                                    setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ip"].commands["bgp"].commands["neighbors"],
            ["20.1.1.1"])
        print("{}".format(result.output))
        assert result.exit_code == 2
        assert result.output == bgp_v4_neighbor_invalid
    
    @pytest.mark.parametrize('setup_single_bgp_instance', ['bgp_v4_neighbor_invalid_address'],
                            indirect=['setup_single_bgp_instance'])
    def test_bgp_v4_invalid_neighbor_address(self, setup_bgp_commands,
                                    setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ip"].commands["bgp"].commands["neighbors"],
            ["invalid_address"])
        print("{}".format(result.output))
        assert result.exit_code == 2
        output =  result.output.strip().split("\n")[-1]
        print("{}".format(output))
        assert output == bgp_v4_neighbor_invalid_address

    @pytest.mark.parametrize('setup_single_bgp_instance', ['bgp_v4_neighbor_adv_routes'],
                                indirect=['setup_single_bgp_instance'])
    def test_bgp_v4_neighbor_adv_routes(self, setup_bgp_commands,
                                    setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ip"].commands["bgp"].commands["neighbors"],
            ["10.0.0.57", "advertised-routes"])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == bgp_v4_neighbor_adv_routes
    
    @pytest.mark.parametrize('setup_single_bgp_instance', ['bgp_v4_neighbor_recv_routes'],
                                indirect=['setup_single_bgp_instance'])
    def test_bgp_v4_neighbor_recv_routes(self, setup_bgp_commands,
                                    setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ip"].commands["bgp"].commands["neighbors"],
            ["10.0.0.57", "received-routes"])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == bgp_v4_neighbor_recv_routes

    @pytest.mark.parametrize('setup_single_bgp_instance', ['bgp_v6_neighbors'],
                             indirect=['setup_single_bgp_instance'])
    def test_bgp_v6_neighbors(self, setup_bgp_commands,
                            setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ipv6"].commands["bgp"].commands["neighbors"], [])
        print("bgp_output {}".format(result.output))
        assert result.exit_code == 0
        assert result.output == bgp_v6_neighbors

    @pytest.mark.parametrize('setup_single_bgp_instance', ['bgp_v6_neighbors'],
                             indirect=['setup_single_bgp_instance'])
    def test_bgp_v6_neighbor(self, setup_bgp_commands,
                            setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ipv6"].commands["bgp"].commands["neighbors"],
            ["fc00::72"])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == bgp_v6_neighbors

    @pytest.mark.parametrize('setup_single_bgp_instance', ['bgp_v6_neighbor_invalid'],
                            indirect=['setup_single_bgp_instance'])
    def test_bgp_v6_invalid_neighbor(self, setup_bgp_commands,
                                    setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ipv6"].commands["bgp"].commands["neighbors"],
            ["aa00::72"])
        print("{}".format(result.output))
        assert result.exit_code == 2
        output =  result.output.strip().split("\n")[-1]
        print("{}".format(output))
        assert output == bgp_v6_neighbor_invalid
    
    @pytest.mark.parametrize('setup_single_bgp_instance', ['bgp_v6_neighbor_invalid_address'],
                            indirect=['setup_single_bgp_instance'])
    def test_bgp_v6_invalid_neighbor_address(self, setup_bgp_commands,
                                    setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ipv6"].commands["bgp"].commands["neighbors"],
            ["20.1.1.1"])
        print("{}".format(result.output))
        assert result.exit_code == 2
        output =  result.output.strip().split("\n")[-1]
        print("{}".format(output))
        assert output == bgp_v6_neighbor_invalid_address

    @pytest.mark.parametrize('setup_single_bgp_instance', ['bgp_v6_neighbor_adv_routes'],
                                indirect=['setup_single_bgp_instance'])
    def test_bgp_v6_neighbor_adv_routes(self, setup_bgp_commands,
                                    setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ipv6"].commands["bgp"].commands["neighbors"],
            ["fc00::72", "advertised-routes"])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == bgp_v6_neighbor_adv_routes
    
    @pytest.mark.parametrize('setup_single_bgp_instance', ['bgp_v6_neighbor_recv_routes'],
                                indirect=['setup_single_bgp_instance'])
    def test_bgp_v6_neighbor_recv_routes(self, setup_bgp_commands,
                                    setup_single_bgp_instance):
        show = setup_bgp_commands
        runner = CliRunner()
        result = runner.invoke(
            show.cli.commands["ipv6"].commands["bgp"].commands["neighbors"],
            ["fc00::72", "received-routes"])
        print("{}".format(result.output))
        assert result.exit_code == 0
        assert result.output == bgp_v6_neighbor_recv_routes



