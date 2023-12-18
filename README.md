# Build
1. `apptainer build --sandbox cuda.sif cuda.def`
2. `apptainer build --sandbox seissol.sif seissol.def`
3. `apptainer build --sandbox server.sif server.def`

# Prepare mesh
1. `cd tpv5/mesh`
2. `./generate_mesh.sh`

# Run
1. Start server in `tpv5` folder: `apptainer run --nv ../server.sif/`
2. Query results: `python3 client/client.py`

# Further info
The server takes three arguments: the pre-stress in the three square patches.
SeisSol records the wave field at five receivers.
The server returns the L2 norm between a reference solution and the simulation 
result at these 5 receivers.
Furthermore, the server returns the sum of the misfits squared, which can be a 
first candidate for the logLikelihood.

One forward model execution takes about 7 minutes on four RTX3080s. It can be 
reduced by changing the mesh (i.e. `tpv5/parameters.par` line 41). Higher numbers
are coarser resolution are less compute time.

For now, we hardcode, whether a GPU is used or not in `server/server.py` line 10.
