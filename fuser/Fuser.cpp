#include "Fuser.h"

#include <iostream>

constexpr size_t NumberOfFusedSimulations = 4;
constexpr size_t NumberOfInputs = 2;
constexpr size_t NumberOfOutputs = 2;
constexpr size_t OutwardPort = 4242;
constexpr size_t ForwardPort = 4343;

std::mutex Fuser::m;
std::condition_variable Fuser::cv;

std::mutex Queue::m;

int main() {
  std::cout << "Fuse " << NumberOfFusedSimulations << " models into one model." << std::endl;

  Fuser f("fuser", NumberOfFusedSimulations, NumberOfInputs, NumberOfOutputs, ForwardPort);
  const std::vector<umbridge::Model*> models = {&f};
  umbridge::serveModels(models, "0.0.0.0", OutwardPort, true, false);

  return 0;
}
