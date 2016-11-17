#!/usr/bin/python

try:
    from gpxpy import gpx
except ImportError:
    print("gpxpy not found - please run: pip install gpxpy")
    sys.exit()

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

class GpxClean:
    def __init__(self, gpx_file):
        self.gpx_file = gpx_file
        self.open(gpx_file)
        self.speed_factor = 4

    def mean(self, numbers):
        return float(sum(numbers)) / max(len(numbers), 1)

    def calculate_mean_speed(self, segment):
        # At i = 0 None is returned instead of a number: Ignore that.
        return self.mean([segment.get_speed(i) for i in range(1, segment.get_points_no())])

    def open(self, gpx_file):
        with open(gpx_file, 'r') as f:
            self.gpx = gpxpy.parse(f)
        
    def clean(self):
        removed_points = []
        for track in self.gpx.tracks:
            anything_removed = True
            while anything_removed:
                anything_removed = False
                for segment in track.segments:
                    mean_speed = self.calculate_mean_speed(segment)
                    i = 0
                    while i < segment.get_points_no():
                        if segment.get_speed(i) > mean_speed * self.speed_factor:
                            removed_points.append(segment.points[i])
                            segment.remove_point(i)
                            anything_removed = True
                        else:
                            i += 1
        return removed_points
        
    def save_file(self, file):
        fp = open(file, 'w')
        fp.write(self.gpx.to_xml())
        fp.close()
