#!/bin/bash

minLat=$1
minLon=$2
maxLat=$3
maxLon=$4

if [ -z "$minLat" -o -z "$minLon" -o -z "$maxLat" -o -z "$maxLon" ]
then
   echo "Usage: $0 minLat minLon maxLat maxLon"
   echo "Prints the path of all images that are geotagged within the given coordinates."
   echo "Images which are geotagged but does not matched are also printed, but with the text"
   echo "\"No match\" in front, so it can be removed using grep -v."
   echo
   echo "The tool searches for all jpg images in the current and sub folders."
   echo "A search may take a long time if there are many images."
   exit 1
fi

if [ `echo "$minLat > $maxLat" | bc` -gt 0 ]; then
   x=$minLat
   minLat=$maxLat
   maxLat=$x
fi

if [ `echo "$minLon > $maxLon" | bc` -gt 0 ]; then
   x=$minLon
   minLon=$maxLon
   maxLon=$x
fi

find -iname '*.jpg' | while read file
do
  pos="`exiftool -S -S -n -gpsposition "$file" | tr ' ' "\n"`"
  lat="`echo "$pos" | head -n1`"
  lon="`echo "$pos" | tail -n1`"

  if [ -n "$lat" -a -n "$lon" ]; then
    if [ `echo "$lat > $minLat && $lat < $maxLat && $lon > $minLon && $lon < $maxLon" | bc` -gt 0 ]; then
      echo "$file $lat $lon"
    else
      echo "No match: $file $lat $lon"
    fi
  fi

done

