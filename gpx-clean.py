from __future__ import division
import os
import os.path
import datetime
import sys
import getopt
import math

try:
    import gpxpy
except ImportError:
    print("gpxpy not found - please run: pip install gpxpy")
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
        speeds = [segment.get_speed(i) for i in range(1, segment.get_points_no())]
        return self.mean([s for s in speeds if s != None])

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
                        next_speed = self.get_speed_to_next(segment, i)
                        prev_speed = self.get_speed_to_prev(segment, i)
                        # Remove points that have too high speed to both sides.
                        if self.is_speed_too_great(mean_speed, next_speed) and self.is_speed_too_great(mean_speed, prev_speed):
                            removed_points.append(segment.points[i])
                            segment.remove_point(i)
                            anything_removed = True
                        else:
                            i += 1
        return removed_points
    def reduce(self, min_angle):
        removed_points = []
        for track in self.gpx.tracks:
            for segment in track.segments:
                i = 1 # -1/+1 So we can access previous and next points.
                while i < segment.get_points_no() -1:
                    prev = segment.points[i - 1]
                    curr = segment.points[i]
                    next = segment.points[i + 1]
                    angle = self.angle((prev.latitude, prev.longitude), (curr.latitude, curr.longitude), (next.latitude, next.longitude))
                    # Remove points that have too low angle.
                    if angle < min_angle:
                        removed_points.append(segment.points[i])
                        segment.remove_point(i)
                    else:
                        i += 1
        return removed_points
    def simplify(self, max_distance):
        for track in self.gpx.tracks:
            for segment in track.segments:
                segment.simplify(max_distance)
    def is_speed_too_great(self, mean_speed, speed):
        """ Returns if the given speed is "too great" with regard to the given mean speed and other factors.
        If speed is None when True is returned. This allows for easy handling of first and last point.
        If these are handled separately, this behavior should be changed.
        """
        return speed == None or abs(speed) > abs(mean_speed * self.speed_factor)

    def dot(self, vA, vB):
        return vA[0]*vB[0]+vA[1]*vB[1]
    def angle(self, point_1, point_2, point_3):
        """Returns the angle in degrees between the two lines point_1->point_2 and point_2->point_3.
        The given points must be tuples with x in index 0 and y in index 1."""
        lineA = (point_1, point_2)
        lineB = (point_2, point_3)
        return self.ang_between_lines(lineA, lineB)
    def ang_between_lines(self, lineA, lineB):
        """ Returns the angle in degrees between the two given lines.
            Format of each line: First index 0 or 1 for start or end. 2nd index: 0: x, 1: y. 
            Credit: http://stackoverflow.com/users/4463342/abhinav-ramakrishnan on http://stackoverflow.com/questions/28260962/calculating-angles-between-line-segments-python-with-math-atan2 """
        # Get nicer vector form
        vA = [(lineA[0][0]-lineA[1][0]), (lineA[0][1]-lineA[1][1])]
        vB = [(lineB[0][0]-lineB[1][0]), (lineB[0][1]-lineB[1][1])]
        # Get dot prod
        dot_prod = self.dot(vA, vB)
        # Get magnitudes
        magA = self.dot(vA, vA)**0.5
        magB = self.dot(vB, vB)**0.5
        # Get cosine value
        if magA == 0 or magB == 0:
            return 0
        cos_ = dot_prod/magA/magB
        # Get angle in radians and then convert to degrees
        angle = math.acos(dot_prod/magB/magA)
        # Basically doing angle <- angle mod 360
        ang_deg = math.degrees(angle)%360

        if ang_deg-180>=0:
            # As in if statement
            return 360 - ang_deg
        else: 
            return ang_deg
    def get_speed_to_next(self, segment, point_no):
        if point_no == len(segment.points) - 1:
            return None
        
        next_point = segment.points[point_no + 1]
        return segment.points[point_no].speed_between(next_point)

    def get_speed_to_prev(self, segment, point_no):
        if point_no == 0:
            return None
        
        prev_point = segment.points[point_no - 1]
        return segment.points[point_no].speed_between(prev_point)

    def save_file(self, file):
        fp = open(file, 'w')
        fp.write(self.gpx.to_xml())
        fp.close()

if __name__ == "__main__":
    speed_factor = 4
    min_angle = 20
    max_distance = 5
    min_angle_more = 10
    max_distance_more = 3

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
       --all       Short hand for --clean --reduce --simplify
       --clean     Clean the gpx file. This is done by default
                   but disabled if --reduce is given. In that case this switch must be given.
       --factor    Give the speed factor for cleaning (default is """+str(speed_factor)+"""
       
       --reduce    Reduce the number of points in the gpx file.
                   This switch must be given for this to happen.
       --min-angle The minimum change in angle that must occur for a point to be removed.
                   Default is """+str(min_angle)+"""
                   
       --simplify  Runs the Ramer-Douglas-Peucker algorithm with """+str(max_distance)+""" as default
                   which can be changed using:
       --max-dinstance Sets the max distance in meters used by --simplify. Points closer than this
                   distance may be removed.
                   
       --more      Raises min-angle by """+str(min_angle_more)+""" degrees and max-distance by """+str(max_distance_more)+""" meters. Can be given multiple times.
                   Does not force anything to be run.
    -h --help      Print this message and exit.
    -v --verbose   Print extra info.
    """

    verbose = 0
    input_file = None
    output_file = None
    clean = None
    reduce = None
    simplify = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv",
                                   ["help", "verbose", "factor", "clean", "reduce", "simplify", "min-angle:", "max-dinstance:", "more", "all"])
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
        elif switch in ("--clean"):
            clean = True
        elif switch in ("--reduce"):
            reduce = True
        elif switch in ("--simplify"):
            simplify = True
        elif switch in ("--all"):
            clean = True
            simplify = True
            reduce = True
        elif switch in ("--min-angle"):
            min_angle = value
        elif switch in ("--max-distance"):
            max_distance = value
        elif switch in ("--more"):
            min_angle += min_angle_more
            max_distance += max_distance_more

    if clean == None and reduce == None and simplify == None:
        clean = True
        reduce = False
        simplify = False
    if clean == None:
        clean = False
    if reduce == None:
        reduce = False
    if simplify == None:
        simplify = False
        
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
    if clean:
        gpx.clean()
    if simplify:
        gpx.simplify(max_distance)
    if reduce:
        gpx.reduce(min_angle)
    gpx.save_file(output_file)
