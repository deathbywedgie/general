import diskcache
import os
import time


DEFAULT_CACHE_DIR = '/tmp'


# ToDo REPLACE ME
class FakeLogger:
    """ Placeholder """

    def __init(self):
        self.debug = self.info = self.msg
    
    def msg(self, msg, *args, **kwargs):
        ...


class ResourceCache:

    read_expiry = 3600
    write_expiry = 86400 * 365  # Store for a year but don't actually use it unless it's newer than the read expiry

    def __init__(self, cache_label: str, cache_dir: str = None, read_expiry: int = None, write_expiry: int = None):
        if not cache_label or not cache_label.strip():
            raise ValueError('Cache label cannot be blank')

        self.__log = FakeLogger()

        cache_dir = os.path.join(
            cache_dir.strip() if cache_dir and cache_dir.strip() else DEFAULT_CACHE_DIR,
            cache_label
        )
        if read_expiry:
            self.read_expiry = int(read_expiry)

        if write_expiry:
            self.read_expiry = int(write_expiry)

        self.__log.debug(f"Cache initializing", dir=cache_dir, default_read_expiry=self.read_expiry)

        # Check diskcache.DEFAULT_SETTINGS for settings to customize and to ensure that cache is large enough
        self.cache = diskcache.Cache(cache_dir, eviction_policy='least-recently-used')

    def store(self, key, result):
        self.__log.debug("Storing resource cache", resource_type=key)
        self.cache.set(key, result, expire=self.write_expiry)

    def delete(self, key):
        self.__log.debug("Deleting resource cache", resource_type=key)
        self.cache.delete(key=key)

    def get_resources(self, key, source_function=None, *func_args, read_expiry: int = None, **func_kwargs):
        read_expiry = read_expiry if read_expiry is not None else self.read_expiry
        if read_expiry > 0:
            self.__log.debug("Fetching cache", resource_type=key)
            value, expire_time = self.cache.get(key, expire_time=True)
            if not value:
                self.__log.debug("No cached value found", resource_type=key)
            else:
                cache_age = int(self.write_expiry - (expire_time - int(time.time())))
                self.__log.debug("Cache found", resource_type=key, expire_time=expire_time, age=cache_age, expiry=read_expiry)
                if cache_age >= read_expiry:
                    self.__log.debug("Cache age not allowed", resource_type=key, age=cache_age, expiry=read_expiry)
                else:
                    self.__log.debug("Cache age is allowed", resource_type=key, age=cache_age, expiry=read_expiry)
                    return value, cache_age

        if source_function:
            self.__log.info(f"No valid cache returned for type {key}; fetching resources from source")
            self.store(key=key, result=source_function(*func_args, **func_kwargs))
            value, expire_time = self.cache.get(key, expire_time=True)
            return value, 0
        return None, None

    @property
    def cache_dir(self):
        return self.cache.directory
