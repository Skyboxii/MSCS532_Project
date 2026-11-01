"""Unit tests for the individual data structures."""

import random
import unittest

from inventory import HashTable, IndexedMinHeap, SkipList


class TestHashTable(unittest.TestCase):
    def test_put_get_replace(self):
        t = HashTable()
        t.put("A1", 1)
        t["B2"] = 2
        t.put("A1", 10)
        self.assertEqual(t["A1"], 10)
        self.assertEqual(t.get("B2"), 2)
        self.assertIsNone(t.get("missing"))
        self.assertEqual(len(t), 2)

    def test_remove_and_tombstone_reuse(self):
        t = HashTable()
        for i in range(5):
            t.put(i, i)
        t.remove(2)
        self.assertNotIn(2, t)
        self.assertIn(3, t)             # probe chain still intact past the tombstone
        with self.assertRaises(KeyError):
            t.remove(2)
        t.put(2, "back")
        self.assertEqual(t[2], "back")
        self.assertEqual(len(t), 5)

    def test_resize_keeps_load_bounded(self):
        t = HashTable()
        for i in range(10_000):
            t.put(f"SKU{i}", i)
        self.assertEqual(len(t), 10_000)
        self.assertLessEqual(t.load_factor, HashTable.MAX_LOAD)
        self.assertTrue(all(t[f"SKU{i}"] == i for i in range(10_000)))

    def test_churn_matches_dict(self):
        rng = random.Random(1)
        t, ref = HashTable(), {}
        for _ in range(20_000):
            k = rng.randrange(500)
            if rng.random() < 0.4 and k in ref:
                self.assertEqual(t.remove(k), ref.pop(k))
            else:
                t.put(k, k * 2)
                ref[k] = k * 2
        self.assertEqual(dict(t.items()), ref)
        self.assertLessEqual(t.load_factor, HashTable.MAX_LOAD)

    def test_none_key_rejected(self):
        with self.assertRaises(TypeError):
            HashTable().put(None, 1)


class TestSkipList(unittest.TestCase):
    def test_sorted_iteration_and_remove(self):
        s = SkipList(seed=7)
        keys = random.Random(7).sample(range(10_000), 2_000)
        for k in keys:
            s.insert(k, str(k))
        self.assertEqual([k for k, _ in s], sorted(keys))
        for k in keys[:1_000]:
            self.assertEqual(s.remove(k), str(k))
        self.assertEqual([k for k, _ in s], sorted(keys[1_000:]))
        self.assertEqual(len(s), 1_000)
        with self.assertRaises(KeyError):
            s.remove(keys[0])

    def test_iter_from(self):
        s = SkipList(seed=1)
        for k in (10, 20, 30, 40):
            s.insert(k)
        self.assertEqual([k for k, _ in s.iter_from(25)], [30, 40])
        self.assertEqual([k for k, _ in s.iter_from(20)], [20, 30, 40])
        self.assertEqual(list(s.iter_from(99)), [])

    def test_insert_existing_replaces_value(self):
        s = SkipList()
        s.insert("a", 1)
        s.insert("a", 2)
        self.assertEqual(len(s), 1)
        self.assertEqual(s.get("a"), 2)


class TestIndexedMinHeap(unittest.TestCase):
    def assert_heap_order(self, h):
        for i in range(1, len(h._heap)):
            self.assertLessEqual(h._heap[(i - 1) // 2], h._heap[i])
        for i, (_, item) in enumerate(h._heap):
            self.assertEqual(h._pos[item], i)

    def test_push_pop_order(self):
        h = IndexedMinHeap()
        for item, p in (("a", 5), ("b", 1), ("c", 3)):
            h.push(item, p)
        self.assertEqual([h.pop()[0] for _ in range(3)], ["b", "c", "a"])

    def test_random_updates_and_removes(self):
        rng = random.Random(3)
        h, ref = IndexedMinHeap(), {}
        for i in range(500):
            h.push(i, rng.randint(-50, 50))
            ref[i] = h.priority_of(i)
        for _ in range(2_000):
            item = rng.choice(list(ref))
            if rng.random() < 0.2:
                h.remove(item)
                del ref[item]
                h.push(item, 0)
                ref[item] = 0
            else:
                ref[item] = rng.randint(-50, 50)
                h.update(item, ref[item])
        self.assert_heap_order(h)
        self.assertEqual(h.peek()[1], min(ref.values()))

    def test_items_at_or_below(self):
        h = IndexedMinHeap()
        for i, p in enumerate([5, -2, 0, 7, -9, 3, 0]):
            h.push(i, p)
        self.assertEqual(sorted(i for i, _ in h.items_at_or_below(0)), [1, 2, 4, 6])

    def test_duplicate_push_rejected(self):
        h = IndexedMinHeap()
        h.push("x", 1)
        with self.assertRaises(KeyError):
            h.push("x", 2)


if __name__ == "__main__":
    unittest.main()
