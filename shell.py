import subprocess
import os

path = os.path.dirname(__file__)

def killNickel():
    subprocess.call(["sh", f"{path}/killNickel.sh"])

def restartNickel():
    subprocess.call(["sh", f"{path}/restart.sh"])
