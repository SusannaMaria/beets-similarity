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

        self.parser.add_option(
            u'-r', u'--results', dest='results',
            action='store', default='10',
            help=u'Limit the results'
        )

        self.parser.add_option(
            u'-m', u'--m3u', dest='m3u',
            action='store', default=None,
            help=u'create M3U'
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
            options.import_xtractor=True
        self.handle_main_task(options)

    def handle_main_task(self,options):
        self._say("Your journey starts here...", log_only=False)
        if options.import_xtractor:
            vec_length=len([str(x) for x in self.config['vectors']])
            self.client.recreate_collection(
                collection_name=str(self.config["qdrant_collection"]),
                vectors_config=models.VectorParams(size=vec_length, distance=models.Distance.COSINE),                
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

                except (TypeError, KeyError):
                    continue
                if len(vec_values) == vec_length:
                    pt_structs.append(PointStruct( id=id, vector=vec_values,payload={"mb_trackid": item['mb_trackid'],"mb_artistid": item['mb_artistid'],"albumartist": item['albumartist'],"album": item['album'],"title": item['title']}))

                    id +=1 
                    print( item['mb_trackid'])

            self.client.upsert(
                collection_name=str(self.config["qdrant_collection"]),
                points=pt_structs
            )
            
            return
                

        items = self.lib.items(self.query)
        if options.m3u:
            m3u_writer=open(options.m3u, 'w')

        for item in items:
            print(f"{item['mb_trackid']} - {item['title']} - {item['mb_artistid']}")
            try:
                vec_array=[]
                for vector in self.config['vectors']:
                    vec_array.append(item.get(str(vector)))
                
                vec_values=[float(x) for x in vec_array]
                search_result = self.client.search(
                    collection_name=str(self.config["qdrant_collection"]),
                    query_vector=vec_values,
                    limit=100,
                    query_filter=models.Filter(must_not=[models.FieldCondition(key="mb_artistid", match=models.MatchValue(value=str(item['mb_artistid'])))])
                )
                if options.m3u:
                    m3u_writer.write(item['path'].decode("utf-8")+"\n")

                mb_artistid_arr = []
                soft_limit=1
                for search_item in search_result:
                    sim_items = self.lib.items(f'mb_trackid:{search_item.payload["mb_trackid"]}')
                    for it in sim_items:
                        if not it['mb_artistid'] in mb_artistid_arr:
                            
                            mb_artistid_arr.append(it['mb_artistid'])
                            if options.m3u:
                                m3u_writer.write(it['path'].decode("utf-8")+"\n")
                            print(f"{it['albumartist']} - {it['album']} - {it['title']}")
                            if soft_limit>int(options.results):
                                break
                            soft_limit+=1
                    if soft_limit>int(options.results):
                        break
            except KeyError as err:
                self._say(f"Keyerror {err}", is_error=True)
        m3u_writer.close()

    def show_version_information(self):
        self._say("{pt}({pn}) plugin for Beets: v{ver}".format(
            pt=common.plg_ns['__PACKAGE_TITLE__'],
            pn=common.plg_ns['__PACKAGE_NAME__'],
            ver=common.plg_ns['__version__']
        ), log_only=False)

    @staticmethod
    def _say(msg, log_only=True, is_error=False):
        common.say(msg, log_only, is_error)
