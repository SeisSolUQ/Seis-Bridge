import hashlib
import jinja2
import misfits
import numpy as np
import os
import re
import subprocess
import sys
import umbridge
import time


job_re = re.compile("job ID: (\d+)")
finished_re = re.compile("State\s+\| (\w+)")


def cluster():
    return "lumi"

def scratch_prefix():
    if cluster() == "lumi":
        return "/scratch/project_465000643/sebastian/Seis-Bridge/tpv13/"
    else:
        return ""


def seissol_command(run_id="", ranks=4, order=4):
    if cluster() == "lumi":
        environment = jinja2.Environment(loader=jinja2.FileSystemLoader("."))
        run_template = environment.get_template("run_template.sh")
        run_content = run_template.render(output_dir=run_id, order=order)
        with open(os.path.join(run_id, "run.sh"), "w+") as run_file:
            run_file.write(run_content)
        return f"hq submit {run_id}/run.sh"
    elif cluster() == "frontera":
        return f"mpiexec.hydra -n {ranks} -machinefile $MACHINE_FILE ../SeisSol_Release_sskx_{order}_elastic {run_id}/parameters.par"

def hq_finished(job_id, my_env):
    job_state = subprocess.run(f"hq job info {job_id}", shell=True, env=my_env, capture_output=True)
    output = job_state.stdout.decode("utf-8")
    result = finished_re.search(output).groups()[0]
    if result == "FAILED":
        raise RuntimeWarning(f"HQ job {job_id} has failed")
    finished = (result == "FINISHED")
    return finished


class SeisSolServer(umbridge.Model):
    def __init__(self, ranks):
        self.name = "SeisSol"
        self.ranks = ranks
        super().__init__("forward")

    def get_input_sizes(self, config):
        return [self.number_of_parameters]

    def get_output_sizes(self, config):
        return [1, self.number_of_receivers]

    def prepare_parameter_files(self, parameters, run_id):
        pass

    def prepare_filesystem(self, parameters, config):   
        submission_time = time.ctime(time.time())
        param_conf_string = str((parameters, config, submission_time)).encode("utf-8")
        print(param_conf_string) 

        m = hashlib.md5()
        m.update(param_conf_string)
        h = m.hexdigest()
        run_id = f"{scratch_prefix()}simulation_{h}"
        print(run_id)

        subprocess.run(["rm", "-rf", run_id])
        subprocess.run(["mkdir", run_id])
        self.prepare_parameter_files(parameters, run_id)

        return run_id

    def prepare_env(self):
        my_env = os.environ.copy()

        if cluster() == "frontera":
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
        try:
            print("Now start SeisSol")     
            submit = subprocess.run(command, shell=True, env=my_env, capture_output=True)
            if cluster() == "lumi":
                job_id = int(job_re.search(submit.stdout.decode("utf-8")).groups()[0])
                print(f"Waiting for hq job {job_id} to complete...")
                while not hq_finished(job_id, my_env):
                    time.sleep(10)
                print("... Done")

            m = [misfits.misfit(run_id, self.reference_dir, self.prefix, i) for i in range(1, self.number_of_receivers+1)]

            output = [[-np.sum(m) / self.number_of_receivers], m]
        except Exception as e:
            print(repr(e))
            output = [[-1000], np.zeros(self.number_of_receivers)]
        output = [np.nan_to_num(o, nan=-1000).tolist() for o in output]
        print(output[0])
        return output

    def supports_evaluate(self):
        return True
