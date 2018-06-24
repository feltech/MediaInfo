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

import deluge.configmanager
import deluge.component as component
from deluge.core.rpcserver import export
from deluge.plugins.pluginbase import CorePluginBase
from twisted.internet.utils import getProcessOutputAndValue

from .videoexts import video_exts

log = logging.getLogger(__name__)

DEFAULT_PREFS = {
    'ffprobe_bin': '/usr/bin/ffprobe'
}


class Core(CorePluginBase):
    def enable(self):
        log.info("Enabling MediaInfo Core plugin")
        self._config = deluge.configmanager.ConfigManager('mediainfo.conf', DEFAULT_PREFS)
        self._core = component.get('Core')
        self._plugin = component.get('CorePluginManager')
        self._torrent_id = None
        self._media_info = {}
        component.start([self._component_name])

    def disable(self):
        self._media_info = {}

    @export
    def set_config(self, config):
        """ Sets the config dictionary
        """
        for key in config:
            self._config[key] = config[key]
        self._config.save()

    @export
    def get_config(self):
        """ Returns the config dictionary
        """
        return self._config.config

    @export
    def get_info(self, torrent_id):
        try:
            self._torrent_id = torrent_id
            return self._media_info[torrent_id].copy() if torrent_id in self._media_info else None
        except Exception:
            log.exception("Failed to get media info for torrent id %s" % torrent_id)
            return None

    def update(self):
        try:
            media_info = self._get_media_info(self._torrent_id)
            # If we have files, but we don't have media info for all of them yet.
            if media_info is not None and not media_info['complete']:
                # Async query for media info for all elligible files.
                self._query_media_info(media_info)
        except Exception:
            log.exception("Error updating media info (core)")
            raise

    def _get_media_info(self, torrent_id):
        if torrent_id is None:
            return None

        if torrent_id not in self._media_info:
            status = self._core.get_torrent_status(
                torrent_id, ["save_path", "download_location", "files"]
            )
            if not status or not status['files']:
                return None
            media_info = {
                'complete': False,
                'root': status.get('download_location', status['save_path']),
                'files': {f['path']: None for f in status['files']}
            }
            self._media_info[torrent_id] = media_info
        else:
            media_info = self._media_info[torrent_id]

        return media_info

    def _query_media_info(self, media_info):
        root = media_info['root']
        files = media_info['files']
        is_complete = True
        for path in files:
            if files[path] and files[path]['complete']:
                continue
            # Check if file extension indicates a supported (video) file.
            if not video_exts.match(os.path.splitext(path)[1]):
                files[path] = False
                continue
            is_complete = False
            fullpath = os.path.join(root, path)
            cmd_args = [
                "-k", "3", "2", self._config['ffprobe_bin'], "-v", "quiet", "-print_format",
                "json", "-show_streams", fullpath
            ]
            log.info("Executing: %s with %s" % (self._config['ffprobe_bin'], cmd_args))
            getProcessOutputAndValue(
                "timeout", cmd_args, env=os.environ
            ).addCallback(self._update_file_in_media_info, media_info, path)

        media_info['complete'] = is_complete

    def _update_file_in_media_info(self, result, media_info, path):
        out, err, code = result
        if code == 124:
            log.warn("ffprobe terminated (timed out)")
        elif code == 137:
            log.warn("ffprobe killed (timed out and refused to die)")
        elif code:
            # Assume if ffprobe failed, it's only temporary (file not downloaded enough yet).
            log.info("No video file metadata available (yet) for %s: [%s]" % (path, code))
            log.debug("out='%s'\nerr='%s'" % (out, err))
        else:
            data = json.loads(out)
            info = []
            media_info['files'][path] = {
                'complete': "misdetection possible" not in err
            }

            for stream in data['streams']:
                stream_info = []
                if 'codec_name' in stream:
                    stream_info += [stream['codec_name']]
                if 'width' in stream:
                    stream_info += ["%sx%s" % (stream['width'], stream['height'])]
                if 'channels' in stream:
                    stream_info += ["%sch" % stream['channels']]
                if 'tags' in stream and 'language' in stream['tags']:
                    stream_info += [stream['tags']['language']]
                stream_info = " ".join(stream_info)
                info.append(stream_info)

            media_info['files'][path]['streams'] = " | ".join(info)
