#include <iostream>
#include <string>
#include <chrono>
#include <thread>
#include <stdlib.h>
#include <fstream>
#include "inja.hpp"
#include <cstdlib>
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>
#include <tuple>
#include <fstream>

#include "../../umbridge/lib/umbridge.h" // Need to figure out a better way to import


class SeisSolModel : public umbridge::Model {
	public:
		SeisSolModel(int test_delay):umbridge::Model("forward"), test_delay(test_delay) {
			// Constructor
		}

		std::vector<std::size_t> GetInputSizes(const json &config_json) const override {
			// Return the size of the input data
			return std::vector<size_t>(getNumFused(config_json), 1);
		}
		std::vector<std::size_t> GetOutputSizes(const json &config_json) const override {
			// Return the size of the output data
			return std::vector<size_t>(getNumFused(config_json), 1);}
		}

		std::vector<std::vector<double>> Evaluate(const std::vector<std::vector<double>> &inputs, json config) override {
			// Evaluate the model
			int numFused = getNumFused(config);
			auto simulation_data = prepareSimulationCase(inputs, config);
			prepareEnvironment();
			std::string srun_command = "ibrun "; // Needs modification for clusters. (TODO) Shift to cluster specific function later
			/**
			 * @brief Modification for location of binaries for fused- and non- fused models
			 * 
			 */
			if (config["order"] == "4"){
				srun_command += scratch_prefix + "SeisSol_Release_dskx_4_elastic";
			}
			else{
				srun_command += scratch_prefix + "SeisSol_Release_dskx_3_elastic_f8";
			}
			
			srun_command = srun_command + " " + scratch_prefix + std::get<0>(simulation_data) + "/parameters.par";

			printf("Running ibrun command for job: %s\n", std::get<1>(simulation_data).c_str());
			printf("First Input is: %f\n", inputs[0][0]);
			std::string fileName = std::get<1>(simulation_data);
			system(srun_command.c_str());
			std::this_thread::sleep_for(std::chrono::milliseconds(1000));
			
			FILE* fpipe;

			std::string pythonCommand = "python3 " + scratch_prefix + "misfits.py " + std::to_string(numFused) + " " + prefix + " " + scratch_prefix + std::get<0>(simulation_data) + " " + scratch_prefix + reference_dir;

			char c = 0;
			std::string raw_output = "";
			if(0==(fpipe = (FILE*)popen(pythonCommand.c_str(), "r"))){
				perror("popen() failed");
				return{};
			}
			while(fread(&c, sizeof(c), 1, fpipe)){
				raw_output += c;
			}
			pclose(fpipe);
			raw_output.erase(remove(raw_output.begin(), raw_output.end(), '['), raw_output.end());
			raw_output.erase(remove(raw_output.begin(), raw_output.end(), ']'), raw_output.end());

			std::vector<std::vector<double>> result;
			std::istringstream iss(raw_output);
			double value;

			while (iss >> value) {
				result.push_back(std::vector<double>{value});
				if (iss.peek() == ',' || iss.peek() == ' ') {
					iss.ignore();
				}
			}
			return result;
		}

		bool SupportsEvaluate() override
		{
			return true;
		}	
	
	private:
		int test_delay;
		const std::string scratch_prefix = "/scratch1/09830/vikaskurapati/UQ/Seis-Bridge/ridgecrest/";
		const std::string reference_dir = "ref";
		const std::string prefix = "ridgecrest";
		const std::string cluster = "frontera";

		int getNumFused(const json& config_json) const {
			return (config_json["order"] == "4") ? 1 : 8;
		}


		std::tuple<std::string, std::string> prepareSimulationCase(const std::vector<std::vector<double>> &inputs,const json &config){
			std::string hq_jobid = std::getenv("SLURM_JOB_ID"); // Get the job ID from the environment variable
			int numFused = getNumFused(config);
			inja::Environment env;
			inja::json data;
			std::string simulation = "simulation_" + hq_jobid;
			system(("rm -rf " + scratch_prefix + simulation).c_str());
			system(("mkdir " + scratch_prefix + simulation).c_str());

			data["output_dir"] = scratch_prefix + simulation;

			inja::Template fault_temp;
			inja::Template parameters_temp;

			try{
				fault_temp = env.parse_template(scratch_prefix + "fault_template.yaml");
			} catch (const std::exception& e) {
				std::cerr << "Error parsing fault template: " << e.what() << std::endl;
			throw;
			}
			try{
				parameters_temp = env.parse_template(scratch_prefix + "parameters_template.par");
			} catch (const std::exception& e) {
				std::cerr << "Error parsing parameter template: " << e.what() << std::endl;
				throw;
			}
			for(int sim = 0; sim < numFused; sim ++){
				data["rs_a"] = inputs[sim][0];
				std::string suffix = "";
				if(numFused > 1){
					suffix = "_" + std::to_string(sim);
				}
				env.write(fault_temp, data, scratch_prefix + simulation + "/fault_chain" + suffix + ".yaml");
			}
			env.write(parameters_temp, data, scratch_prefix + simulation + "/parameters.par");

			std::tuple<std::string, std::string> simulation_data = std::make_tuple(simulation, hq_jobid);

			return simulation_data;
		}

		void Logger(std::string logMsg){
			std::string filePath = scratch_prefix + "simulation_" + std::getenv("SLURM_JOB_ID") + "/log.txt";
			std::ofstream ofs(filePath.c_str(), std::ios_base::out | std::ios_base::app);
			ofs << logMsg << '\n';
			ofs.close();
}

		void prepareEnvironment(){ // modify this function as per the supercomputer being used
			if(cluster == "laptop"){
				putenv("OMP_NUM_THREADS=11");
				putenv("OMP_PROC_BIND=close");
				putenv("OMP_PLACES=cores(11)");
				}
			else if (cluster == "frontera") {
				putenv("I_MPI_SHM_HEAP_VSIZE=32768");

				putenv("OMP_NUM_THREADS=27");
				putenv("OMP_PLACES=cores(27)");
				putenv("OMP_PROC_BIND=close");

				putenv("XDMFWRITER_ALIGNMENT=8388608");
				putenv("XDMFWRITER_BLOCK_SIZE=8388608");
				putenv("ASYNC_MODE=THREAD");
				putenv("ASYNC_BUFFER_ALIGNMENT=8388608");

				system("ulimit -Ss 2097152");

				putenv("UCX_TLS=knem,dc");
				putenv("UCX_DC_MLX5_TIMEOUT=35000000.00us");
				putenv("UCX_DC_MLX5_RNR_TIMEOUT=35000000.00us");
				putenv("UCX_DC_MLX5_RETRY_COUNT=180");
				putenv("UCX_DC_MLX5_RNR_RETRY_COUNT=180");
				putenv("UCX_RC_MLX5_TIMEOUT=35000000.00us");
				putenv("UCX_RC_MLX5_RNR_TIMEOUT=35000000.00us");
				putenv("UCX_RC_MLX5_RETRY_COUNT=180");
				putenv("UCX_RC_MLX5_RNR_RETRY_COUNT=180");
				putenv("UCX_UD_MLX5_TIMEOUT=35000000.00us");
				putenv("UCX_UD_MLX5_RETRY_COUNT=180");
			}
			else{
				std::cerr << "Unknown cluster type!" << std::endl;
			}
		}
};

int main(){
	char const *port_cstr = std::getenv("PORT");
	int port = 0;
	if (port_cstr != nullptr) {
		port = std::atoi(port_cstr);
	} else {
		std::cout << "PORT environment variable not set! Using port 4242 as default." << std::endl;
		port = 4242;
	}

	char const *delay_cstr = std::getenv("TEST_DELAY");
	int test_delay = 0;
	if(delay_cstr!= nullptr){
		test_delay = std::atoi(delay_cstr);
	}
	std::cout << "Evaluation delay set to " << test_delay << " ms." << std::endl;

	SeisSolModel model(test_delay);
	umbridge::serveModels({&model}, "0.0.0.0", port);
	return 0;
}
