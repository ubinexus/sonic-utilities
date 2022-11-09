from click.testing import CliRunner

import config.main as config
import show.main as show
from utilities_common.db import Db


class TestSuppressFibPending:
    def test_synchronous_mode(self):
        runner = CliRunner()

        db = Db()

        result = runner.invoke(config.config.commands['suppress-pending-fib'], ['enabled'], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry('DEVICE_METADATA' , 'localhost')['suppress-pending-fib'] == 'enabled'

        result = runner.invoke(show.cli.commands['suppress-pending-fib'], obj=db)
        assert result.exit_code == 0
        assert result.output == 'Enabled\n'

        result = runner.invoke(config.config.commands['suppress-pending-fib'], ['disabled'], obj=db)
        print(result.output)
        assert result.exit_code == 0
        assert db.cfgdb.get_entry('DEVICE_METADATA' , 'localhost')['suppress-pending-fib'] == 'disabled'

        result = runner.invoke(show.cli.commands['suppress-pending-fib'], obj=db)
        assert result.exit_code == 0
        assert result.output == 'Disabled\n'

        result = runner.invoke(config.config.commands['suppress-pending-fib'], ['invalid-input'], obj=db)
        print(result.output)
        assert result.exit_code != 0
