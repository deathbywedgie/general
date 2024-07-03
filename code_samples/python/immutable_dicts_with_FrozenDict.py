#!/usr/bin/env python3

"""
Simplistic example: creating immutable dicts that can be used as dict keys
"""

from frozendict import frozendict


fd = frozendict({'a': 1, 'b': 2})
nested_dict = {fd: 'value'}

print(nested_dict[fd])  # Output: value
