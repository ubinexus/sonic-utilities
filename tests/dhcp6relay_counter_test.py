import sys
import os

import show.main as show
from click.testing import CliRunner

expected_counts = """\
  Message Type    Vlan1000
--------------  ----------
       Solicit           0
     Advertise           0
       Request           0
       Confirm           0
         Renew           0
        Rebind           0
         Reply           0
       Release           0
       Decline           0
 Relay-Forward           0
   Relay-Reply           0

"""

class TestDhcp6RelayCounters(object):

    def test_show_counts(self):           
        runner = CliRunner()
        result = runner.invoke(show.cli.commands['dhcp6relay_counters'].commands["counts"], ["-i", "Vlan1000"])

        orig_stdout = sys.stdout
        f = open('output.txt','w')
        sys.stdout = f
        print(result.output)
        sys.stdout = orig_stdout
        f.close()
        
        print(result.output)
        assert result.output == expected_counts
