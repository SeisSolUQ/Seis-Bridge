import umbridge
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("port", help="port", type=int)
args = parser.parse_args()

address = f"http://localhost:{args.port}"
print(umbridge.supported_models(address))
model = umbridge.HTTPModel(address, "forward")
print(model.get_input_sizes())
print(model.get_output_sizes())
config = {"order": 6}
for traction_middle in [81.2, 81.3, 81.4, 81.5, 81.6, 81.7, 81.8, 81.9, 82.0]:
    print(traction_middle)
    print(model([[78e6, traction_middle * 1e6, 62e6]], config))
