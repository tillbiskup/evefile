import unittest

import numpy as np
from numpy import ma

from evefile.controllers import joining


class MockMetadata:
    def __init__(self):
        name = ""


class MockDevice:
    def __init__(
        self, data=np.random.random(5), positions=np.arange(2, 7), name=""
    ):
        self.data = data
        self.position_counts = positions
        self.metadata = MockMetadata()
        self.metadata.name = name

    def get_data(self):
        pass


class MockEveFile:
    def __init__(self, snapshots=False):
        self.data = {
            "SimChan:01": MockDevice(),
            "SimMot:01": MockDevice(),
        }
        if snapshots:
            self.snapshots = {
                "SimChan:01": MockDevice(
                    data=np.random.random(2), positions=np.asarray([1, 7])
                ),
                "SimMot:01": MockDevice(
                    data=np.random.random(2), positions=np.asarray([1, 7])
                ),
            }
        else:
            self.snapshots = {}

    def get_data(self, name=""):
        names = {item.metadata.name: key for key, item in self.data.items()}
        return self.data[names[name]]


class TestJoin(unittest.TestCase):
    def setUp(self):
        self.join = joining.Join()
        self.evefile = MockEveFile()

    def test_instantiate_class(self):
        pass

    def test_has_attributes(self):
        attributes = [
            "evefile",
        ]
        for attribute in attributes:
            with self.subTest(attribute=attribute):
                self.assertTrue(hasattr(self.join, attribute))

    def test_initialise_with_evefile_sets_evefile(self):
        evefile = self.evefile
        join = joining.Join(evefile=evefile)
        self.assertEqual(evefile, join.evefile)

    def test_join_without_evefile_raises(self):
        self.join.evefile = None
        with self.assertRaisesRegex(
            ValueError, "Need an evefile to join data."
        ):
            self.join.join()

    def test_join_without_data_raises(self):
        self.join.evefile = self.evefile
        with self.assertRaisesRegex(ValueError, "Need data to join data."):
            self.join.join()

    def test_join_returns_list(self):
        self.join.evefile = self.evefile
        self.join.evefile.data = {
            "bar": MockDevice(),
            "baz": MockDevice(),
        }
        result = self.join.join(data=["bar", "baz"])
        self.assertIsInstance(result, list)

    def test_join_with_ids_converts_to_datasets(self):
        class MyJoin(joining.Join):
            def _join(self, data=None):
                return data

        self.join = MyJoin()
        self.join.evefile = MockEveFile()
        self.join.evefile.data = {
            "SimChan:01": MockDevice(
                data=np.random.random(5), positions=np.linspace(0, 4, 5)
            ),
            "SimMot:01": MockDevice(
                data=np.random.random(7), positions=np.linspace(0, 6, 7)
            ),
        }
        result = self.join.join(data=["SimChan:01", "SimMot:01"])
        for item in result:
            self.assertIsInstance(item, MockDevice)

    def test_join_with_names_converts_to_datasets(self):
        class MyJoin(joining.Join):
            def _join(self, data=None):
                return data

        self.join = MyJoin()
        self.join.evefile = MockEveFile()
        self.join.evefile.data = {
            "SimChan:01": MockDevice(
                data=np.random.random(5),
                positions=np.linspace(0, 4, 5),
                name="bar",
            ),
            "SimMot:01": MockDevice(
                data=np.random.random(7),
                positions=np.linspace(0, 6, 7),
                name="baz",
            ),
        }
        result = self.join.join(data=["bar", "baz"])
        for item in result:
            self.assertIsInstance(item, MockDevice)


