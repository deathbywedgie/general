#!/usr/bin/env python3

"""
Combining In-Memory and Disk Caching

Combining diskcache with LRUCache to keep data in memory and limit I/O.
Still depends on fetching each item from diskcache for the first time.
"""

import cachetools
from diskcache import Cache

# Initialize disk cache
disk_cache = Cache('cache_directory')

# Initialize in-memory LRU cache
in_memory_cache = cachetools.LRUCache(maxsize=1000)


def get_from_cache(key):
    # Try to get the value from in-memory cache
    if key in in_memory_cache:
        return in_memory_cache[key]

    # If not found in-memory, get from disk cache
    if key in disk_cache:
        value = disk_cache[key]
        # Store in in-memory cache for faster future access
        in_memory_cache[key] = value
        return value

    # If not found in either, raise KeyError
    raise KeyError(f"Key {key} not found")


def set_in_cache(key, value):
    # Set the value in both caches
    in_memory_cache[key] = value
    disk_cache[key] = value


# Preload data into the caches
for i in range(10000):
    set_in_cache(i, i * i)

# Access cached data
print(get_from_cache(5000))  # Output: 25000000
