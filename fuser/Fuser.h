#include <chrono>
#include <cmath>
#include <condition_variable>
#include <linux/limits.h>
#include <mutex>
#include <string>
#include <utility>
#include <vector>

#include "umbridge/lib/umbridge.h"

#include "Queue.h"
#include "Request.h"

class Fuser : public umbridge::Model {
  private:
  static std::mutex m;
  static std::condition_variable cv;
  const size_t numberOfInputs;
  const size_t numberOfOutputs;
  Queue q;

  // Use an external lock to ignore spurious wakeup.
  static void wait(const bool& lock) {
    std::unique_lock<std::mutex> lk(m);
    std::cerr << "Waiting for fused evaluation ..." << std::endl;
    cv.wait(lk, [&lock] { return lock; });
    std::cerr << "...finished waiting." << std::endl;
  }

  public:
  Fuser(std::string name,
        size_t numberOfFusedSimulations,
        size_t numberOfInputs,
        size_t numberOfOutputs,
        size_t forwardPort)
      : umbridge::Model(std::move(name)), numberOfInputs(numberOfInputs),
        numberOfOutputs(numberOfOutputs),
        q(numberOfFusedSimulations, numberOfInputs, numberOfOutputs, forwardPort) {}

  [[nodiscard]] std::vector<std::size_t>
      GetInputSizes(const json& config = json::parse("{}")) const override {
    return {numberOfInputs};
  }

  [[nodiscard]] std::vector<std::size_t>
      GetOutputSizes(const json& config = json::parse("{}")) const override {
    return {numberOfOutputs};
  }

  [[nodiscard]] std::vector<std::vector<double>>
      Evaluate(const std::vector<std::vector<double>>& inputs,
               json config = json::parse("{}")) override {
    Request r(inputs, config);
    const bool finished = q.push(&r);
    if (!finished) {
      std::thread t(wait, std::ref(r.finished));
      t.join();
    } else {
      cv.notify_all();
    }

    return r.output;
  }

  [[nodiscard]] bool SupportsEvaluate() override { return true; }

  [[nodiscard]] bool SupportsGradient() override { return false; }

  [[nodiscard]] bool SupportsApplyJacobian() override { return false; }

  [[nodiscard]] bool SupportsApplyHessian() override { return false; }
};
