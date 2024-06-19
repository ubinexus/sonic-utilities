import show.main as show
import pytest
import os
from click.testing import CliRunner
from utilities_common.db import Db
from .mock_tables import dbconnector
from .bgp_input import assert_show_output
 
test_path = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(test_path, "bgp_input")
mock_config_path = os.path.join(input_path, "mock_config")
 
class TestBgpMultiAsic:
    @classmethod
    def setup_class(cls):
        logger.info("Setup class: {}".format(cls.__name__))
        os.environ['UTILITIES_UNIT_TESTING'] = "2"
        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = "multi_asic"
        delete_cache()
 
    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")
        delete_cache()
        logger.info("Teardown class: {}".format(cls.__name__))
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        os.environ["UTILITIES_UNIT_TESTING_TOPOLOGY"] = ""
        from .mock_tables import mock_single_asic
        importlib.reload(mock_single_asic)
       
    @pytest.mark.parametrize(
    "cfgdb,output", [
            pytest.param(
                os.path.join(mock_config_path, "empty"),
                {
                    "plain": assert_show_output.show_device_global_all_disabled_multi_asic,
                    "json": assert_show_output.show_device_global_empty
                },
                id="empty"
            ),
            pytest.param(
                os.path.join(mock_config_path, "all_disabled"),
                {
                    "plain": assert_show_output.show_device_global_all_disabled_multi_asic,
                    "json": assert_show_output.show_device_global_all_disabled_multi_asic_json
                },
                id="all-disabled"
            ),
            pytest.param(
                os.path.join(mock_config_path, "all_enabled"),
                {
                    "plain": assert_show_output.show_device_global_all_enabled_multi_asic,
                    "json": assert_show_output.show_device_global_all_enabled_multi_asic_json
                },
                id="all-enabled"
            ),
            pytest.param(
                os.path.join(mock_config_path, "tsa_enabled"),
                {
                    "plain": assert_show_output.show_device_global_tsa_enabled_multi_asic,
                    "json": assert_show_output.show_device_global_tsa_enabled_multi_asic_json
                },
                id="tsa-enabled"
            ),
            pytest.param(
                os.path.join(mock_config_path, "wcmp_enabled"),
                {
                    "plain": assert_show_output.show_device_global_wcmp_enabled_multi_asic,
                    "json": assert_show_output.show_device_global_wcmp_enabled_multi_asic_json
                },
                id="w-ecmp-enabled"
            )
        ]
    )
       
    @pytest.mark.parametrize(
        "format", [
            "plain",
            "json",
        ]
    )
    
    @patch('multi_asic.is_multi_asic', return_value=True)
    @patch('multi_asic.get_namespace_list', return_value=['asic0', 'asic1'])
    def test_show_device_global_multi_asic(self, cfgdb, output, format):
        db = MagicMock()
        runner = CliRunner()
        db.cfgdb_clients = {
            "asic0": MagicMock(),
            "asic1": MagicMock()
        }
       
        for asic in ["asic0", "asic1"]:
            db.cfgdb_clients[f"{asic}"].get_table.return_value = cfgdb
       
        cmd_args = [] if output_format == "plain" else ["--json"]
           
        result = runner.invoke(
            show.cli.commands["bgp"].commands["device-global"],
            cmd_args, obj=db
        )
       
        logger.debug("\n" + result.output)
        logger.debug(result.exit_code)
 
        assert result.output == output[format]
        assert result.exit_code == SUCCESS
      
   