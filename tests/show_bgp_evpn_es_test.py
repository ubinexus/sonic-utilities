import importlib
import pytest

from click.testing import CliRunner
from .bgp_commands_input.bgp_evpn_es_test_vector import testData


def executor(test_vector, show):
    runner = CliRunner()
    input = testData[test_vector]
    exec_cmd = show.cli.commands["evpn"].commands[input['name']]

    result = runner.invoke(exec_cmd, input['args'])

    print(result.exit_code)
    print(result.output)

    if input['rc'] == 0:
        assert result.exit_code == 0
    else:
        assert result.exit_code == input['rc']

    if 'rc_err_msg' in input:
        output = result.output.strip().split("\n")[-1]
        assert input['rc_err_msg'] == output

    if 'rc_output' in input:
        assert result.output == input['rc_output']

    if 'rc_warning_msg' in input:
        output = result.output.strip().split("\n")[0]
        assert input['rc_warning_msg'] in output


class TestBgpEvpnEs(object):

    @classmethod
    def setup_class(cls):
        print("SETUP")
        from .mock_tables import mock_single_asic
        importlib.reload(mock_single_asic)
        from .mock_tables import dbconnector
        dbconnector.load_namespace_config()

    @pytest.mark.parametrize('setup_single_bgp_instance, test_vector',
                             [
                                 ('show_run_bgp_evpn_es', 'bgp_evpn_es'),
                                 ('show_run_bgp_evpn_es_detail', 'bgp_evpn_es_detail'),
                                 ('show_run_bgp_evpn_es_evi', 'bgp_evpn_es_evi'),
                                 ('show_run_bgp_evpn_es_evi_2vtep', 'bgp_evpn_es_evi_2vtep'),
                                 ('show_bgp_evpn_route', 'bgp_evpn_route')
                             ],
                             indirect=['setup_single_bgp_instance'])
    def test_bgp_evpn_es(self,
                         setup_bgp_commands,
                         setup_single_bgp_instance,
                         test_vector):
        show = setup_bgp_commands
        executor(test_vector, show)
