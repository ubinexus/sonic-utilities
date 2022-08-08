import subprocess

child = subprocess.Popen(
    ['rexec','all','-c','show ip bgp summary','-p','123456'], 
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)

output = child.stdout.read().decode()

print(output)