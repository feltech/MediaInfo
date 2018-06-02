#
# -*- coding: utf-8 -*-#

# Copyright (C) 2018 David Feltell <dave@feltell.net>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
#               2007-2009 Andrew Resch <andrewresch@gmail.com>
#               2009 Damien Churchill <damoxc@gmail.com>
#               2010 Pedro Algarvio <pedro@algarvio.me>
#               2017 Calum Lind <calumlind+deluge@gmail.com>
#
# This file is part of MediaInfo and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#


from __future__ import unicode_literals

import os
import logging
import json
import subprocess
import threading

import deluge.configmanager
import deluge.component as component
from deluge.core.rpcserver import export
from deluge.plugins.pluginbase import CorePluginBase

from .videoexts import video_exts

log = logging.getLogger(__name__)

DEFAULT_PREFS = {
    'ffprobe_bin': '/usr/bin/ffprobe'
}


class Core(CorePluginBase):
    def enable(self):
        log.info("XX Enabling MediaInfo core")
        self._config = deluge.configmanager.ConfigManager('mediainfo.conf', DEFAULT_PREFS)
        self._core = component.get('Core')
        self._plugin = component.get('CorePluginManager')
        self._media_info = {}
        log.info("XX Enabled MediaInfo core")

    def disable(self):
        log.info("XX Disabling MediaInfo core")
        self._media_info = {}
        log.info("XX Disabled MediaInfo core")

    @export
    def set_config(self, config):
        """Sets the config dictionary"""
        for key in config:
            self._config[key] = config[key]
        self._config.save()

    @export
    def get_config(self):
        """Returns the config dictionary"""
        return self._config.config

    @export
    def get_info(self, torrent_id):
        log.info("XX get_info enter")
        if torrent_id is None:
            return None

        if torrent_id not in self._media_info:
            status = self._core.get_torrent_status(
                torrent_id, ["save_path", "download_location", "files"]
            )
            if not status:
                return None
            media_info = {
                'complete': False,
                'root': status.get('download_location', status['save_path']),
                'files': {f['path']: None for f in status['files']}
            }
            self._media_info[torrent_id] = media_info
        else:
            media_info = self._media_info[torrent_id]

        if media_info['complete']:
            return media_info

        media_info['complete'] = True
        root = media_info['root']
        files = media_info['files']
        for path in files:
            log.info("Checking file %s" % path)
            if files[path] is None:
                ext = os.path.splitext(path)[1]
                # Check if file extension indicates a video file.
                if video_exts.match(ext):
                    try:
                        cmd = [
                            self._config['ffprobe_bin'], "-v", "quiet", "-print_format",
                            "json", "-show_streams", os.path.join(root, path)
                        ]
                        log.info("Executing: %s" % cmd)
                        output = subprocess.check_output(cmd)
                    except subprocess.CalledProcessError as e:
                        # Assume if ffprobe failed, it's only temporary (file not downloaded
                        # enough yet).
                        log.info("No video file metadata available (yet): %s" % e)
                        media_info['complete'] = False
                    else:
                        log.info("Got file metadata")
                        data = json.loads(output)
                        info = []

                        for stream in data['streams']:
                            stream_info = []
                            if 'codec_name' in stream:
                                stream_info += [stream['codec_name']]
                            if 'width' in stream:
                                stream_info += ["%sx%s" % (stream['width'], stream['height'])]
                            if 'channels' in stream:
                                stream_info += ["%sch" % stream['channels']]
                            if 'tags' in stream and 'language' in stream['tags']:
                                stream_info += ["%s" % stream['tags']['language']]
                            stream_info = " ".join(stream_info)
                            info.append(stream_info)
                        info = " | ".join(info)

                        files[path] = info

        log.info("XX get_info exit")
        return media_info
