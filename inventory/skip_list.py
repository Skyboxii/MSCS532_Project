"""
Skip list: a probabilistic ordered map (Pugh, 1990).

Used as the price index, keyed by (price, sku). Search, insert, and delete
take O(log n) expected time, and an in-order scan from any key supports
price-range queries in O(log n + k) for k results.
"""

import random


class _Node:
    __slots__ = ("key", "value", "forward")

    def __init__(self, key, value, level):
        self.key = key
        self.value = value
        self.forward = [None] * level   # forward[i] = next node on level i


class SkipList:
    """Ordered map from comparable keys to values."""

    MAX_LEVEL = 32      # supports ~2^32 keys at P = 0.5
    P = 0.5             # probability a node is promoted to the next level

    def __init__(self, seed=None):
        self._head = _Node(None, None, self.MAX_LEVEL)
        self._level = 1                 # number of levels currently in use
        self._size = 0
        self._rng = random.Random(seed)

    def _random_level(self):
        """Geometric level: 1 with prob. 1/2, 2 with prob. 1/4, ..."""
        level = 1
        while level < self.MAX_LEVEL and self._rng.random() < self.P:
            level += 1
        return level

    def _predecessors(self, key):
        """
        For each level i, find the rightmost node whose key is < key.
        These are the nodes whose forward pointers change on insert/delete.
        """
        update = [self._head] * self.MAX_LEVEL
        x = self._head
        for i in reversed(range(self._level)):
            while x.forward[i] is not None and x.forward[i].key < key:
                x = x.forward[i]
            update[i] = x
        return update

    def insert(self, key, value=None):
        """Insert key (or replace its value). O(log n) expected."""
        update = self._predecessors(key)
        nxt = update[0].forward[0]
        if nxt is not None and nxt.key == key:
            nxt.value = value
            return
        level = self._random_level()
        if level > self._level:
            self._level = level         # update[] already points at head there
        node = _Node(key, value, level)
        for i in range(level):          # splice the node into each level
            node.forward[i] = update[i].forward[i]
            update[i].forward[i] = node
        self._size += 1

    def remove(self, key):
        """Delete key and return its value. Raises KeyError if absent."""
        update = self._predecessors(key)
        node = update[0].forward[0]
        if node is None or node.key != key:
            raise KeyError(key)
        for i in range(len(node.forward)):
            update[i].forward[i] = node.forward[i]
        while self._level > 1 and self._head.forward[self._level - 1] is None:
            self._level -= 1            # drop now-empty top levels
        self._size -= 1
        return node.value

    def get(self, key, default=None):
        node = self._predecessors(key)[0].forward[0]
        return node.value if node is not None and node.key == key else default

    def iter_from(self, key):
        """Yield (key, value) pairs in order, starting at the first key >= key."""
        node = self._predecessors(key)[0].forward[0]
        while node is not None:
            yield node.key, node.value
            node = node.forward[0]

    def __iter__(self):
        node = self._head.forward[0]
        while node is not None:
            yield node.key, node.value
            node = node.forward[0]

    def __contains__(self, key):
        node = self._predecessors(key)[0].forward[0]
        return node is not None and node.key == key

    def __len__(self):
        return self._size
