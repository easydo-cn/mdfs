# encoding: utf-8

class BaseDevice:

    def __init__(self, name, title='', options={}):
        self.name = name
        self.title = title
        self.options = options
    
    def gen_key(self, prefix='', suffix=''):
        """ 生成一个未用的key """
    
    def put_data(self, key, data):
        """ 直接存储一个数据，适合小文件 """

    def put_stream(self, key, file_obj):
        """ 通过iterator来存储一个文件，适合大文件 """

    def remove(self, key):
        """ 删除key文件 """
    
    def get_data(self, key):
        """ 根据key返回文件内容，不适合大文件 """

    def get_stream(self, key):
        """ 返回文件的一个stream对象，可以通过iterator来逐步得到文件，适合大文件 """

class StorageDeviceManager:
    """ 支持缓存多设备的文件存储管理器 """

    devices = {}

    def add(self, device, cache_device):
        self.devices[device.name] = (device, cache_device)

    def get_device(self, name):
        return self.devices[name]

    def gen_key(self, name, prefix='', suffix=''):
        """ 生成一个未用的key """
        device, cache_device = self.devices[name]
        return device.gen_key(prefix, suffix)

    def get_cache_key(self, key, mime='', subpath=''):
        mime = mime.replace('/', '_')
        return key + '/.frs.' + mime + '/' + subpath

    def os_path(self, name, key):
        device, cache_device = self.devices[name]
        return device.os_path(key)

    def cache_os_path(self, name, key):
        device, cache_device = self.devices[name]
        return cache_device.os_path(key)

    def remove(self, name, key):
        """ 删除一个文件，同时删除缓存 """
        device, cache_device = self.devices[name]
        device.remove(key)
        # TODO 需要删除所有的缓存
        cache_device.remove(self.get_cache_key(key))

    def get_data(self, name, key):
        """ 读取数据 """
        device, cache_device = self.devices[name]
        return device.get_data(key)

    def get_stream(self, name, key):
        """ 读取数据流 """
        device, cache_device = self.devices[name]
        return device.get_stream(key)

    def put_data(self, name, key, data):
        """ 存储数据 """
        device, cache_device = self.devices[name]
        return device.put_data(key, data)

    def put_stream(self, name, key, stream):
        """ 存储文件流 """
        device, cache_device = self.devices[name]
        return device.put_stream(key, stream)

    def get_cache_data(self, name, key, mime, subpath):
        """ 读取缓存数据 """
        device, cache_device = self.devices[name]
        key = self.get_cache_key(key, mime, subpath)
        return cache_device.get_data(key)

    def get_cache_stream(self, name, key, mime, subpath):
        """ 读取缓存数据流 """
        device, cache_device = self.devices[name]
        key = self.get_cache_key(key, mime, subpath)
        return cache_device.get_stream(key)

    def put_cache_data(self, name, key, mime, subpath, data):
        """ 存储缓存数据 """
        device, cache_device = self.devices[name]
        key = self.get_cache_key(key, mime, subpath)
        return cache_device.put_data(key, data)

    def put_cache_stream(self, name, key, mime, subpath, stream):
        """ 存储缓存文件流 """
        device, cache_device = self.devices[name]
        key = self.get_cache_key(key, mime, subpath)
        return cache_device.put_stream(key, stream)

