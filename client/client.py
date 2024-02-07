import argparse
import itertools
import multiprocessing as mp
import time
import umbridge

if __name__ == "__main__":
        parser = argparse.ArgumentParser()
        parser.add_argument("port", help="port", type=int)
        args = parser.parse_args()
        
        address = f"http://localhost:{args.port}"
        server_available = False
        while not server_available:
                try:
                        model = umbridge.HTTPModel(address, "forward")
                        print("Server available")
                        server_available = True
                except:
                        print("Server not available")
                        time.sleep(10)

        def eval_um_model(traction_left, traction_middle):
                config = {"order": 6}
                return model([[traction_left * 1e6, traction_middle * 1e6, 62e6]], config)

        start_time = time.time() 
        tractions_middle = [81.2, 81.3, 81.4, 81.5, 81.6, 81.7, 81.8, 81.9, 82.0, 82.1]
        tractions_left = [78.0, 79.0, 80.0, 81.0, 82.0, 83.0]
        arguments = [a for a in itertools.product(tractions_left, tractions_middle)]
        number_of_models = len(arguments)
        print(f"Evaluate {number_of_models} in parallel")
        with mp.Pool(number_of_models) as p:
                result = p.starmap(eval_um_model, arguments)
                print(result)
        end_time = time.time()
        print(end_time - start_time)

