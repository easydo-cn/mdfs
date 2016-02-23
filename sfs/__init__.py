# encoding: utf-8
import os
from zopen.frs import FRS

class SFS:

    def __init__(self, data_dir, cache_dir):
        # 初始化frs
        self.frs = FRS()
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self.frs.setCacheRoot(unicode(cache_dir))
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        self.frs.mount(u'sites', unicode(data_dir))

    def create_site(self, site_name):
        """ create a site """

    def remove_site(self, site_name):
        """ remove a site """

    def put_data(self, site_name, key, data, mime_type):
        pass

    def put_file(self, site_name, key, file_obj, mime_type):
        pass

    def remove(self, site_name, key):
        pass

    def put_cache_data(self, site_name, key, cache_name, data, mime_type):
        pass

    def put_cache_file(self, site_name, key, cache_name, file_obj, mime_type):
        pass

    def remove_cache(self, site_name, key, cache_name):
        pass
