# Build
1. `apptainer build mpi.sif mpi.def`
2. `apptainer build seissol.sif seissol.def`

# Test performance
On Frontera:
`OMP_NUM_THREADS=54 apptainer run seissol.sif SeisSol_proxy_Release_sskx_6_elastic 100000 10 all`

# Prepare mesh
1. `cd tpv5/mesh`
2. `./generate_mesh.sh`
3. Choose resolution in `parameters_template.par`

# Run SeisSol
```
cd tpv5
export MV2_ENABLE_AFFINITY=0
export MV2_HOMOGENEOUS_CLUSTER=1
export MV2_SMP_USE_CMA=0
export MV2_USE_AFFINITY=0
export MV2_USE_ALIGNED_ALLOC=1
export TACC_AFFINITY_ENABLED=1
export OMP_NUM_THREADS=54
export OMP_PLACES="cores(54)"
ibrun -n 2 apptainer run ../seissol.sif SeisSol_Release_sskx_6_elastic parameters.par
```

# Run Server
```
export RANKS=2
export PORT=4242
```
1. Start server in `tpv5` folder: `python3 ../server/server.py`
2. Query results: `python3 client/client.py`

# Further info
The server takes three arguments: the pre-stress in the three square patches.
SeisSol records the wave field at five receivers.  The server returns the L2 norm 
between a reference solution and the simulation result at these 5 receivers.  
Furthermore, the server returns the sum of the misfits squared, which can be a 
first candidate for the logLikelihood.

To adapt the server to your needs, adjust `parameters_template.par` and `fault_template.yaml` 
accordingly. We use `jinja2` syntax here.
