import unittest

from se_buddy.commands.trace import _reverse_closure


class FakeObj:
    def __init__(self, uuid):
        self.uuid = uuid


class FakeModel:
    """`find_references(obj)` returns whatever the caller wired up for
    `obj.uuid` - a minimal stand-in for capellambse's real method, letting
    `_reverse_closure`'s own BFS/dedup logic be tested without a real
    model.
    """

    def __init__(self, refs_by_target_uuid: dict):
        self._refs = refs_by_target_uuid

    def find_references(self, obj):
        return self._refs.get(obj.uuid, [])


class TestReverseClosure(unittest.TestCase):
    def test_two_distinct_attribute_edges_from_the_same_object_are_both_recorded(self):
        """A code review found the original single `visited` set treated
        "already reached this object" and "already recorded an edge from
        it" as the same thing - so if one object referenced the target
        through two different attributes, only the first edge survived
        and the second was silently dropped.
        """
        target = FakeObj("T")
        a = FakeObj("A")
        model = FakeModel({"T": [(a, "attr_one", 0), (a, "attr_two", 0)]})

        found = _reverse_closure(model, target, depth=2)

        self.assertEqual(len(found), 2)
        attrs = {attr for _obj, attr in found}
        self.assertEqual(attrs, {"attr_one", "attr_two"})

    def test_depth_bounds_how_far_the_closure_expands(self):
        target = FakeObj("T")
        a = FakeObj("A")
        b = FakeObj("B")
        model = FakeModel({"T": [(a, "attr", 0)], "A": [(b, "attr", 0)]})

        depth_one = _reverse_closure(model, target, depth=1)
        self.assertEqual([obj.uuid for obj, _attr in depth_one], ["A"])

        depth_two = _reverse_closure(model, target, depth=2)
        self.assertEqual({obj.uuid for obj, _attr in depth_two}, {"A", "B"})

    def test_duplicate_edge_from_two_paths_is_recorded_once(self):
        target = FakeObj("T")
        a = FakeObj("A")
        b = FakeObj("B")
        # both A and B reach the target directly, and both also happen to
        # be reachable through each other - the same (uuid, attr) edge
        # must not be double-counted just because BFS visits it twice.
        model = FakeModel(
            {
                "T": [(a, "attr", 0), (b, "attr", 0)],
                "A": [(b, "attr", 0)],
                "B": [(a, "attr", 0)],
            }
        )

        found = _reverse_closure(model, target, depth=3)
        self.assertEqual(len(found), len(set(found)))


if __name__ == "__main__":
    unittest.main()
