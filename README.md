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

    cat *.jpg | ffmpeg -f image2pipe -r 5 -vcodec mjpeg -i - -vcodec libx264 out.mp4

