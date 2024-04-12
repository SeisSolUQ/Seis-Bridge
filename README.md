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
1. Start server in the `tpvX` folder: `python3 tpvXserver.py`
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

