#  Copyright: Copyright (c) 2020., <AUTHOR>
#  Author: <AUTHOR> <EMAIL>
#  License: See LICENSE.txt

from optparse import OptionParser

from beets.library import Library
from beets.ui import Subcommand, decargs
from confuse import Subview

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import PointStruct
from urllib.parse import urlparse

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
            action='store_true', dest='import_xtractor', default=False,
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
        
        qdrant_url = self.config["qdrant_url"]
        q_url=urlparse(str(qdrant_url)).netloc.split(":")

        self.client = QdrantClient(q_url[0], port=int(q_url[1]))
        try:
            self.client.get_collection(str(self.config["qdrant_collection"]))
        except UnexpectedResponse:
            self.client.create_collection(
                collection_name=str(self.config["qdrant_collection"]),
                vectors_config=models.VectorParams(size=100, distance=models.Distance.DOT),
            )
        self.handle_main_task(options)

    def handle_main_task(self,options):
        self._say("Your journey starts here...", log_only=False)
        if options.import_xtractor:
            self.client.recreate_collection(
                collection_name=str(self.config["qdrant_collection"]),
                vectors_config=models.VectorParams(size=7, distance=models.Distance.DOT),                
            )
            items = self.lib.items()
            id=0
            pt_structs = []
            for item in items:
                try:
                    vec_array=[]
                    for vector in self.config['vectors']:
                        vec_array.append(item.get(str(vector)))
                    
                    vec_values=[float(x) for x in vec_array]
                    #print(f"{item['mb_trackid']} - {item['title']}")
                    #print(vec_values)
                except (TypeError, KeyError):
                    continue
                if len(vec_values) == 7:
                    pt_structs.append(PointStruct( id=id, vector=vec_values,payload={"mb_trackid": item['mb_trackid'],"mb_artistid": item['mb_artistid']}))

                    id +=1 

            self.client.upsert(
                collection_name=str(self.config["qdrant_collection"]),
                points=pt_structs
            )
            
            return
                

        items = self.lib.items(self.query)
        for item in items:
            print(f"{item['mb_trackid']} - {item['title']}")
            try:
                vec_array=[]
                for vector in self.config['vectors']:
                    vec_array.append(item.get(str(vector)))
                
                vec_values=[float(x) for x in vec_array]
                search_result = self.client.search(
                    collection_name=str(self.config["qdrant_collection"]),
                    query_vector=vec_values,
                    limit=1
                )
                sim_items = self.lib.items(f'mb_trackid:{search_result[0].payload["mbid"]}')
                print(f"{sim_items[0]['mb_trackid']} - {sim_items[0]['title']}")
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
