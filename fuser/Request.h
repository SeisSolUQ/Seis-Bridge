#ifndef REQUEST_H
#define REQUEST_H

#include <vector>

#include "umbridge/lib/json.hpp"
#include "umbridge/lib/httplib.h"

class Request {
  public:
  const std::vector<std::vector<double>>& input;
  const nlohmann::json& config;
  std::vector<std::vector<double>> output;
  bool finished{};

  Request(const std::vector<std::vector<double>>& i, const nlohmann::json& c)
      : input(i), config(c){};
};

#endif
