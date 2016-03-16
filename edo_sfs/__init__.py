# encoding: utf-8
import os
from zopen.frs import FRS
import mimetypes

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
        self.frs.mapSitepath2Vpath( u'/', u'/sites' )

    def create_site(self, site_name):
        """ create a site """

    def remove_site(self, site_name):
        """ remove a site """

    def _get_vpath(self, site_name, key):
        zpath = '/'.join(['/wo', site_name, key])
        # 历史版本，直接找到对应的历史版本文件夹
        if '/++versions++/' in zpath:
            zpath, version = zpath.split('/++versions++/')
            zpath = zpath.split('/')
            zpath.insert(-1, self.frs.dotfrs)
            #_, ext = os.path.splitext(site_path[-1])
            zpath.append('archived')
            zpath.append(version)
            zpath = '/'.join(zpath)
        return self.frs.sitepath2Vpath(zpath)

    def get_data(self, site_name, key):
        vpath = self._get_vpath(site_name, key)
        return self.frs.open(vpath, 'rb').read()

    def get_stream(self, site_name, key):
        vpath = self._get_vpath(site_name, key)
        return self.frs.open(vpath, 'rb')

    def get_cached_data(self, site_name, mime, key, subfile=""):
        vpath = self._get_vpath(site_name, key)

        if subfile:
            file_name = subfile
        else:
            ext = mimetypes.guess_extension(mime)
            file_name = 'transformed' + ext

        cache_path = os.path.join(self.frs.getCacheFolder(vpath, mime.replace('/', '_')), file_name)
        try:
            return open(cache_path, 'rb').read()
        except:
            return 'N/A'

    def put_data(self, site_name, key, data, mime_type=''):
        vpath = self.frs.sitepath2Vpath(zpath)
        ospath = self.frs.ospath(vpath)
        #将文档的内容写入文件系统
        dirpath = os.path.dirname(ospath)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        # 先复制到临时文件上，在覆盖目标文档
        temp_file = tempfile.mktemp(dir=dirpath)
        try:
            # 支持流式存储
            with open(temp_file,'wb') as fd:
                if isinstance(data, StringTypes):
                    fd.write(data)
                else:
                    # catch the OverflowError: Python int too large to convert to C long
                    #for block in data:
                    #    fd.write(block)
                    try:
                        content_length = max(-1, getRequest().get('CONTENT_LENGTH', -1))
                    except:
                        content_length = -1

                    content_length = int(content_length)
                    bufsize = getattr(data, 'bufsize', 131072) # 1024*128 = 131072

                    if content_length >0:
                        # 支持expect 100-continue HTTP协议
                        # 在最后，如果上传文件还剩余1KB需要上传，但是data.read读取大于1KB会令socket抛出timeout错误
                        while content_length > 0:
                            n = min(content_length, bufsize)
                            readbuffer = data.read(n)
                            read_buf_length = len(readbuffer)
                            if not read_buf_length > 0:
                                break
                            fd.write(readbuffer)
                            content_length -= read_buf_length
                    else:
                        shutil.copyfileobj(data, fd, bufsize)
        except:
            os.remove(temp_file)
            raise

        #删除缓存文件
        if os.path.exists(ospath):
            frs.removeCache(vpath)

        #shutil.move(temp_file, ospath)
        move_file(temp_file, ospath)
        return os.path.getsize(temp_file)

    def put_file(self, site_name, key, file_obj, mime_type=''):
        pass

    def remove(self, site_name, key):
        pass

    def put_cache_data(self, site_name, key, cache_name, data, mime_type):
        pass

    def put_cache_file(self, site_name, key, cache_name, file_obj, mime_type):
        pass

    def remove_cache(self, site_name, key, cache_name):
        pass

_sfs = {}
def register_sfs(sfs, name='default'):
    _sfs[name] = sfs

def get_sfs(name='default'):
    return _sfs[name]

