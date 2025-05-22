# Build
Build SeisSol according to the documentation.  Copy or link the SeisSol executable
 into this directory.  Currently, the server expects `Seissol_Release_sskx_O_elastic` 
builds, where `O` is the order. 

# Prepare mesh
1. `cd tpv5/mesh` or `cd tpv13/mesh`
2. `./generate_mesh.sh`
3. Choose resolution in `parameters_template.par`

# Run SeisSol

1. `cd tpv5 # or tpv13`
2. `mkdir simulation && cd simulation`
3. ` cp ../fault_template.yaml fault_chain.yaml && cp ../material_template.yaml material.yaml && cp ../parameter_template.par parameters.par`.
4. Adapt the placeholder values, which are written in double curly brackets, e.g. `{{ placeholder }}`.
5. Run SeisSol.

```
export MV2_ENABLE_AFFINITY=0
export MV2_HOMOGENEOUS_CLUSTER=1
export MV2_SMP_USE_CMA=0
export MV2_USE_AFFINITY=0
export MV2_USE_ALIGNED_ALLOC=1
export TACC_AFFINITY_ENABLED=1
export OMP_NUM_THREADS=54
export OMP_PLACES="cores(54)"
ibrun ../SeisSol_Release_sskx_6_elastic parameters.par
```

# Query models 
```
export RANKS=2
export PORT=4242
```
1. Start server in the `tpvX` folder: `python3 tpvXserver.py`. The server expects
an environment variable `$MACHINE_FILE`, which contains the hostnames of all MPI
ranks. It can ususally be created with `export MACHINE_FILE=$(mtkemp) && mpirun hostname > $MACHINE_FILE`.
 This is not necessary for standalone servers, but if we want to run several servers 
in the same slurm allocation, we need the machine file to map different instances
to different nodes.
2. Query results with any UM-Bridge client.
3. For the tpv13 example, use e.g. `python3 client/client.py`

# Further info
SeisSol records the wave field at all receivers.  The server returns the L2 norm 
between a reference solution and the simulation result at these 5 receivers.  
Furthermore, the server returns the sum of the misfits squared, which can be a 
first candidate for the logLikelihood.
For postprocessing the simulation result can be found in `simulation_HASH` directories.

## TPV5
The server takes three arguments: the pre-stress in the three square patches on the fault.

## TPV13
The server takes one argument: the plastic cohesion in the bulk.

## New models
To adapt the server to your needs, adjust `fault_template.yaml`, `material_template.yaml`
and `parameter_template.par`  accordingly. We use `jinja2` syntax here.

# HPC
The server currently, is built for the supercomputer Frontera, which has a particular
MPI installation. If you have a different MPI installation, adjust `server/server.py:23`.

# Ridgecrest C++ server
As a lot of HPC systems do not allow manipulating their srun command to use partial resources from the allocated nodes, we write a different C++ server which is to be combined with the SLURM based load-balancer of UMBridge. This is demonstrated in the Ridgecrest C++ server in the ridgecrest folder. It is also taking care of fused simulations depending on the config. Please note that this is in a very skeletal stage, and is not automated for every situation. There are quite a few hard-coded values as per the filesystem used; more values could be added as per use in the `prepareenvironment()` method and the `prepareSimulationCase()` method needs to be modified as per the simulation case. In the simulation files, all paths are given as absolute paths, hardcoded to avoid copying the files into a new simulation folder for every query. This could be modified if necessary, but this could be very heavy on the filesystem causing slow runs during automated UQ workflows. 

The mesh and ASAGI_files are not uploaded as they are very big for GitHub file storage.
