#!/usr/bin/env python3

"""
Combining In-Memory and Disk Caching

Combining diskcache with LRUCache to keep data in memory and limit I/O.
Preloads the entire cache to memory, then doesn't write to diskcache until the end
"""

import cachetools
from diskcache import Cache

# Initialize disk cache
cache_dir = 'cache_directory'
disk_cache = Cache(cache_dir)

# Initialize in-memory LRU cache
in_memory_cache = cachetools.LRUCache(maxsize=1000)
for key in disk_cache:
    in_memory_cache[key] = disk_cache[key]

# Function to get value from in-memory cache
def get_from_cache(key):
    return in_memory_cache.get(key)

# Function to set value in in-memory cache
def set_in_cache(key, value):
    # Set the value in both caches
    in_memory_cache[key] = value

# Function to save in-memory cache back to disk
def save_to_disk():
    disk_cache.clear()
    for key, value in in_memory_cache.items():
        disk_cache[key] = value
    disk_cache.close()

# Preload data into memory
print(f"Preloading {len(in_memory_cache)} items into memory.")

# # Preload data into the caches
# for i in range(10000):
#     set_in_cache(i, i * i)
#
# # Access cached data
# print(get_from_cache(5000))  # Output: 25000000

# Perform operations in-memory
set_in_cache('key1', 'value1')
set_in_cache('key2', [1, 2, 3])
print(get_from_cache('key1'))  # Output: value1
print(get_from_cache('key2'))  # Output: [1, 2, 3]

# Save updated data back to disk before shutting down
save_to_disk()
print("Data saved back to disk.")
