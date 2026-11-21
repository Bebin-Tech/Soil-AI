"""Optional Linux wheel cache when Docker Desktop's registry network is slow."""
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-m','pip','download','--only-binary=:all:','--platform','manylinux_2_28_x86_64','--platform','manylinux2014_x86_64','--platform','manylinux_2_26_x86_64','--platform','manylinux_2_27_x86_64','--python-version','3.13','--implementation','cp','--abi','cp313','--abi','abi3','--dest',str(root/'backend/wheels'),'-r',str(root/'backend/requirements-lock.txt')],check=True)
