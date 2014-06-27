'''
create_res_sim_mat.py

Create res_sim.mat file from disp.dat (This was originally called
from StructPost, but now is a stand-alone Python script.)

Copyright 2014 Mark L. Palmeri (mlp6@duke.edu)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

__author__ = "Mark Palmeri"
__email__ = "mlp6@duke.edu"
__license__ = "Apache v2.0"


def main():
    import os
    import sys
    import fem_mesh
    import numpy as n

    if sys.version < '2.7':
        sys.exit("ERROR: Requires Python >= v2.7")

    args = read_cli()

    [snic, axes] = load_sort_nodes(args.nodedyn)

    imagingPlane = fem_mesh.extractPlane(snic, axes, (0, 0.0))

    NUM = extractNumNodesDimsTimesteps(args.dispout)

    arfidata = extract_binary_arfidata(args.dispout, NUM, imagingPlane)

    dt = read_dt(args.dynadeck)

    var_dict = create_var_dict(axes, dt, arfidata)

    save_res_sim_mat(args.ressim, var_dict)


def read_cli():
    """
    read in command line arguments
    """

    import argparse as ap

    par = ap.ArgumentParser(description="Generate res_sim.mat from disp.dat",
                            formatter_class=ap.ArgumentDefaultsHelpFormatter)
    par.add_argument("--dispout",
                     help="name of the binary displacement output file",
                     default="disp.dat")
    par.add_argument("--ressim",
                     help="name of the matlab output file",
                     default="res_sim.mat")
    par.add_argument("--nodedyn",
                     help="ls-dyna node definition file",
                     default="nodes.dyn")
    par.add_argument("--dynadeck",
                     help="ls-dyna input deck",
                     default="dynadeck.dyn")

    args = par.parse_args()

    return args


def read_dt(dynadeck):
    """
    read in the time step increment (dt) from the dyna deck

    using *DATABASE_NODOUT for this, and trailing comment lines
    are accomodated
    """
    import re
    r = re.compile('\*DATABASE_NODOUT')
    readNextNonCommentLine = False
    with open(dynadeck, 'r') as d:
        for line in d:
            if readNextNonCommentLine is True:
                # skip next line if it is a comment
                if line[0] is '$':
                    continue
                else:
                    dt = float(line.split(',')[0])
                    return dt
            if r.match(line):
                readNextNonCommentLine = True


def save_res_sim_mat(resname, var_dict):
    """
    save res_sim.mat, with error checking, etc.
    """
    import scipy.io as sio
    try:
        sio.savemat(resname, var_dict, do_compression=True, oned_as='row')
    except IOerror:
        print('Error saving %s.' % resname)


def load_sort_nodes(nodedyn):
    """
    load and sort nodes
    """
    from numpy import loadtxt
    import fem_mesh
    # load in all of the node data, excluding '*' lines
    header_comment_skips = fem_mesh.count_header_comment_skips(nodedyn)
    nodeIDcoords = loadtxt(opts.nodefile,
                           delimiter=',',
                           comments='*',
                           skiprows=header_comment_skips,
                           dtype=[('id', 'i4'), ('x', 'f4'), ('y', 'f4'),
                                  ('z', 'f4')])
    [snic, axes] = fem_mesh.SortNodeIDs()
    return [snic, axes]


def extractNumNodesDimsTimesteps(dispdat):
    """
    extract number of nodes, spatial dimensions and timesteps from
    disp.dat and save in NUM dictionary
    """
    import struct
    f = open(dispdat, 'rb')
    NUM_NODES = struct.unpack('f', f.read(4))
    NUM_DIMS = struct.unpack('f', f.read(4))
    NUM_TIMESTEPS = struct.unpack('f', f.read(4))
    NUM = {'NODES': NUM_NODES, 'DIMS': NUM_DIMS, 'TIMESTEPS': NUM_TIMESTEPS}
    return NUM


def create_var_dict(axes, NUM, dt, arfidata):
    """
    create dictionary of variables to be saved to res_sim.mat

    spatial axes are in mm, time in s
    """
    var_dict = {}
    var_dict['axial'] = -axes[0]*10
    var_dict['lat'] = axes[1]*10
    var_dict['t'] = float(range(0, NUM['TIMESTEPS'], 1)) * dt

if __name__ == "__main__":
    main()
