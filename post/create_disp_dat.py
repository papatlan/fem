#!/bin/env python
"""
create_disp_dat.py

Create disp.dat file from nodout file.

This is replacing StuctPost, which relied on LS-PREPOST, to extract data from
d3plot* files.  (LS-PREPOST no longer works gracefully on the cluster w/o
GTK/video support.)  Instead of working with d3plot files, this approach now
utilizes ASCII nodout files.  Also replaced the Matlab scritps, so this should
run self-contained w/ less dependencies.

EXAMPLE
=======
create_disp_dat.py

=======
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
"""

__author__ = "Mark Palmeri"
__email__ = "mlp6@duke.edu"
__license__ = "Apache v2.0"


def main():
    import sys

    # lets read in some command-line arguments
    args = parse_cli()

    # open dispout for binary writing
    dispout = open(args.dispout, 'wb')

    generate_write_header(dispout, args.nodedyn)

    # open nodout file
    if args.nodout.endswith('gz'):
        import gzip
        print("Extracting gzip-compressed data . . .\n")
        nodout = gzip.open(args.nodout, 'r')
    else:
        print("Extracting data . . .\n")
        nodout = open(args.nodout, 'r')

    header_written = False
    timestep_read = False
    timestep_count = 0
    written_count = 0
    NODE_COUNT = []
    for line in nodout:
        if 'nodal' in line:
            timestep_read = True
            if timestep_count == 0:
                sys.stdout.write('Time Step: ')
                sys.stdout.flush()
            sys.stdout.write('%i ' % timestep_count)
            sys.stdout.flush()
            timestep_count = timestep_count + 1
            data = []
            line_count = 0
            continue
        if timestep_read is True:
            # THIS DOES NOT DEAL WITH THE LAST TIME STEP CORRECTLY!!  FIX THIS!!!!
            if line.startswith('\n'):  # done reading the time step
                timestep_read = False
                # if this was the first time, everything needed to be read to
                # get node count for header
                if not header_written:
                    header = generate_header(data, nodout)
                    NODE_COUNT = header['numnodes']
                    print(NODE_COUNT)
                    write_headers(dispout, header)
                    header_written = True
                process_timestep_data(data, dispout)
                written_count = written_count + 1
                print('WRITTEN!')
            else:
                raw_data = line.split()
                corrected_raw_data = correct_Enot(raw_data)
                data.append(map(float, corrected_raw_data))
                line_count = line_count + 1

    assert (written_count == header['numtimesteps']), 'Mismatch in number of timesteps'

    # close all open files
    dispout.close()
    nodout.close()


def parse_cli():
    '''
    parse command-line interface arguments
    '''
    import sys
    
    if sys.version_info[:2] < (2, 7):
        sys.exit("ERROR: Requires Python >= 2.7")
    
    import argparse

    parser = argparse.ArgumentParser(description="Generate disp.dat "
                                     "data from an ls-dyna nodout file.",
                                     formatter_class=
                                     argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--nodout",
                        help="ASCII file containing nodout data",
                        default="nodout.gz")
    parser.add_argument("--dispout", help="name of the binary displacement "
                        "output file", default="disp.dat")
    parser.add_argument("--nodedyn", help="nodes.dyn input file", 
                        default="nodes.dyn")                        
                        
    args = parser.parse_args()

    return args


def generate_write_header(dispout, nodedyn):
    """
    generate headers & write to disp.dat
    
    INPUTS: dispout ('disp.dat') [binary filename to write to]
            nodedyn ('nodes.dyn') [used to determine # nodes & timesteps]
            
    OUTPUTS: header w/ # nodes, dims and timesteps written to disp.dat
             header (dict: numnodes, numdims, numtimesteps)
    """

    header = {}
    header['numnodes'] = count_nodes(nodedyn)
#    header['numnodes'] = len(data)
    header['numdims'] = 4  # node ID, x-val, y-val, z-val
    ts_count = 0
    t = re.compile('time')
    if outfile.name.endswith('gz'):
        import gzip
        n = gzip.open(outfile.name)
    else:
        n = open(outfile.name)

    header['numtimesteps'] = ts_count

    return header


def count_nodes(nodefile):
    """
    count # nodes from nodes.dyn
    """
    import fem_mesh
    header_comment_skips = fem_mesh.count_header_comment_skips(nodefile)
    nodeIDcoords = n.loadtxt(nodefile,
                             delimiter=',',
                             skiprows=header_comment_skips,
                             comments='*',
                             dtype=[('id', 'i4'), ('x', 'f4'),
                                    ('y', 'f4'), ('z', 'f4')])
    numNodes = len(nodeIDcoords)
    return numNodes
    
    
def write_headers(outfile, header):
    '''
    write binary header information to reformat things on read downstream
    'header' is a dictionary containing the necessary information
    '''
    import struct
    outfile.write(struct.pack('fff', header['numnodes'],
                              header['numdims'], header['numtimesteps']))


def process_timestep_data(data, outfile):
    '''
    operate on each time step data row
    '''
    import struct
    # write all node IDs, then x-val, then y-val, then z-val
    [outfile.write(struct.pack('f', data[j][i]))
        for i in [0, 1, 2, 3]
        for j in range(len(data))]

def correct_Enot(raw_data):
    '''
    ls-dyna seems to drop the 'E' when the negative exponent is three digits,
    so check for those in the line data and change those to 'E-100' so that
    we can convert to floats
    '''
    import re
    for i in range(len(raw_data)):
        raw_data[i] = re.sub(r'(?<!E)\-[1-9][0-9][0-9]', 'E-100', raw_data[i])
    return raw_data


if __name__ == "__main__":
    main()
