"""Configure against locally installed, pinned build dependencies; no fetch."""
import argparse
from pathlib import Path
import subprocess
import sys
import cmake
import nlohmann_json

p=argparse.ArgumentParser();p.add_argument('--no-numerical',action='store_true');p.add_argument('--build-dir',default='build');a=p.parse_args()
args=[str(Path(cmake.CMAKE_BIN_DIR)/'cmake'),'-S','.', '-B',a.build_dir,'-DCMAKE_BUILD_TYPE=Release',
      '-DNLOHMANN_JSON_INCLUDE_DIR='+str(nlohmann_json.get_include())]
if a.no_numerical: args+=['-DMAIDIONIS_NUMERICAL=OFF']
else:
    import torch
    args+=['-DMAIDIONIS_NUMERICAL=ON','-DCMAKE_PREFIX_PATH='+torch.utils.cmake_prefix_path]
subprocess.run(args,check=True)
