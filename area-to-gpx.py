#!/usr/bin/python

import json
import errno        
import os
import os.path
import datetime
import sys
import getopt

import lib.config

try:
    from gpxpy import gpx
except ImportError:
    print("gpxpy not found - please run: pip install gpxpy")
    sys.exit()
try:
    import requests
except ImportError:
    print("requests not found - please run: pip install requests")
    sys.exit()

class FileHelper:
    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:    # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def save_json(self, data, folder, file):
        self.mkdir_p(folder)
        fp = open(os.path.join(folder, file), 'w')
        json.dump(data, fp)
        fp.close()
    def save_file(self, data, file):
        fp = open(file, 'w')
        fp.write(data)
        fp.close()
class GpxUtil:
    def coords_2_sequences(self, coords):
        """ Takes an array of arrays of coordinates (lon,lat) and returns a gpx object with sequences."""
        gpx_file = gpx.GPX()

        # Create first track in our GPX:
        gpx_track = gpx.GPXTrack()
        gpx_file.tracks.append(gpx_track)
        
        for seq in coords:
            gpx_segment = gpx.GPXTrackSegment()
            for pair in seq:
                #                                              lon,   lat
                gpx_segment.points.append(gpx.GPXTrackPoint(pair[1], pair[0]))
            gpx_track.segments.append(gpx_segment)
        return gpx_file
        
class MapillaryImageSequence:
    def __init__(self, images = []):
        self.images = images
    def add_image(self, im):
        self.images.append(im)
    def unixtimestamp_2_datetime(self, timestamp):
        return datetime.datetime.utcfromtimestamp(timestamp)
    def images_2_gpxSegment(self):
	"""Takes a sequence of images, as return by get_images_in_sequence() and returns a corresponding gpxpy gpx segment."""
        gpx_segment = gpx.GPXTrackSegment()
        for im in self.images:
            gpx_segment.points.append(gpx.GPXTrackPoint(im['lat'], im['lon'], time=self.unixtimestamp_2_datetime(int(im['captured_at']) / 1000), comment=im['key']))
        return gpx_segment
    def images_2_gpx(self):
        gpx_file = gpx.GPX()

        # Create first track in our GPX:
        gpx_track = gpx.GPXTrack()
        gpx_file.tracks.append(gpx_track)

        # Create first segment in our GPX track:
        gpx_segment = self.images_2_gpxSegment()
        gpx_track.segments.append(gpx_segment)
        return gpx_file
    def get_images(self):
        return self.images

class MapillaryRequest:
    def __init__(self, client_id):
        self.client_id = client_id
    def get_sequence(self, key):
        return self.request('/s/%s' % key)
    def get_image(self, key):
        return self.request('/im/%s' % key)
    def handleErrorSequence(self, response, message = None):
        if 'code' in response and response['code'] == 'not_found':
            print "Sequence not found: %s" % message
            sys.exit(1)
        for key in ['message', 'code']:
            if key in response:
                print "Error %s: %s" % (key, response[key])
        if message != None:
            print message
        sys.exit(1)
    def get_images_in_sequence(self, key):
        seq = self.get_sequence(key)
        if not 'keys' in seq:
            self.handleErrorSequence(seq, key)
        return MapillaryImageSequence([self.get_image(key) for key in seq['keys']])
    def get_sequences_in_area(self, min_lat, min_lon, max_lat, max_lon):
        allSequences = []
        more = True
        page = 0
        while more:
            sequences = self.request('/search/s?max_lat=%s&max_lon=%s&min_lat=%s&min_lon=%s&limit=50&page=%s' % (max_lat, max_lon, min_lat, min_lon, page))
            if 'ss' not in sequences:
                more = False
                return allSequences
            more = 'more' in sequences and sequences['more']
            page = page + 1
            for seq in sequences['ss']:
                allSequences.append(seq['coords'])
        return allSequences;
    def request(self, request):
        if self.client_id == None or len(self.client_id) == 0:
            print "No client ID given."
            sys.exit(1)
        sepChar = '?'
        if request.find("?") != -1:
            sepChar = '&'
        r = requests.get('https://a.mapillary.com/v2%s%sclient_id=%s' % (request, sepChar, self.client_id))
        print r.url
        return r.json()

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
    m = MapillaryRequest(client_id)

    file_helper = FileHelper()
    coords = m.get_sequences_in_area(min_lat,min_lon,max_lat,max_lon)
    gpxutil = GpxUtil()
    gpxobj = gpxutil.coords_2_sequences(coords)
    file_helper.save_file(gpxobj.to_xml(), output_file)
