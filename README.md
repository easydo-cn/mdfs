# mdfs: Multiple Device File Storage



## Features

- Support multi-devices: Local Filesystem, qiniu, Ceph, swift, ali....
- File caches: to store file generated information

# 多设备的文件存储系统

## 问题、需求

1. 文件可能存储在多种介质，比如本地、NAS服务器、七牛、阿里、Ceph等。

2. 实际文件可能是混合存放在多个存储设备。因此需要提供一个通用的文件存取接口，方便应用的访问。

3. 每个存储设备的文件，需要进行文件转换，转换结果需要临时保存起来。这些转换之后的文件，本质是可再生成的缓存文件。

   因此，每个设备需要关联一个缓存文件的存储设备。

## 总体方案

提供 device_name + key 的统一文件访问方法。

- 所有存储设备注册到设备管理器
- 根据device_name找到相应的设备
- 每个设备通过key进行文件的管理

## 接口

运营点存储设备管理器

    sdm = StorageDeviceManager()
    cache_device = VfsDevice(cache_path)

    vfs_device = VfsDevice(path)
    vfs_device.set_cache_device(cache_device)
    sdm.add(vfs_device)

    ceph_device = CephDevice(server, port, token)
    ceph_device.set_cache_device(cache_device)
    sdm.add(ceph_device)

    sdm.site_policy  # {site:[devices]}
    sdm.mime_policy  # {mime:[devices]}
    devices = sdm.allowed_devices(site_name, mimes)
    device = sdm.get_device(device_name)

设备文件管理

    print device.title
    print device.type
    print device.options
    print device.mimes
    print device.instance

    key = device.new_key(site_name)

    device.put_data(key, data)
    device.put_stream(key, file_obj)

    device.remove(key)

    file_content = device.get_data(key)
    file_stream = device.get_stream(key)

缓存设备

    cache_device = device.get_cache_device()
    print cache_device.type
    print cache_device.options

    cache_key = cache_device.get_cache_key(key, mime, subpath)
    cach_device.put_data(cache_key, data)
    cach_device.get_data(cache_key, data)

VFS: 虚拟文件系统

  vfs = VFS(root=path)
  os_path = vfs.ospath(key)将key映射到实际文件系统路径

- os.path.split统一
- 历史版本路径映射：

    ff/aa.doc/++versions++/1.doc
    ff/.frs/aa.doc/archive/1.doc

- CIFS/NFS
