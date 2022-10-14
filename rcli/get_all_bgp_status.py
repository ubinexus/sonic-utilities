from click.testing import CliRunner
from rcli import rexec

runner = CliRunner()

result = runner.invoke(rexec.cli,  ["all", "-c", "show ip bgp summary", "-p","password.txt"])

print(result.output.strip("\n"))