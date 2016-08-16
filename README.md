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

## 已经支持的设备

- vfs：文件系统访问
- ceph: s3接口
- aliyun: oss
- mirror：镜像存储


