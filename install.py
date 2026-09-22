import subprocess

res = subprocess.run(["sudo", "pacman", "-Syu"])
print(res.returncode)
