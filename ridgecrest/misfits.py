import argparse
import numpy as np
import os
import pandas as pd
import re
import scipy.interpolate as sp_int

# Read CLI arguments
parser = argparse.ArgumentParser(description='Script to calculate misfits for MTMLDA')
parser.add_argument('numFused', metavar='numFused', type=int,
                    help='number of Fused Simulations in the data')
parser.add_argument('prefix', metavar='prefix', type=str, help='prefix of receiver files')
parser.add_argument('directory', metavar='directory', type=str, help='simulation directory')
parser.add_argument('reference', metavar='reference', type=str, help='reference files')

args = parser.parse_args()

def read_receiver(filename):
    with open(filename) as receiver_file:
        lines = receiver_file.readlines()

    quantity_line = lines[1].strip().replace('"',"")
    header_length = 2

    while header_length<len(lines) and lines[header_length].startswith("#"):
        header_length += 1

    receiver_df = pd.read_csv(filename, skiprows=header_length, header=None, sep=r"\s+")
    receiver_df.columns = quantity_line[12:].split(",")
    return receiver_df

def find_receiver(directory, prefix, number):
    receiver_re = re.compile(rf"{prefix}-receiver-{number:05d}-(\d)+.dat")
    for fn in os.listdir(directory):
        if receiver_re.match(fn):
            return os.path.join(directory, fn)


ref_GPS = np.load(os.path.join(args.reference, "dataGPSForCompare.npy"))
rec_comps = ['v1', 'v2', 'v3']

#=================covariance=========
cov_diag = 1e-3*np.ones(30)
cov_diag[0] = 6e-3
cov_diag[2] = 3e-3
cov_diag[3] = 7e-3
cov_diag[10] = 3e-3
cov_diag[13] = 3e-3
cov_diag[20] = 2e-3
cov_diag[22] = 3e-3
cov_diag[23] = 3e-3
cov_diag[24] = 2e-3
cov_diag[25] = 2e-3
cov_diag[26] = 5e-3
cov_diag[27] = 4e-3
#==================================

nRec = 10

log_likelihood = np.zeros(args.numFused)
y_outsquared = np.zeros(args.numFused)
sig_y = 1.0/np.sqrt(2.0)

for sim in range(args.numFused):
    diffnorms = []
    for i_c in range(3):
        for i_s in range(nRec):
            sim_result = read_receiver(find_receiver(args.directory, args.prefix, i_s+1))
            dt = sim_result['Time'][1] - sim_result['Time'][0]
            if args.numFused > 1:
                displace = np.cumsum(sim_result[ rec_comps[i_c] + str(sim) ])*dt
            else:
                displace = np.cumsum(sim_result[rec_comps[i_c]])*dt
            dispRef = ref_GPS[i_c][i_s][0:21]
            times_interp = np.linspace(0.001, 19.99, 21)
            interpolatorGPS = sp_int.interp1d(sim_result['Time'], displace)
            dispSim_interpolated = interpolatorGPS(times_interp)
            diffGPS = dispSim_interpolated - dispRef
            diffnorms.append(np.linalg.norm(diffGPS)**2)
            y_outsquared[sim] += np.linalg.norm(diffGPS)**2/cov_diag[i_c*nRec+i_s]/3/nRec

    log_likelihood[sim] = 0.5*y_outsquared[sim]/sig_y**2

print(-log_likelihood)
