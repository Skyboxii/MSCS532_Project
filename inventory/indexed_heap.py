"""
Indexed binary min-heap (Williams, 1964), with a position map so any item's
priority can be changed or the item removed in O(log n).

Used as the stock-alert index: priority = quantity - reorder_point, so the
root is always the product furthest below (or closest to) its reorder point.
"""

from .hash_table import HashTable


class IndexedMinHeap:
    """Min-heap of (priority, item) entries with O(log n) update and remove."""

    def __init__(self):
        self._heap = []                 # list of [priority, item]
        self._pos = HashTable()         # item -> index in self._heap

    # -- heap maintenance -----------------------------------------------------

    def _less(self, i, j):
        # Break priority ties by item so ordering is deterministic.
        return self._heap[i] < self._heap[j]

    def _swap(self, i, j):
        h = self._heap
        h[i], h[j] = h[j], h[i]
        self._pos[h[i][1]] = i
        self._pos[h[j][1]] = j

    def _sift_up(self, i):
        while i > 0:
            parent = (i - 1) // 2
            if not self._less(i, parent):
                break
            self._swap(i, parent)
            i = parent

    def _sift_down(self, i):
        n = len(self._heap)
        while True:
            smallest = i
            for child in (2 * i + 1, 2 * i + 2):
                if child < n and self._less(child, smallest):
                    smallest = child
            if smallest == i:
                break
            self._swap(i, smallest)
            i = smallest

    # -- public API -----------------------------------------------------------

    def push(self, item, priority):
        """Add a new item. O(log n)."""
        if item in self._pos:
            raise KeyError(f"{item!r} is already in the heap")
        self._heap.append([priority, item])
        self._pos[item] = len(self._heap) - 1
        self._sift_up(len(self._heap) - 1)

    def update(self, item, priority):
        """Change an item's priority and restore heap order. O(log n)."""
        i = self._pos[item]
        old = self._heap[i][0]
        self._heap[i][0] = priority
        if priority < old:
            self._sift_up(i)
        elif priority > old:
            self._sift_down(i)

    def remove(self, item):
        """Remove an arbitrary item. O(log n)."""
        i = self._pos[item]
        last = len(self._heap) - 1
        if i != last:
            self._swap(i, last)
        self._heap.pop()
        del self._pos[item]
        if i < len(self._heap):         # moved entry may need to go either way
            self._sift_up(i)
            self._sift_down(i)

    def peek(self):
        """Return (item, priority) with the smallest priority. O(1)."""
        if not self._heap:
            raise IndexError("peek from empty heap")
        priority, item = self._heap[0]
        return item, priority

    def pop(self):
        """Remove and return (item, priority) with the smallest priority."""
        item, priority = self.peek()
        self.remove(item)
        return item, priority

    def items_at_or_below(self, threshold):
        """
        Yield (item, priority) for every entry with priority <= threshold.

        Any subtree whose root exceeds the threshold is skipped entirely,
        because heap order guarantees its descendants are larger too. The
        cost is therefore O(k) for k results, not O(n).
        """
        stack = [0] if self._heap else []
        while stack:
            i = stack.pop()
            priority, item = self._heap[i]
            if priority > threshold:
                continue
            yield item, priority
            for child in (2 * i + 1, 2 * i + 2):
                if child < len(self._heap):
                    stack.append(child)

    def priority_of(self, item):
        return self._heap[self._pos[item]][0]

    def __contains__(self, item):
        return item in self._pos

    def __len__(self):
        return len(self._heap)
