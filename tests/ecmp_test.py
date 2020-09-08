import os
import traceback

from click.testing import CliRunner

import config.main as config
import show.main as show
from utilities_common.db import Db

show_ecmp_fg_nhg_hash_view_output="""\
+-----------------------------+--------------------+------------+
| FG_NHG_PREFIX               | Active Next Hops   | Bank Ids   |
+=============================+====================+============+
| NHG_PREFIX: 100.50.25.12/32 | 200.200.200.4      | 0          |
|                             |                    | 1          |
|                             |                    | 2          |
|                             |                    | 3          |
|                             |                    | 4          |
|                             |                    | 5          |
|                             |                    | 6          |
|                             |                    | 7          |
|                             |                    | 8          |
|                             |                    | 9          |
|                             |                    | 10         |
|                             |                    | 11         |
|                             |                    | 12         |
|                             |                    | 13         |
|                             |                    | 14         |
|                             |                    | 15         |
+-----------------------------+--------------------+------------+
| NHG_PREFIX: 100.50.25.12/32 | 200.200.200.5      | 16         |
|                             |                    | 17         |
|                             |                    | 18         |
|                             |                    | 19         |
|                             |                    | 20         |
|                             |                    | 21         |
|                             |                    | 22         |
|                             |                    | 23         |
|                             |                    | 24         |
|                             |                    | 25         |
|                             |                    | 26         |
|                             |                    | 27         |
|                             |                    | 28         |
|                             |                    | 29         |
|                             |                    | 30         |
|                             |                    | 31         |
+-----------------------------+--------------------+------------+
| NHG_PREFIX: fc:5::/128      | 200:200:200:200::4 | 0          |
|                             |                    | 1          |
|                             |                    | 2          |
|                             |                    | 3          |
|                             |                    | 4          |
|                             |                    | 5          |
|                             |                    | 6          |
|                             |                    | 7          |
|                             |                    | 8          |
|                             |                    | 9          |
|                             |                    | 10         |
|                             |                    | 11         |
|                             |                    | 12         |
|                             |                    | 13         |
|                             |                    | 14         |
|                             |                    | 15         |
+-----------------------------+--------------------+------------+
| NHG_PREFIX: fc:5::/128      | 200:200:200:200::5 | 16         |
|                             |                    | 17         |
|                             |                    | 18         |
|                             |                    | 19         |
|                             |                    | 20         |
|                             |                    | 21         |
|                             |                    | 22         |
|                             |                    | 23         |
|                             |                    | 24         |
|                             |                    | 25         |
|                             |                    | 26         |
|                             |                    | 27         |
|                             |                    | 28         |
|                             |                    | 29         |
|                             |                    | 30         |
|                             |                    | 31         |
+-----------------------------+--------------------+------------+
"""

show_ecmp_fg_nhg_active_hops_output="""\
+-----------------------------+--------------------+
| FG_NHG_PREFIX               | Active Next Hops   |
+=============================+====================+
| NHG_PREFIX: 100.50.25.12/32 | 200.200.200.4      |
|                             | 200.200.200.5      |
+-----------------------------+--------------------+
| NHG_PREFIX: fc:5::/128      | 200:200:200:200::4 |
|                             | 200:200:200:200::5 |
+-----------------------------+--------------------+
"""
class TestECMP(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def test_show_ecmp_fg_nhg_hash_view(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["ecmp"].commands["fg-nhg-hash-view"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_ecmp_fg_nhg_hash_view_output

    def test_show_ecmp_fg_nhg_active_hops(self):
        runner = CliRunner()
        result = runner.invoke(show.cli.commands["ecmp"].commands["fg-nhg-active-hops"], [])
        print(result.exit_code)
        print(result.output)
        assert result.exit_code == 0
        assert result.output == show_ecmp_fg_nhg_active_hops_output

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
