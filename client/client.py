import argparse
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

        def eval_um_model(traction_middle):
                config = {"order": 6}
                return model([[78e6, traction_middle * 1e6, 62e6]], config)

        start_time = time.time() 
        with mp.Pool(10) as p:
                result = p.map(eval_um_model, [81.2, 81.3, 81.4, 81.5, 81.6, 81.7, 81.8, 81.9, 82.0, 82.1])
                print(result)
        end_time = time.time()
        print(end_time - start_time)

