import subprocess

child = subprocess.Popen(
    ['rexec','all','-c','show ip bgp summary','-p','password.txt'], 
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)

output = child.stdout.read().decode()

print(output)