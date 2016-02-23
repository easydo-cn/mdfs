# sfs: Site File Storage

SFS is wrapper for simple file storage. File can be stored in the filesystem directly or in the cloud.

## Features

- Support multi-sites. Each site has its own storage.
- File caches: to store file generated information

## API

  sfs = SFS(path, cache_path, cloud....)
  sfs.create_site_space(site_name)
  sfs.remove_site_space(site_name)
  sfs.put_data(site_name, key, mime_type)
  sfs.put_file(site_name, key, file_obj, mime_type)
  sfs.remove(site_name, xxx)
  sfs.read(site_name, xxx)
  sfs.save_cache
  sfs.remove_cache

## Dependency

- zopen.frs
