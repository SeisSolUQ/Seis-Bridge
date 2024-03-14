#ifndef QUEUE_H
#define QUEUE_H

#include <cassert>
#include <iostream>
#include <vector>

#include "umbridge/lib/umbridge.h"

#include "Request.h"

class Queue {
  private:
  static std::mutex m;
  const size_t numberOfFusedSimulations;
  const size_t numberOfInputs;
  const size_t numberOfOutputs;
  const size_t forwardPort;

  public:
  std::vector<Request*> requests;

  Queue(size_t numberOfFusedSimulations,
        size_t numberOfInputs,
        size_t numberOfOutputs,
        size_t forwardPort)
      : numberOfFusedSimulations(numberOfFusedSimulations), numberOfInputs(numberOfInputs),
        numberOfOutputs(numberOfOutputs), forwardPort(forwardPort){};

  [[nodiscard]] std::vector<std::vector<double>>
      queryFusedModel(const std::vector<std::vector<double>>& inputs) const {
    const std::string hostname = "localhost:" + std::to_string(forwardPort);
    umbridge::HTTPModel client(hostname, "forward");

    const auto inputSizes = client.GetInputSizes();
    assert(inputSizes.size() == numberOfFusedSimulations);
    for (const auto is : inputSizes) {
      assert(is == numberOfInputs);
    }
    const auto outputSizes = client.GetOutputSizes();
    assert(outputSizes.size() == numberOfFusedSimulations);
    for (const auto os : outputSizes) {
      assert(os == numberOfOutputs);
    }

    std::cout << "Now evaluate fused model at " << hostname << std::endl;
    std::vector<std::vector<double>> outputs = client.Evaluate(inputs);
    return outputs;
  }

  bool push(Request* r) {
    const std::unique_lock<std::mutex> lk(m);
    requests.push_back(r);
    if (requests.size() == numberOfFusedSimulations) {
      std::vector<std::vector<double>> accumulatedRequests;
      for (const auto* r : requests) {
        for (const auto& v : r->input) {
          accumulatedRequests.push_back(v);
        }
      }
      const auto output = queryFusedModel(accumulatedRequests);

      for (size_t i = 0; i < numberOfFusedSimulations; i++) {
        Request* r = requests[i];
        r->output.clear();
        r->output.push_back(output.at(i));
        r->finished = true;
      }
      requests.clear();
      return true;
    } else {
      return false;
    }
  }
};

#endif
