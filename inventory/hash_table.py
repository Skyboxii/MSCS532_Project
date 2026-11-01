"""
Hash table with open addressing and linear probing.

Used as the primary SKU -> Product index. Average-case O(1) get/put/remove
while the load factor stays bounded (Knuth, 1998, Section 6.4).
"""

_DELETED = object()     # tombstone: marks a removed slot so probe chains stay intact


class HashTable:
    """Map hashable, non-None keys to values."""

    MIN_CAPACITY = 8
    MAX_LOAD = 0.6      # resize once live entries + tombstones exceed 60% of slots

    def __init__(self, capacity=MIN_CAPACITY):
        cap = self.MIN_CAPACITY
        while cap < capacity:
            cap *= 2                    # power of two so we can mask instead of mod
        self._keys = [None] * cap
        self._values = [None] * cap
        self._size = 0                  # live entries
        self._used = 0                  # live entries + tombstones

    # -- core probing ---------------------------------------------------------

    def _probe(self, key):
        """
        Walk the probe sequence for key.

        Returns (index_of_key or None, first_reusable_slot). The first reusable
        slot is the earliest tombstone seen, or the empty slot that ended the
        search, so inserts recycle tombstones instead of growing the chain.
        """
        if key is None:
            raise TypeError("HashTable keys cannot be None")
        mask = len(self._keys) - 1
        i = hash(key) & mask
        first_free = None
        while True:
            k = self._keys[i]
            if k is None:                           # end of chain: key absent
                return None, (i if first_free is None else first_free)
            if k is _DELETED:
                if first_free is None:
                    first_free = i
            elif k == key:
                return i, first_free
            i = (i + 1) & mask                      # linear probing

    def _resize(self):
        """Rehash all live entries, doubling capacity if the table is busy.
        Rehashing also discards tombstones."""
        cap = len(self._keys)
        if self._size > cap * self.MAX_LOAD / 2:
            cap *= 2
        old = zip(self._keys, self._values)
        self._keys = [None] * cap
        self._values = [None] * cap
        self._size = self._used = 0
        for k, v in old:
            if k is not None and k is not _DELETED:
                self.put(k, v)

    # -- public API -----------------------------------------------------------

    def put(self, key, value):
        """Insert or replace the value for key. Amortized O(1)."""
        idx, free = self._probe(key)
        if idx is not None:
            self._values[idx] = value
            return
        if self._keys[free] is None:                # consuming a fresh slot
            self._used += 1
        self._keys[free] = key
        self._values[free] = value
        self._size += 1
        if self._used > len(self._keys) * self.MAX_LOAD:
            self._resize()

    def get(self, key, default=None):
        """Return the value for key, or default if absent. Average O(1)."""
        idx, _ = self._probe(key)
        return default if idx is None else self._values[idx]

    def remove(self, key):
        """Delete key and return its value. Raises KeyError if absent."""
        idx, _ = self._probe(key)
        if idx is None:
            raise KeyError(key)
        value = self._values[idx]
        self._keys[idx] = _DELETED
        self._values[idx] = None
        self._size -= 1
        return value

    def __getitem__(self, key):
        idx, _ = self._probe(key)
        if idx is None:
            raise KeyError(key)
        return self._values[idx]

    __setitem__ = put
    __delitem__ = remove

    def __contains__(self, key):
        return self._probe(key)[0] is not None

    def __len__(self):
        return self._size

    def items(self):
        """Yield (key, value) pairs in slot order. O(capacity)."""
        for k, v in zip(self._keys, self._values):
            if k is not None and k is not _DELETED:
                yield k, v

    def __iter__(self):
        for k, _ in self.items():
            yield k

    def values(self):
        for _, v in self.items():
            yield v

    @property
    def load_factor(self):
        return self._used / len(self._keys)
