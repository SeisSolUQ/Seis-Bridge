import jinja2
import misfits
import numpy as np
import subprocess
import umbridge

def gpu_available():
    # Hard coded for now, until I find a better way to automatically check,
    # whether a GPU is available.
    # return True
    return False

def seissol_command(order=4):
    if gpu_available():
        return f"mpirun -n 4 -bind-to none seissol-launch SeisSol_Release_ssm_86_cuda_{order}_elastic parameters.par"
    else:
        return f"mpirun -n 4 SeisSol_Release_shsw_{order}_elastic parameters.par"

class SeisSol(umbridge.Model):

    def __init__(self):
        print("Hello")
        self.name = "SeisSol"
        super().__init__("forward")

    def get_input_sizes(self, config):
        return [3]

    def get_output_sizes(self, config):
        return [1, 5]

    def __call__(self, parameters, config):
        if config["order"]:
            o = config["order"]
        else:
            o = 4
        print(o)
        environment = jinja2.Environment(loader=jinja2.FileSystemLoader("."))
        template = environment.get_template("fault_template.yaml")
        content = template.render(traction_left=parameters[0][0], traction_middle=parameters[0][1], traction_right=parameters[0][2])
        with open("fault_chain.yaml", "w+") as fault_file:
            fault_file.write(content)

        # Now start simulation
        subprocess.run(["rm", "-rf", "simulation"])
        subprocess.run(["mkdir", "simulation"])
        subprocess.run(["ls", "-la", "simulation"])
        subprocess.run(seissol_command(o), shell=True)

        m = [misfits.misfit("simulation", "reference", "tpv5", i) for i in [1, 2, 3, 4, 5]]

        output = [[-np.sum(m)**2], m]
        return output

    def supports_evaluate(self):
        return True

umbridge.serve_models([SeisSol()], 4244)
