/*
Script: mediainfo.js
    The client-side javascript code for the MediaInfo plugin.

Copyright:
    (C) David Feltell 2018 <dave@feltell.net>

    This file is part of MediaInfo and is licensed under GNU General Public License 3.0, or later, with
    the additional special exception to link portions of this program with the OpenSSL library.
    See LICENSE for more details.
*/

MediaInfoPlugin = Ext.extend(Deluge.Plugin, {
    constructor: function(config) {
        config = Ext.apply({
            name: 'MediaInfo'
        }, config);
        MediaInfoPlugin.superclass.constructor.call(this, config);
    },

    onDisable: function() {
        deluge.preferences.removePage(this.prefsPage);
    },

    onEnable: function() {
        this.prefsPage = deluge.preferences.addPage(new Deluge.ux.preferences.MediaInfoPage());
    }
});
new MediaInfoPlugin();
