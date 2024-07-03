#!/usr/bin/env python3

"""
[in progress] A custom dict type to allow mutable items (such as dicts and lists) as keys
"""


class CustomDict:
    """
    A custom dictionary class that allows using mutable objects such as dicts and lists as keys.
    Internally, it stores items as a list of (key, value) pairs and simulates dictionary behavior.
    """

    def __init__(self):
        """
        Initialize the CustomDict.
        """
        self.data = []

    def __setitem__(self, key, value):
        """
        Set the value for the specified key. If the key exists, update its value; otherwise, add a new (key, value) pair.

        Parameters:
        key (any): The key to set.
        value (any): The value to be associated with the key.
        """
        for i, (k, v) in enumerate(self.data):
            if k is key or k == key:
                self.data[i] = (key, value)
                return
        self.data.append((key, value))

    def __getitem__(self, key):
        """
        Get the value associated with the specified key.

        Parameters:
        key (any): The key to retrieve.

        Returns:
        any: The value associated with the key.

        Raises:
        KeyError: If the key does not exist.
        """
        for k, v in self.data:
            if k is key or k == key:
                return v
        raise KeyError(f"Key {key} not found")

    def __delitem__(self, key):
        """
        Delete the value associated with the specified key.

        Parameters:
        key (any): The key to delete.

        Raises:
        KeyError: If the key does not exist.
        """
        for i, (k, v) in enumerate(self.data):
            if k is key or k == key:
                del self.data[i]
                return
        raise KeyError(f"Key {key} not found")

    def __contains__(self, key):
        """
        Check if the specified key exists in the dictionary.

        Parameters:
        key (any): The key to check.

        Returns:
        bool: True if the key exists, False otherwise.
        """
        for k, v in self.data:
            if k is key or k == key:
                return True
        return False

    def __repr__(self):
        """
        Return the string representation of the CustomDict.

        Returns:
        str: The string representation of the CustomDict.
        """
        return f"CustomDict({self.data})"

    def keys(self):
        """
        Get the keys of the CustomDict.

        Returns:
        list: A list of keys.
        """
        return [k for k, v in self.data]

    def values(self):
        """
        Get the values of the CustomDict.

        Returns:
        list: A list of values.
        """
        return [v for k, v in self.data]

    def items(self):
        """
        Get the items of the CustomDict.

        Returns:
        list: A list of (key, value) pairs.
        """
        return self.data[:]


cd = CustomDict()

# Using a list as a key
key_list = [1, 2, 3]
cd[key_list] = "List as a key"

# Using a dict as a key
key_dict = {'a': 1, 'b': 2}
cd[key_dict] = "Dict as a key"

print(cd[key_list])  # Output: List as a key
print(cd[key_dict])  # Output: Dict as a key

# Modify the key
key_list.append(4)
print(cd[key_list])  # Output: List as a key

# Check if keys exist
print(key_list in cd)  # Output: True
print(key_dict in cd)  # Output: True

# Get all keys, values, and items
print(cd.keys())    # Output: [[1, 2, 3, 4], {'a': 1, 'b': 2}]
print(cd.values())  # Output: ['List as a key', 'Dict as a key']
print(cd.items())   # Output: [([1, 2, 3, 4], 'List as a key'), ({'a': 1, 'b': 2}, 'Dict as a key')]
