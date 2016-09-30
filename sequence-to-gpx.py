#!/usr/bin/python

import json
import errno        
import os
import os.path
import datetime
import sys
import getopt

import lib.config
import lib.filehelper
import lib.config
import lib.mapillary

if __name__ == "__main__":

    cache_folder = None
    def print_help():
        print """Usage: sequence-to-gpx.py [-h | -v] -c sequence_id [output_file]

    Options:
    -c --client-id Give the client ID used for accessing the Mapillary API.
                   This argument must be given the first time the script is used,
                   then it is saved in a configuration file.
    -h --help      Print this message and exit.
    -v --verbose   Print extra info.
    """

    verbose = 0
    seq_id = None
    output_file = None
    client_id = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvc:",
                                   ["help", "verbose", "cache-dir", "client-id:"])
    except getopt.GetoptError, err:
        print str(err)
        sys.exit(2)
    for switch, value in opts:
        if switch in ("-h", "--help"):
            print_help()
            sys.exit(0)
        elif switch in ("-v", "--verbose"):
            verbose += 1
        elif switch in ("-c", "--client-id"):
            client_id = value
        elif switch in ("--cache-dir"):
            cache_folder = value
            

    if len(args) in (1, 2):
        seq_id = args[0]
    else:
        print "Only 1 or 2 arguments must be given:"
        print_help()
        sys.exit(1)
    
    if len(args) == 2:
        output_file = args[1]
    if output_file == None:
        output_file = seq_id+'.gpx'

    config = lib.config.MapillaryConfig()
    if client_id == None:
        client_id = config.getClientID()
    else:
        config.setClientID(client_id)
        config.save()
    m = lib.mapillary.MapillaryRequest(client_id)

    file_helper = lib.filehelper.FileHelper()
    images = m.get_images_in_sequence(seq_id)
    if cache_folder != None:
        file_helper.save_json(images.get_images(), cache_folder, seq_id)
    file_helper.save_file(images.images_2_gpx().to_xml(), output_file)
