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


from setuptools import find_packages, setup

__plugin_name__ = 'MediaInfo'
__author__ = 'David Feltell'
__author_email__ = 'dave@feltell.net'
__version__ = '0.1'
__url__ = ''
__license__ = 'GPLv3'
__description__ = ''
__long_description__ = """"""
__pkg_data__ = {'deluge.plugins.'+__plugin_name__.lower(): ['template/*', 'data/*']}

setup(
    name=__plugin_name__,
    version=__version__,
    description=__description__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license=__license__,
    long_description=__long_description__,

    packages=find_packages(),
    namespace_packages=['deluge', 'deluge.plugins'],
    package_data=__pkg_data__,

    entry_points="""
    [deluge.plugin.core]
    %s = deluge.plugins.%s:CorePlugin
    [deluge.plugin.gtkui]
    %s = deluge.plugins.%s:GtkUIPlugin
    [deluge.plugin.web]
    %s = deluge.plugins.%s:WebUIPlugin
    """ % ((__plugin_name__, __plugin_name__.lower()) * 3)
)
