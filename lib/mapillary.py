#!/usr/bin/python

import json
import datetime
import sys

try:
    import requests
except ImportError:
    print("requests not found - please run: pip install requests")
    sys.exit()

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
        # print r.url
        return r.json()
