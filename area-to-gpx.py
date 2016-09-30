#!/usr/bin/python

import json
import errno        
import os
import os.path
import datetime
import sys
import getopt

import lib.filehelper
import lib.config
import lib.mapillary
import lib.gpxutils

if __name__ == "__main__":

    cache_folder = None
    def print_help():
        print """Usage: area-to-gpx.py [-h | -v] -c client_id min_lat,min_lon,max_lat,max_lon output_file

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
            

    if len(args) != 2:
        print "2 arguments must be given:"
        print_help()
        sys.exit(1)
    else:
        latlon = args[0]
        output_file = args[1]
    if len(latlon.split(',')) != 4:
        print "The lat/lon... argument must contain 4 numbers separated by only a , and no spaces."
        print_help()
        sys.exit(1)
        
    (min_lat,min_lon,max_lat,max_lon) = latlon.split(',')
    
    config = lib.config.MapillaryConfig()
    if client_id == None:
        client_id = config.getClientID()
    else:
        config.setClientID(client_id)
        config.save()
    m = lib.mapillary.MapillaryRequest(client_id)

    file_helper = lib.filehelper.FileHelper()
    coords = m.get_sequences_in_area(min_lat,min_lon,max_lat,max_lon)
    gpxutil = lib.gpxutils.GpxUtil()
    gpxobj = gpxutil.coords_2_sequences(coords)
    file_helper.save_file(gpxobj.to_xml(), output_file)
