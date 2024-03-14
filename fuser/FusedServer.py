import umbridge
import time
import os

class TestModel(umbridge.Model):

    def __init__(self, n):
        self.n = n
        super().__init__("forward")

    def get_input_sizes(self, config):
        return [2 for i in range(self.n)]

    def get_output_sizes(self, config):
        return [2 for i in range(self.n)]

    def __call__(self, parameters, config):
        time.sleep(int(os.getenv("TEST_DELAY", 0)) / 1000)
        if config and "offset" in config.keys():
            offset = config["offset"]
        else:
            offset = 1

        posterior = [[(i+offset) * parameters[j][i] for i in range(len(parameters[0]))] for j in range(self.n)]
        print(posterior)
        return posterior

    def supports_evaluate(self):
        return True

if __name__ == "__main__":
    testmodel = TestModel(4)
    umbridge.serve_models([testmodel], 4343)
