# import os
# from unittest import mock
# from click.testing import CliRunner
# from swsscommon.swsscommon import SonicV2Connector
# from .mock_tables import dbconnector
# from utilities_common.db import Db

# import show.main as show
# import rcli
# from rcli import rexec
# from rcli import rshell

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

#     # @mock.patch("rcli.utils.get_linecard_ip", mock.MagicMock(return_value="1.1.1.1"))
#     @mock.patch("os.getlogin", mock.MagicMock(return_value="admin"))
#     @mock.patch("rcli.utils.get_password", mock.MagicMock(return_value="123456"))
#     def test_rexec_echo(self):
#         runner = CliRunner()
#         db = Db()
#         dbconnector = db.db
#         LINECARD_NAME = "LINE-CARD0"

#         runner = CliRunner()
#         result = runner.invoke(show.cli.commands["chassis"].commands["modules"].commands["midplane-status"], obj=db)
#         result_lines = result.output.strip('\n').split('\n')
#         assert result.exit_code == 0
#         result_out = (result_lines[header_lines]).split()
#         print(result_out)
#         assert result_out[2] == 'True', "Unable to find LINE-CARD0 in CHASSIS_MIDPLANE_TABLE"

#         linecard_instance = mock.MagicMock()
#         linecard_instance.connection = True
#         linecard_instance.linecard_name = LINECARD_NAME
#         linecard_instance.execute_cmd.return_value = "hello world\n"


#         rcli.utils.get_linecard_ip = mock.MagicMock(return_value="1.1.1.1")
        
                
#         print(dir(rcli.utils))

#         result = runner.invoke(rexec.cli, [LINECARD_NAME, "-c", "pwd"], obj=db)
#         print(result.output)
#         assert result.exit_code == 0, result.output
#         assert "hello world" in result.output
            
#         # with runner.isolated_filesystem():
#         #     with open('password.txt', 'w') as f:
#         #         f.write('123456')
#         #     result = runner.invoke(rexec.cli, [LINECARD_NAME, "-c", "pwd"])
#         #     print(result)
#         #     assert result.exit_code == 0, result.output
#         #     assert "hello world" in result.output
    
#     # @mock.patch("paramiko")
#     # def test_rexec_echo(self, paramiko):
#     #     runner = CliRunner()
#     #     db = Db()
#     #     dbconnector = db.db
#     #     LINECARD_NAME = "LINE-CARD0"

#     #     runner = CliRunner()
#     #     result = runner.invoke(show.cli.commands["chassis"].commands["modules"].commands["midplane-status"], [LINECARD_NAME], obj=db)
#     #     result_lines = result.output.strip('\n').split('\n')
#     #     assert result.exit_code == 0
#     #     result_out = (result_lines[header_lines]).split()
#     #     assert result_out[2] == 'True', "Unable to find LINE-CARD0 in CHASSIS_MIDPLANE_TABLE"

#         # ssh_client_instance = mock.MagicMock()
#         # ssh_client_instance.connection = mock.MagicMock()
    
#     #   must mock for all test cases
#         # ssh_client_instance.connection.exec_command.return_value
    
#     #   ssh-copy-id
#     #   mock_os = mock.MagicMock()
#     #   mock_os.exists.return_value = True
    
      