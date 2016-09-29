import os
import os.path
import datetime
import sys
import getopt

try:
    import gpxpy
except ImportError:
    print("gpxpy not found - please run: pip install gpxpy")
    sys.exit()
try:
    import requests
except ImportError:
    print("requests not found - please run: pip install gpxpy")
    sys.exit()

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

if __name__ == "__main__":
    speed_factor = 4

    def print_help():
        print """Usage: gpx-clean.py [-h | -v | -t] input_file [output_file]
    Removes points that stands out from the given GPX file.
    
    The algorithm works by computing the average speed between all points.
    Then all points that has a higher speed * the speed factor than this, is removed.
    This is repeated on new sequence untill no points are removed.
    
    The algorithm works well on sequences with no great speed changes, e.g. doing one
    activity like walking og driving. But combining e.g. walking and driving may yield
    false positives and the sequence should be split manually.
    
    It is perfectly ok to bike and walk a bit, but when the slow activity takes up a
    significant portion of the time, you may get false positives and the fast activity
    may get completely removed.
    
    If too many points are removed, you can raise the factor. If too few are removed
    you may lower the factor.

    Options:
    -t --factor    Give the speed factor (default is """+str(speed_factor)+"""
    -h --help      Print this message and exit.
    -v --verbose   Print extra info.
    """

    verbose = 0
    input_file = None
    output_file = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvt:",
                                   ["help", "verbose", "factor"])
    except getopt.GetoptError, err:
        print str(err)
        sys.exit(2)
    for switch, value in opts:
        if switch in ("-t", "--factor"):
            speed_factor = value
        elif switch in ("-h", "--help"):
            print_help()
            sys.exit(0)
        elif switch in ("-v", "--verbose"):
            verbose += 1

    if len(args) in (1,2):
        input_file = args[0]
    if len(args) == 2:
        output_file = args[1]
    else:
        output_file = input_file
        
    if input_file == None:
        print_help()
        sys.exit(2)

    gpx = GpxClean(input_file)
    gpx.clean()
    gpx.save_file(output_file)
