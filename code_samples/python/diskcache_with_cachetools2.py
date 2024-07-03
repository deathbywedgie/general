#!/usr/bin/env python3

"""
Combining In-Memory and Disk Caching

Combining diskcache with LRUCache to keep data in memory and limit I/O.
In theory, preloads the entire cache to memory
"""

from diskcache import Cache

# Initialize disk cache
cache_dir = 'cache_directory'
disk_cache = Cache(cache_dir)

# Load all data into memory
in_memory_cache = {}
for key in disk_cache:
    in_memory_cache[key] = disk_cache[key]

# Function to get value from in-memory cache
def get_from_cache(key):
    return in_memory_cache.get(key)

# Function to set value in in-memory cache
def set_in_cache(key, value):
    in_memory_cache[key] = value

# Function to save in-memory cache back to disk
def save_to_disk():
    disk_cache.clear()
    for key, value in in_memory_cache.items():
        disk_cache[key] = value
    disk_cache.close()

# Preload data into memory
print(f"Preloading {len(in_memory_cache)} items into memory.")

# Perform operations in-memory
set_in_cache('key1', 'value1')
set_in_cache('key2', [1, 2, 3])
print(get_from_cache('key1'))  # Output: value1
print(get_from_cache('key2'))  # Output: [1, 2, 3]

# Save updated data back to disk before shutting down
save_to_disk()
print("Data saved back to disk.")
