#include <iostream>
#include <string>
#include <chrono>
#include <thread>
#include <stdlib.h>
#include <fstream>
#include "inja.hpp"
#include <cstdlib>

// Needed for HTTPS, implies the need for openssl, may be omitted if HTTP suffices
#define CPPHTTPLIB_OPENSSL_SUPPORT

#include "../../umbridge/lib/umbridge.h" // Need to figure out a better way to import this

class SeisSolModel : public umbridge::Model
{
public:
    SeisSolModel(int test_delay)
        : umbridge::Model("forward"),
          test_delay(test_delay)
    {
    }

    // Define input and output dimensions of model (here we have a single vector of length 1 for input; same for output)
    std::vector<std::size_t> GetInputSizes(const json &config_json) const override
    {
        return {1};
    }

    std::vector<std::size_t> GetOutputSizes(const json &config_json) const override
    {
        return {20};
    }

    std::vector<std::vector<double>> Evaluate(const std::vector<std::vector<double>> &inputs, json config) override
    {
        // Do the actual model evaluation; here we just multiply the first entry of the first input vector by two, and store the result in the output.
        // In addition, we support an artificial delay here, simulating actual work being done.
	std::string hq_jobid = std::getenv("HQ_JOB_ID");
	std::string scratch_prefix = "/scratch/project_465000643/vikas/UQ-2/Seis-Bridge/tpv13/";
	inja::Environment env;
	inja::json data;
	std::string simulation = "simulation_" + hq_jobid;
	system(("rm -rf "+ scratch_prefix + "/" + simulation).c_str());
	system(("mkdir " + scratch_prefix + "/" + simulation).c_str());
	system(("cp " + scratch_prefix + "initial_stress.yaml " + scratch_prefix + simulation + "/").c_str());
	data["output_dir"] = scratch_prefix + simulation;
	data["plastic_cohesion"] = inputs[0][0];
	data["mesh_dir"] = scratch_prefix + "mesh";

	inja::Template fault_temp = env.parse_template(scratch_prefix + "/fault_template.yaml");
	inja::Template parameters_temp = env.parse_template(scratch_prefix + "/parameters_template.par");
	inja::Template material_temp = env.parse_template(scratch_prefix + "/material_template.yaml");
	
	env.write(fault_temp, data, scratch_prefix + simulation + "/fault_chain.yaml");
	env.write(material_temp, data, scratch_prefix + simulation + "/material.yaml");
	env.write(parameters_temp, data, scratch_prefix + simulation + "/parameters.par");
	

	std::string cat_command = inja::render("cat << EOF > " + scratch_prefix + simulation + "/select_gpu\n", data);
	cat_command = cat_command + "#!/bin/bash\n\n";
    	cat_command = cat_command + "export ROCR_VISIBLE_DEVICES=\\$SLURM_LOCALID\n";
    	cat_command = cat_command + "exec \\$*\n";
    	cat_command = cat_command + "EOF";
    	system(cat_command.c_str());

    	system(("chmod +x "+scratch_prefix+simulation+"/select_gpu").c_str());

        putenv("CPU_BIND=7e000000000000,7e00000000000000,7e0000,7e000000,7e,7e00,7e00000000,7e0000000000");
    	putenv("MPICH_GPU_SUPPORT_ENABLED=1");
    	putenv("HSA_XNACK=0");
   	putenv("OMP_NUM_THREADS=3");
    	putenv("OMP_PLACES=cores(3)");
   	putenv("OMP_PROC_BIND=close");
    	putenv("DEVICE_STACK_MEM_SIZE=4");
    	putenv("SEISSOL_FREE_CPUS_MASK=52-54,60-62,20-22,28-30,4-6,12-14,36-38,44-46");

	std::string srun_command = "srun --cpu-bind=mask_cpu:${CPU_BIND} " + scratch_prefix + simulation + "/select_gpu " + scratch_prefix + "/SeisSol_Release_sgfx90a_hip_4_elastic " + scratch_prefix + simulation + "/parameters.par";

	printf("Running srun command for job: %s\n", hq_jobid.c_str());
	printf("Input is: %f\n", inputs[0][0]);
	
	system(srun_command.c_str());
	std::string file_name = hq_jobid;

	std::vector<double> output(20,0.0);	

	return {{output}};
    }

    // Specify that our model supports evaluation. Jacobian support etc. may be indicated similarly.
    bool SupportsEvaluate() override
    {
        return true;
    }

private:
    int test_delay;
};

int main()
{

    // Read environment variables for configuration
    char const *port_cstr = std::getenv("PORT");
    int port = 0;
    if (port_cstr == NULL)
    {
        std::cout << "Environment variable PORT not set! Using port 4242 as default." << std::endl;
        port = 4242;
    }
    else
    {
        port = atoi(port_cstr);
    }

    char const *delay_cstr = std::getenv("TEST_DELAY");
    int test_delay = 0;
    if (delay_cstr != NULL)
    {
        test_delay = atoi(delay_cstr);
    }
    std::cout << "Evaluation delay set to " << test_delay << " ms." << std::endl;

    // Set up and serve model
    SeisSolModel model(test_delay);
    umbridge::serveModels({&model}, "0.0.0.0", port);

    return 0;
}
