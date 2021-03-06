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

import gtk
import logging

import deluge.component as component
from deluge.plugins.pluginbase import GtkPluginBase
from deluge.ui.client import client

from .common import get_resource

log = logging.getLogger(__name__)


class GtkUI(GtkPluginBase):

    def enable(self):
        try:
            log.info("Enabling MediaInfo GTK plugin")
            self.media_info = {}
            self._glade = gtk.glade.XML(get_resource('config.glade'))

            component.get('Preferences').add_page('MediaInfo', self._glade.get_widget('prefs_box'))
            component.get('PluginManager').register_hook('on_apply_prefs', self.on_apply_prefs)
            component.get('PluginManager').register_hook('on_show_prefs', self.on_show_prefs)

            # Media column
            self._column = gtk.TreeViewColumn(_('Media Streams'))
            render = gtk.CellRendererText()
            self._column.pack_start(render, False)
            self._column.set_cell_data_func(render, cell_data_media, self)
            self._column.set_sort_column_id(5)
            self._column.set_clickable(True)
            self._column.set_resizable(True)
            self._column.set_expand(False)
            self._column.set_min_width(50)
            self._column.set_reorderable(True)

            self.tab = component.get('TorrentDetails').tabs['Files']
            self.tab.listview.append_column(self._column)
        except Exception:
            log.exception("Error enabling")
            raise

    def disable(self):
        self.tab.listview.remove_column(self._column)
        self._column = None
        component.get('Preferences').remove_page('MediaInfo')
        component.get('PluginManager').deregister_hook('on_apply_prefs', self.on_apply_prefs)
        component.get('PluginManager').deregister_hook('on_show_prefs', self.on_show_prefs)

    def update(self):
        try:
            if self.tab.torrent_id is None:
                return
            if (
                self.media_info.get(self.tab.torrent_id) and
                self.media_info[self.tab.torrent_id]['complete']
            ):
                return

            client.mediainfo.get_info(self.tab.torrent_id).addCallback(
                lambda media_info: self._cb_get_media_info(media_info, self.tab.torrent_id)
            )
        except Exception:
            log.exception("Error updating media info (gtk)")
            raise

    def on_apply_prefs(self):
        log.info('Applying prefs for MediaInfo')
        config = {
            'ffprobe_bin': self._glade.get_widget('txt_ffprobe_bin').get_text()
        }
        client.mediainfo.set_config(config)

    def on_show_prefs(self):
        client.mediainfo.get_config().addCallback(self._cb_get_config)

    def _cb_get_config(self, config):
        """ Callback for on show_prefs
        """
        self._glade.get_widget('txt_ffprobe_bin').set_text(config['ffprobe_bin'])

    def _cb_get_media_info(self, media_info, torrent_id):
        if self._column is None:
            return
        if torrent_id != self.tab.torrent_id:
            return
        prev_info = self.media_info.get(torrent_id)
        self.media_info[torrent_id] = media_info
        if prev_info != media_info:
            self.tab.listview.queue_draw()


def cell_data_media(column, cell, model, row, data):
    try:
        # This is a folder, so lets just set it blank for now
        if model.get_value(row, 5) == -1:
            cell.set_property('text', '')
            return
        # No media info for this torrent available yet.
        media_info = data.media_info.get(data.tab.torrent_id)
        if media_info is None:
            cell.set_property('text', '...')
            return
        file_media_info = media_info['files'][data.tab.get_file_path(row)]
        # File didn't pass file extension regex, so not even checked.
        if file_media_info is False:
            cell.set_property('text', '')
            return
        # File is awaiting a positive result from ffprobe.
        if file_media_info is None:
            cell.set_property('text', '...')
            return
        # ffprobe complete, show results.
        cell.set_property('text', file_media_info['streams'])
    except Exception:
        log.exception("Error rendering media info")
        raise

