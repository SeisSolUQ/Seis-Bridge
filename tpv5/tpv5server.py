import sys
import inspect
sys.path.append("../server")
import server

import os
import umbridge
import jinja2

class TPV5Server(server.SeisSolServer):
  def get_input_sizes(self, config):
    return [3]

  def get_output_sizes(self, config):
    return [1, 5]

  def prepare_parameter_files(self, parameters, run_id):
      environment = jinja2.Environment(loader=jinja2.FileSystemLoader("."))

      fault_template = environment.get_template("fault_template.yaml")
      fault_content = fault_template.render(
        traction_left = parameters[0][0],
        traction_middle = parameters[0][1],
        traction_right = parameters[0][2],
      )
      with open(os.path.join(run_id, "fault_chain.yaml"), "w+") as fault_file:
          fault_file.write(fault_content)

      material_template = environment.get_template("material_template.yaml")
      material_content = material_template.render(
        # no parameters here 
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
  print(f"Running SeisSol server with {ranks} MPI ranks on port {port}.")
  umbridge.serve_models([TPV5Server(ranks)], port)
