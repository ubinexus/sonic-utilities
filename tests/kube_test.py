from click.testing import CliRunner
from utilities_common.db import Db

show_server_output_0="""\
Kubernetes server config:
KUBERNETES_MASTER SERVER ip 10.3.157.24
KUBERNETES_MASTER SERVER insecure True
KUBERNETES_MASTER SERVER disable False
KUBERNETES_MASTER SERVER port 6443
Kubernetes server has no status info
"""

show_server_output_1="""\
Kubernetes server config:
KUBERNETES_MASTER SERVER ip 10.10.10.11
KUBERNETES_MASTER SERVER insecure True
KUBERNETES_MASTER SERVER disable False
KUBERNETES_MASTER SERVER port 6443
Kubernetes server has no status info
"""

show_server_output_2="""\
Kubernetes server config:
KUBERNETES_MASTER SERVER ip 10.3.157.24
KUBERNETES_MASTER SERVER insecure False
KUBERNETES_MASTER SERVER disable False
KUBERNETES_MASTER SERVER port 6443
Kubernetes server has no status info
"""

show_server_output_3="""\
Kubernetes server config:
KUBERNETES_MASTER SERVER ip 10.3.157.24
KUBERNETES_MASTER SERVER insecure True
KUBERNETES_MASTER SERVER disable True
KUBERNETES_MASTER SERVER port 6443
Kubernetes server has no status info
"""

show_server_output_4="""\
Kubernetes server config:
KUBERNETES_MASTER SERVER ip 10.3.157.24
KUBERNETES_MASTER SERVER insecure True
KUBERNETES_MASTER SERVER disable False
KUBERNETES_MASTER SERVER port 7777
Kubernetes server has no status info
"""


class TestKube(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")


    def __check_res(self, result, info, op):
        print("Running test: {}".format(info))
        print result.exit_code
        print result.output
        assert result.exit_code == 0
        assert result.output == op


    def test_kube_server(self, get_cmd_module):
        (config, show) = get_cmd_module
        runner = CliRunner()

        # Check server not configured
        result = runner.invoke(show.cli.commands["kubernetes"].commands["server"])
        self.__check_res(result, "init server test", show_server_output_0)


    def test_set_server_ip(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # Add IP & test show
        result = runner.invoke(config.config.commands["kubernetes"].commands["server"], ["ip", "10.10.10.11"], obj=db)
        self.__check_res(result, "set server IP", "")
        
        result = runner.invoke(show.cli.commands["kubernetes"].commands["server"], [], obj=db)
        self.__check_res(result, "check server IP", show_server_output_1)


    def test_set_insecure(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # set insecure as True & test show
        result = runner.invoke(config.config.commands["kubernetes"].commands["server"], ["insecure", "off"], obj=db)
        self.__check_res(result, "set server insecure", "")
        
        result = runner.invoke(show.cli.commands["kubernetes"].commands["server"], [], obj=db)
        self.__check_res(result, "check server IP", show_server_output_2)


    def test_set_disable(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # set disable as True & test show
        result = runner.invoke(config.config.commands["kubernetes"].commands["server"], ["disable", "on"], obj=db)
        self.__check_res(result, "set server disable", "")
        
        result = runner.invoke(show.cli.commands["kubernetes"].commands["server"], [], obj=db)
        self.__check_res(result, "check server IP", show_server_output_3)

    
    def test_set_port(self, get_cmd_module):
        (config, show) = get_cmd_module
        db = Db()
        runner = CliRunner()

        # set port  to a different value & test show
        result = runner.invoke(config.config.commands["kubernetes"].commands["server"], ["port", "7777"], obj=db)
        self.__check_res(result, "set server port", "")
        
        result = runner.invoke(show.cli.commands["kubernetes"].commands["server"], [], obj=db)
        self.__check_res(result, "check server IP", show_server_output_4)

    

    @classmethod
    def teardown_class(cls):
        print("TEARDOWN")


