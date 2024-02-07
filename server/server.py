import hashlib
import jinja2
import misfits
import numpy as np
import os
import subprocess
import sys
import umbridge


def gpu_available():
    # Hard coded for now, until I find a better way to automatically check,
    # whether a GPU is available.
    # return True
    return False


def seissol_command(run_id="", ranks=4, order=4):
    if gpu_available():
        return f"mpirun -n {ranks} -bind-to none seissol-launch SeisSol_Release_ssm_86_cuda_{order}_elastic parameters.par"
    else:
        return f"mpiexec.hydra -n {ranks} -machinefile $HQ_NODE_FILE apptainer run ../seissol.sif SeisSol_Release_sskx_{order}_elastic {run_id}/parameters.par"


class SeisSol(umbridge.Model):
    def __init__(self, ranks):
        self.name = "SeisSol"
        self.ranks = ranks
        super().__init__("forward")

    def get_input_sizes(self, config):
        return [3]

    def get_output_sizes(self, config):
        return [1, 5]

    def prepare_filesystem(self, parameters, config):
        param_conf_string = str((parameters, config)).encode("utf-8")
        print(param_conf_string) 

        m = hashlib.md5()
        m.update(param_conf_string)
        h = m.hexdigest()
        run_id = f"simulation_{h}"
        print(run_id)

        subprocess.run(["rm", "-rf", run_id])
        subprocess.run(["mkdir", run_id])
        environment = jinja2.Environment(loader=jinja2.FileSystemLoader("."))
        fault_template = environment.get_template("fault_template.yaml")
        fault_content = fault_template.render(
            traction_left=parameters[0][0],
            traction_middle=parameters[0][1],
            traction_right=parameters[0][2],
        )
        with open(os.path.join(run_id, "fault_chain.yaml"), "w+") as fault_file:
            fault_file.write(fault_content)
        parameter_template = environment.get_template("parameters_template.par")
        parameter_content = parameter_template.render(output_dir=run_id)
        with open(os.path.join(run_id, "parameters.par"), "w+") as parameter_file:
            parameter_file.write(parameter_content)

        return run_id

    def prepare_env(self):
        my_env = os.environ.copy()
        my_env["MV2_ENABLE_AFFINITY"] = "0"
        my_env["MV2_HOMOGENEOUS_CLUSTER"] = "1"
        my_env["MV2_SMP_USE_CMA"] = "0"
        my_env["MV2_USE_AFFINITY"] = "0"
        my_env["MV2_USE_ALIGNED_ALLOC"] = "1"
        my_env["TACC_AFFINITY_ENABLED"] = "1"
        my_env["OMP_NUM_THREADS"] = "54"
        my_env["OMP_PLACES"] = "cores(54)"
        return my_env

    def __call__(self, parameters, config):
        if not config["order"]:
            config["order"] = 4
        run_id = self.prepare_filesystem(parameters, config)

        command = seissol_command(run_id, self.ranks, config["order"])
        print(command)
        my_env = self.prepare_env()
        sys.stdout.flush()
        subprocess.run("cat $HQ_NODE_FILE", shell=True)
        result = subprocess.run(command, shell=True, env=my_env)
        result.check_returncode()

        m = [misfits.misfit(run_id, "reference", "tpv5", i) for i in [1, 2, 3, 4, 5]]

        output = [[-np.sum(m) ** 2], m]
        print(output)
        return output

    def supports_evaluate(self):
        return True


if __name__ == "__main__":
    port = int(os.environ["PORT"])
    ranks = int(os.environ["RANKS"])
    print(f"Running SeisSol server with {ranks} MPI ranks on port {port}.")
    umbridge.serve_models([SeisSol(ranks)], port)
