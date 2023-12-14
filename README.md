#Build
1. `apptainer build --sandbox cuda.sif cuda.def`
2. `apptainer build --sandbox seissol.sif seissol.def`
3. `apptainer build --sandbox server.sif server.def`

#Run
1. Start server in `tpv5` folder: `apptainer run --nv ../server.sif/`
2. Query results: `python3 client/client.py`
