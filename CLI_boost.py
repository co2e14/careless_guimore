#!/dls/science/groups/i23/pyenvs/carelesspy_3p9/bin/python

import sys
import os
import time
import subprocess
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("project", help="name of the project")
parser.add_argument("file", help="path to the file")
args = parser.parse_args()

project_name = args.project
file_path = args.file

print("Project name: ", project_name)
print("File path: ", file_path)

try:
    os.makedirs("careless_" + project_name, exist_ok=True)
    projname = project_name
except:
    pass

try:
    output = subprocess.check_output(["rs.mtzdump", file_path]).decode(
        "utf-8"
    )
except:
    pass

start_line = "mtz.dtypes:\n"
start_index = output.index(start_line) + len(start_line)
mtz_lines = output[start_index:].split("\n")
batch_and_mtzreal_columns = ["dHKL", "Hobs", "Kobs", "Lobs"]

for line in mtz_lines:
    if "Batch" in line or "MTZReal" in line:
        column_name = line.split()[0]
        batch_and_mtzreal_columns.append(column_name)

mode_folder = os.path.join("careless_" + project_name, "boost")
os.makedirs(mode_folder + "_noanom", exist_ok=True)
os.makedirs(mode_folder + "_anom", exist_ok=True)

boost_layers = 4
dof = 16

command1 = [
    "careless",
    "mono",
    f"--studentt-likelihood-dof={dof}",
    "--mc-samples=20",
    "--mlp-layers=10",
    f"--image-layers={boost_layers}",
    ",".join(batch_and_mtzreal_columns),
    file_path,
    f"careless_{project_name}/boost_noanom/{project_name}",
]

command2 = [
    "careless",
    "mono",
    "--freeze-scale",
    f"--scale-file=careless_{project_name}/boost_noanom/{project_name}_scale",
    "--anomalous",
    f"--studentt-likelihood-dof={dof}",
    "--mc-samples=20",
    "--mlp-layers=10",
    f"--image-layers={boost_layers}",
    ",".join(batch_and_mtzreal_columns),
    file_path,
    f"careless_{project_name}/boost_anom/{project_name}",
]

try:
    subprocess.run(command1)
except:
    exit()
time.sleep(5)
try:
    subprocess.run(command2)
except:
    exit()