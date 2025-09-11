import unittest

import numpy as np

from evefile.controllers import timestamp_mapping
import evefile.entities.data


class MockMonitor(evefile.entities.data.MonitorData):
    def __init__(
        self,
        data=np.random.random(5),
        milliseconds=np.asarray([-1, -1, 2000, 6200, 9100]),
        name="",
    ):
        super().__init__()
        self.data = data
        self.milliseconds = milliseconds
        self.metadata.name = name


class MockEveFile:
    def __init__(self, snapshots=False):
        self.monitors = {
            "SimMonitor:01.STAT": MockMonitor(name="Status"),
        }
        self.position_timestamps = evefile.entities.data.TimestampData()
        self.position_timestamps.position_counts = np.arange(1, 11)
        self.position_timestamps.data = np.arange(0, 10) * 1002


class TestMapper(unittest.TestCase):
    def setUp(self):
        self.mapper = timestamp_mapping.Mapper()
        self.evefile = MockEveFile()
        self.monitor_name = list(self.evefile.monitors.keys())[0]

    def test_instantiate_class(self):
        pass

    def test_has_attributes(self):
        attributes = [
            "evefile",
        ]
        for attribute in attributes:
            with self.subTest(attribute=attribute):
                self.assertTrue(hasattr(self.mapper, attribute))

    def test_initialise_with_evefile_sets_evefile(self):
        evefile = self.evefile
        mapper = timestamp_mapping.Mapper(evefile=evefile)
        self.assertEqual(evefile, mapper.evefile)

    def test_map_without_evefile_raises(self):
        self.mapper.evefile = None
        with self.assertRaisesRegex(
            ValueError, "Need an evefile to map data."
        ):
            self.mapper.map()

    def test_map_without_data_raises(self):
        self.mapper.evefile = self.evefile
        with self.assertRaisesRegex(
            ValueError, "Need monitor to map " "timestamps to positions."
        ):
            self.mapper.map()

    def test_map_returns_device_data(self):
        self.mapper.evefile = self.evefile
        mapped_data = self.mapper.map(self.monitor_name)
        self.assertIsInstance(mapped_data, evefile.entities.data.DeviceData)

    def test_returned_device_data_contain_correct_metadata(self):
        self.mapper.evefile = self.evefile
        mapped_data = self.mapper.map(self.monitor_name)
        self.assertEqual(
            self.mapper.evefile.monitors[self.monitor_name].metadata.name,
            mapped_data.metadata.name,
        )

    def test_returned_device_data_contain_positions(self):
        self.mapper.evefile = self.evefile
        mapped_data = self.mapper.map(self.monitor_name)
        self.assertTrue(all(mapped_data.position_counts > 0))
        self.assertTrue(all(mapped_data.position_counts < 11))

    def test_returned_device_data_contain_data(self):
        self.mapper.evefile = self.evefile
        mapped_data = self.mapper.map(self.monitor_name)
        np.testing.assert_array_equal(
            mapped_data.data,
            self.mapper.evefile.monitors[self.monitor_name].data[1:],
        )

    def test_returned_device_data_contain_copy_of_data(self):
        self.mapper.evefile = self.evefile
        mapped_data = self.mapper.map(self.monitor_name)
        self.assertIsNot(
            mapped_data.data,
            self.mapper.evefile.monitors[self.monitor_name].data,
        )

    def test_returned_device_data_contain_last_of_duplicate_times(self):
        self.mapper.evefile = self.evefile
        mapped_data = self.mapper.map(self.monitor_name)
        self.assertEqual(
            self.mapper.evefile.monitors[self.monitor_name].data[1],
            mapped_data.data[0],
        )