class TestAxesLastFill(unittest.TestCase):
    def setUp(self):
        self.join = joining.AxesLastFill()
        self.join.evefile = MockEveFile()

    def test_instantiate_class(self):
        pass

    def test_join_returns_list(self):
        result = self.join.join(data=["SimChan:01", "SimMot:01"])
        self.assertIsInstance(result, list)

    def test_join_returns_only_values_for_data_positions(self):
        self.join.evefile.data = {
            "SimChan:01": MockDevice(
                data=np.random.random(5), positions=np.linspace(0, 4, 5)
            ),
            "SimMot:01": MockDevice(
                data=np.random.random(7), positions=np.linspace(0, 6, 7)
            ),
        }
        result = self.join.join(data=["SimChan:01", "SimMot:01"])
        self.assertEqual(len(result[0]), len(result[1]))

    def test_join_returns_only_values_for_data_positions_with_gaps(self):
        self.join.evefile.data = {
            "SimChan:01": MockDevice(
                data=np.random.random(4), positions=np.asarray([0, 2, 3, 4])
            ),
            "SimMot:01": MockDevice(
                data=np.random.random(7), positions=np.linspace(0, 6, 7)
            ),
        }
        result = self.join.join(data=["SimChan:01", "SimMot:01"])
        self.assertEqual(len(result[0]), len(result[1]))

    def test_join_fills_axes_values(self):
        self.join.evefile.data = {
            "SimChan:01": MockDevice(
                data=np.random.random(5), positions=np.linspace(0, 4, 5)
            ),
            "SimMot:01": MockDevice(
                data=np.random.random(4), positions=np.linspace(0, 3, 4)
            ),
        }
        result = self.join.join(data=["SimChan:01", "SimMot:01"])
        self.assertEqual(len(result[0]), len(result[1]))
        np.testing.assert_array_equal(
            self.join.evefile.data["SimMot:01"].data,
            result[1][:-1],
        )
        self.assertEqual(result[1][-2], result[1][-1])

    def test_join_masks_axes_values_with_gap_at_beginning(self):
        self.join.evefile.data = {
            "SimChan:01": MockDevice(
                data=np.random.random(5), positions=np.linspace(0, 4, 5)
            ),
            "SimMot:01": MockDevice(
                data=np.random.random(3), positions=np.linspace(2, 4, 3)
            ),
        }
        result = self.join.join(data=["SimChan:01", "SimMot:01"])
        self.assertEqual(len(result[0]), len(result[1]))
        np.testing.assert_array_equal(
            self.join.evefile.data["SimMot:01"].data,
            result[1][2:],
        )
        self.assertIsInstance(result[1], ma.masked_array)
        self.assertTrue(result[1].mask[0])

    def test_join_fills_axes_values_with_gaps(self):
        self.join.evefile.data = {
            "SimChan:01": MockDevice(
                data=np.random.random(5), positions=np.linspace(0, 4, 5)
            ),
            "SimMot:01": MockDevice(
                data=np.random.random(4), positions=np.asarray([0, 2, 4])
            ),
        }
        result = self.join.join(data=["SimChan:01", "SimMot:01"])
        self.assertEqual(len(result[0]), len(result[1]))
        self.assertEqual(result[1][0], result[1][1])
        self.assertEqual(result[1][2], result[1][3])

    def test_join_fills_axes_values_with_snapshots(self):
        self.join.evefile.data = {
            "SimChan:01": MockDevice(
                data=np.random.random(5), positions=np.arange(2, 7)
            ),
            "SimMot:01": MockDevice(
                data=np.random.random(4), positions=np.asarray([3, 4, 5, 6])
            ),
        }
        self.join.evefile.snapshots = {
            "SimChan:01": MockDevice(
                data=np.random.random(2), positions=np.asarray([1, 7])
            ),
            "SimMot:01": MockDevice(
                data=np.random.random(2), positions=np.asarray([1, 7])
            ),
        }
        result = self.join.join(data=["SimChan:01", "SimMot:01"])
        self.assertEqual(len(result[0]), len(result[1]))
        self.assertEqual(
            self.join.evefile.snapshots["SimMot:01"].data[0],
            result[1][0],
        )


class TestJoinFactory(unittest.TestCase):
    def setUp(self):
        self.factory = joining.JoinFactory()

    def test_instantiate_class(self):
        pass

    def test_get_join_returns_join(self):
        self.assertIsInstance(self.factory.get_join(), joining.Join)

    def test_get_join_with_type_returns_correct_join(self):
        self.assertIsInstance(
            self.factory.get_join(mode="AxesLastFill"),
            joining.Join,
        )

    def test_initialise_with_evefile_sets_evefile(self):
        evefile = "foo"
        factory = joining.JoinFactory(evefile=evefile)
        self.assertEqual(evefile, factory.evefile)

    def test_get_join_with_evefile_sets_evefile(self):
        self.factory.evefile = "foo"
        join = self.factory.get_join()
        self.assertEqual(self.factory.evefile, join.evefile)
