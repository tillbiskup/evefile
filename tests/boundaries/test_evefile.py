import os
import unittest

import h5py
import numpy as np

from evefile.boundaries import evefile


class DummyHDF5File:
    def __init__(self, filename=""):
        self.filename = filename

    def create(self):
        with h5py.File(self.filename, "w") as file:
            file.attrs["EVEH5Version"] = np.bytes_(["7"])
            file.attrs["Version"] = np.bytes_(["2.0"])
            file.attrs["XMLversion"] = np.bytes_(["9.2"])
            file.attrs["Comment"] = np.bytes_([""])
            file.attrs["Location"] = np.bytes_(["Unittest"])
            file.attrs["StartTimeISO"] = np.bytes_(["2024-06-03T12:01:32"])
            file.attrs["EndTimeISO"] = np.bytes_(["2024-06-03T12:01:37"])
            file.attrs["Simulation"] = np.bytes_(["no"])
            c1 = file.create_group("c1")
            main = c1.create_group("main")
            meta = c1.create_group("meta")
            simmot = main.create_dataset(
                "SimMot:01",
                data=np.ones(
                    [5],
                    dtype=np.dtype(
                        [("PosCounter", "<i4"), ("SimMot:01", "<f8")]
                    ),
                ),
            )
            simmot["PosCounter"] = np.linspace(1, 5, 5)
            simmot["SimMot:01"] = np.random.random(5)
            simmot.attrs["Name"] = np.bytes_(["foo"])
            simmot.attrs["Access"] = np.bytes_(["ca:foobar"])
            simmot.attrs["DeviceType"] = np.bytes_(["Axis"])
            simchan = main.create_dataset(
                "SimChan:01",
                data=np.ones(
                    [5],
                    dtype=np.dtype(
                        [("PosCounter", "<i4"), ("SimChan:01", "<f8")]
                    ),
                ),
            )
            simchan["PosCounter"] = np.linspace(1, 5, 5)
            simchan["SimChan:01"] = np.random.random(5)
            simchan.attrs["Name"] = np.bytes_(["bar"])
            simchan.attrs["Access"] = np.bytes_(["ca:barbaz"])
            simchan.attrs["DeviceType"] = np.bytes_(["Channel"])
            simchan.attrs["Detectortype"] = np.bytes_(["Standard"])
            data = np.ndarray(
                [10],
                dtype=np.dtype(
                    [("PosCounter", "<i4"), ("PosCountTimer", "<i4")]
                ),
            )
            poscounttimer = meta.create_dataset("PosCountTimer", data=data)
            poscounttimer.attrs["Unit"] = np.bytes_(["msecs"])


class TestEveFile(unittest.TestCase):
    def setUp(self):
        self.filename = "file.h5"
        self.evefile = evefile.EveFile(filename=self.filename)

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_instantiate_class(self):
        pass

    def test_has_attributes(self):
        attributes = [
            "metadata",
            "log_messages",
            "data",
            "snapshots",
            "monitors",
            "position_timestamps",
            "filename",
        ]
        for attribute in attributes:
            with self.subTest(attribute=attribute):
                self.assertTrue(hasattr(self.evefile, attribute))

    def test_setting_filename_sets_metadata_filename(self):
        filename = "foobar.h5"
        self.evefile.filename = filename
        self.assertEqual(self.evefile.metadata.filename, filename)

    def test_init_with_filename_sets_metadata_filename(self):
        filename = "foobar.h5"
        file = evefile.EveFile(filename=filename)
        self.assertEqual(filename, file.metadata.filename)

    def test_load_sets_file_metadata(self):
        h5file = DummyHDF5File(filename=self.filename)
        h5file.create()
        self.evefile.load()
        root_mappings = {
            "eveh5_version": "7",
            "measurement_station": "Unittest",
        }
        for key, value in root_mappings.items():
            with self.subTest(key=key, val=value):
                self.assertEqual(getattr(self.evefile.metadata, key), value)

    def test_get_data_returns_data_by_name(self):
        h5file = DummyHDF5File(filename=self.filename)
        h5file.create()
        self.evefile.load()
        self.assertEqual(
            self.evefile.data["SimMot:01"],
            self.evefile.get_data("foo"),
        )

    def test_get_data_list_returns_data_by_name_as_array(self):
        h5file = DummyHDF5File(filename=self.filename)
        h5file.create()
        self.evefile.load()
        self.assertEqual(
            self.evefile.data["SimMot:01"],
            self.evefile.get_data(["foo", "bar"])[0],
        )

    def test_data_have_correct_shape(self):
        h5file = DummyHDF5File(filename=self.filename)
        h5file.create()
        self.evefile.load()
        self.assertEqual(5, len(self.evefile.data["SimChan:01"].data))
        self.assertEqual(5, len(self.evefile.data["SimMot:01"].data))

    def test_get_data_names(self):
        h5file = DummyHDF5File(filename=self.filename)
        h5file.create()
        self.evefile.load()
        self.assertEqual(
            [item.metadata.name for item in self.evefile.data.values()],
            self.evefile.get_data_names(),
        )
