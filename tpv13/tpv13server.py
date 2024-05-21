import sys
import inspect

sys.path.append("../server")
import server

import os
import umbridge
import jinja2


class TPV13Server(server.SeisSolServer):
    def __init__(self, ranks):
        self.number_of_receivers = 20
        self.number_of_parameters = 1
        self.prefix = "tpv13"
        self.reference_dir = "reference_noise"
        super().__init__(ranks)

    def prepare_parameter_files(self, parameters, run_id):
        environment = jinja2.Environment(loader=jinja2.FileSystemLoader("."))

        fault_template = environment.get_template("fault_template.yaml")
        fault_content = fault_template.render(
            # no parameters here
        )
        with open(os.path.join(run_id, "fault_chain.yaml"), "w+") as fault_file:
            fault_file.write(fault_content)

        material_template = environment.get_template("material_template.yaml")
        material_content = material_template.render(
            plastic_cohesion=parameters[0][0],
        )
        with open(os.path.join(run_id, "material.yaml"), "w+") as material_file:
            material_file.write(material_content)

        parameter_template = environment.get_template("parameters_template.par")
        parameter_content = parameter_template.render(output_dir=run_id)
        with open(os.path.join(run_id, "parameters.par"), "w+") as parameter_file:
            parameter_file.write(parameter_content)


if __name__ == "__main__":
    port = int(os.environ["PORT"])
    ranks = int(os.environ["RANKS"])
    host = os.uname()[1]
    print(host)
    print(f"Running SeisSol server with {ranks} MPI ranks on {host}:{port}.")
    umbridge.serve_models([TPV13Server(ranks)], port)
