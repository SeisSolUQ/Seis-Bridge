#! /bin/bash
#HQ --resource=gpus/amd=8
#HQ --time-request=10m
#HQ --time-limit=15m

cat << EOF > {{ output_dir }}/select_gpu
#!/bin/bash

export ROCR_VISIBLE_DEVICES=\$SLURM_LOCALID
exec \$*
EOF

chmod +x {{ output_dir }}/select_gpu

CPU_BIND="7e000000000000,7e00000000000000"
CPU_BIND="${CPU_BIND},7e0000,7e000000"
CPU_BIND="${CPU_BIND},7e,7e00"
CPU_BIND="${CPU_BIND},7e00000000,7e0000000000"

export MPICH_GPU_SUPPORT_ENABLED=1
export HSA_XNACK=0

export OMP_NUM_THREADS=3
export OMP_PLACES="cores(3)"
export OMP_PROC_BIND=close

export DEVICE_STACK_MEM_SIZE=4
export SEISSOL_FREE_CPUS_MASK="52-54,60-62,20-22,28-30,4-6,12-14,36-38,44-46"

hostname
date
srun --cpu-bind=mask_cpu:${CPU_BIND} {{ output_dir }}/select_gpu ./SeisSol_Release_sgfx90a_hip_{{ order }}_elastic {{ output_dir }}/parameters.par
