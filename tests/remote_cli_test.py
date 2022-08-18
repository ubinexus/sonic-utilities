pass
# import os
# from unittest import mock
# from click.testing import CliRunner
# from swsscommon.swsscommon import SonicV2Connector
# from utilities_common.db import Db

# import show.main as show
# import rcli.rexec as rexec
# import rcli.rshell as rshell

# test_path = os.path.dirname(os.path.abspath(__file__))
# mock_db_path = os.path.join(test_path, "remote_cli")
# header_lines = 2


# class TestRemoteCLI(object):
#     @classmethod
#     def setup_class(cls):
#         print("SETUP")
#         os.environ["UTILITIES_UNIT_TESTING"] = "1"

#     def set_db_values(self, db, key, kvs):
#         for field, value in kvs.items():
#             db.set(db.STATE_DB, key, field, value)

#     @mock.patch("rcli.linecard.Linecard")
#     def test_rexec_echo(self, mock_Linecard):
#         runner = CliRunner()
#         db = Db()
#         dbconnector = db.db
#         LINECARD_NAME = "LINE-CARD0"

#         runner = CliRunner()
#         result = runner.invoke(show.cli.commands["chassis"].commands["modules"].commands["midplane-status"], [LINECARD_NAME], obj=db)
#         result_lines = result.output.strip('\n').split('\n')
#         assert result.exit_code == 0
#         result_out = (result_lines[header_lines]).split()
#         assert result_out[2] == 'True', "Unable to find LINE-CARD0 in CHASSIS_MIDPLANE_TABLE"

#         linecard_instance = mock.MagicMock()
#         linecard_instance.connection = True
#         linecard_instance.linecard_name = LINECARD_NAME
#         linecard_instance.execute_cmd.return_value = "hello world\n"

#         mock_Linecard.return_value = linecard_instance
#         result = runner.invoke(rexec.cli, [LINECARD_NAME, "-c", "echo 'hello world'"], "123456", obj=db)
#         print(result)
#         assert result.exit_code == 0
#         assert "hello world" in result.output
    
    # @mock.patch("paramiko")
    # def test_rexec_echo(self, paramiko):
    #     runner = CliRunner()
    #     db = Db()
    #     dbconnector = db.db
    #     LINECARD_NAME = "LINE-CARD0"

    #     runner = CliRunner()
    #     result = runner.invoke(show.cli.commands["chassis"].commands["modules"].commands["midplane-status"], [LINECARD_NAME], obj=db)
    #     result_lines = result.output.strip('\n').split('\n')
    #     assert result.exit_code == 0
    #     result_out = (result_lines[header_lines]).split()
    #     assert result_out[2] == 'True', "Unable to find LINE-CARD0 in CHASSIS_MIDPLANE_TABLE"

    #     ssh_client_instance = mock.MagicMock()
    #     ssh_client_instance.connection = mock.MagicMock()
    #
    #   must mock for all test cases
    #     ssh_client_instance.connection.exec_command.return_value
    # 
    #   ssh-copy-id
    #   mock_os = mock.MagicMock()
    #   mock_os.exists.return_value = True
    #
    #   