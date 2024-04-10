import subprocess
import sys

def main():
    command = ["az", "ad", "signed-in-user", "show"]
    command.extend(sys.argv[1:])
    subprocess.run(command)
