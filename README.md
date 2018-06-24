# MediaInfo

This a plugin for [deluge](https://deluge-torrent.org/) that adds an additional column to the 
"Files" tab showing codec information about files, as soon as enough of the file has downloaded.

We pre-filter by file extension, then use `ffprobe` to repeatedly query for codec information until
it is complete.

Therefore you must have [`ffprobe`](https://ffbinaries.com/downloads), which comes either 
pre-installed or easy to install on most operating systems. 
