#  Copyright: Copyright (c) 2020., <AUTHOR>
#  Author: <AUTHOR> <EMAIL>
#  License: See LICENSE.txt

from optparse import OptionParser

from beets.library import Library
from beets.ui import Subcommand, decargs
from confuse import Subview

from beetsplug.similarity import common


class SimilarityCommand(Subcommand):
    config: Subview = None
    lib: Library = None
    query = None
    parser: OptionParser = None

    def __init__(self, cfg):
        self.config = cfg

        self.parser = OptionParser(
            usage='beet {plg} [options] [QUERY...]'.format(
                plg=common.plg_ns['__PLUGIN_NAME__']
            ))

        self.parser.add_option(
            '-v', '--version',
            action='store_true', dest='version', default=False,
            help=u'show plugin version'
        )

        self.parser.add_option(
            '-i', '--import',
            action='store_true', dest='import', default=False,
            help=u'(re)import dataset into qdrant'
        )

        self.parser.add_option(
            u'-u', u'--url', dest='qdrant_url',
            action='store', default='http://127.0.0.1:6333',
            help=u'qdrant url to store music features generated from xtractor'
        )

        self.parser.add_option(
            u'-c', u'--collection', dest='qdrant_collection',
            action='store', default='beets_similarity',
            help=u'qdrant collection to store vectors'
        )

        super(SimilarityCommand, self).__init__(
            parser=self.parser,
            name=common.plg_ns['__PLUGIN_NAME__'],
            aliases=[common.plg_ns['__PLUGIN_ALIAS__']] if
            common.plg_ns['__PLUGIN_ALIAS__'] else [],
            help=common.plg_ns['__PLUGIN_SHORT_DESCRIPTION__']
        )

    def func(self, lib: Library, options, arguments):
        self.lib = lib
        self.query = decargs(arguments)

        if options.version:
            self.show_version_information()
            return
        
        self.handle_main_task()

    def handle_main_task(self):
        self._say("Your journey starts here...", log_only=False)

        items = self.lib.items(self.query)
        for item in items:
            print(f"{item['mb_trackid']} - {item['title']}")
            try:
                for vector in self.config['vectors']:
                    self._say(f"{vector} - {item.get(str(vector))}", log_only=False)
            except KeyError:
                self._say("xtractor based field not found, please process the beet xtractor plugin", is_error=True)


    def show_version_information(self):
        self._say("{pt}({pn}) plugin for Beets: v{ver}".format(
            pt=common.plg_ns['__PACKAGE_TITLE__'],
            pn=common.plg_ns['__PACKAGE_NAME__'],
            ver=common.plg_ns['__version__']
        ), log_only=False)

    @staticmethod
    def _say(msg, log_only=True, is_error=False):
        common.say(msg, log_only, is_error)
