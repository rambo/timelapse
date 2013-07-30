Motion time lapse
=================

Idea is to have [motion][motionweb] monitoring the space and when event starts a python daemon
to handle [capturing][captureweb] the timelapse photos is started. Strictly speaking this part is 
an intervalometer.

Another process (running on a network server, where the photos will be stored, conserve write cycles on the SD card)
will then convert these photos into a time lapse movie.

[motionweb]: http://www.lavrsen.dk/foswiki/bin/view/Motion
[captureweb]: http://capture.sourceforge.net/

# Making movies

## Resize images

    mkdir resized
    mogrify -path resized/ -resize x1080 `find . -name *.jpg`

## Encode to MP4

    cd resized
    cat *.jpg | ffmpeg -f image2pipe -r 5 -vcodec mjpeg -i - -vcodec libx264 out.mp4

## Resize with filename tagging

    mkdir resized
    mogrify -path resized/ -resize x1080 -gravity southwest -stroke '#000C' -strokewidth 5 -annotate 0 '%t' -stroke  none   -fill white    -annotate 0 '%t' `find . -name *.jpg`

And if you do not have RTC on the computer you are using you might get weird timestamps, use [timestamp_adjust.py](./timestamp_adjust.py) to fix the names.

## Faster resize on multicore systems

Use [GNU Parallel][gnuparallel].

    mkdir resized
    find . -name *.jpg | parallel mogrify -path resized/ -resize x1080 -gravity southwest -stroke '\#000C' -strokewidth 5 -annotate 0 '%t' -stroke  none   -fill white    -annotate 0 '%t'

[gnuparallel]: http://www.gnu.org/software/parallel/

# TODO

## Deflicker

understand the perl-script and either incorporate it to the helpers or rewrite in python.

## "Camera lost"

Sometimes we lose a chunk of time, make a script to recognize this and add "camera lost" images with suitable timestamps to keep consistent flow of time.

Losing a few frames is not bad but an hour worth of frames is.
