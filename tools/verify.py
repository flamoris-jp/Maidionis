"""Build and run the actual offline acceptance path; never download dependencies."""
import argparse
import os
from pathlib import Path
import platform
import subprocess
import sys
import cmake

p=argparse.ArgumentParser()
p.add_argument('--build-dir',default='build')
p.add_argument('--no-numerical',action='store_true')
p.add_argument('--jobs',type=int,default=2)
a=p.parse_args()
if sys.platform!='linux' or platform.machine() not in ('x86_64','AMD64'):
    p.error('initial durability/numerical profile requires Linux x86_64')
if not 1<=a.jobs<=8:p.error('jobs must be 1..8')
root=Path(__file__).resolve().parents[1];os.chdir(root)
build=Path(a.build_dir).resolve();bin_dir=Path(cmake.CMAKE_BIN_DIR)
args=[sys.executable,'tools/configure.py','--build-dir',str(build)]
if a.no_numerical:args.append('--no-numerical')
subprocess.run(args,check=True)
subprocess.run([str(bin_dir/'cmake'),'--build',str(build),'-j',str(a.jobs)],check=True)
subprocess.run([str(bin_dir/'ctest'),'--test-dir',str(build),'--output-on-failure'],check=True)
env=dict(os.environ,MAIDIONIS_CONTRACT_CHECK=str(build/'maidionis_contract_check'))
if not a.no_numerical:env['MAIDIONIS_TINYBEAT_DRIVER']=str(build/'maidionis_tinybeat_driver')
else:env.pop('MAIDIONIS_TINYBEAT_DRIVER',None)
subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],env=env,check=True)
print('Offline verification completed'+(' (contracts-only; A21 not run)' if a.no_numerical else ' (native + Python + A21 lifecycle)'))
