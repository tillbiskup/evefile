import logging
import unittest

import numpy as np

import evefile.boundaries.evefile
from evefile.controllers import version_mapping
import evefile.entities.data


class MockHDF5Item:
    def __init__(self, name="", filename=""):
        self.filename = filename
        self.name = name
        self.attributes = {}


class MockHDF5Dataset(MockHDF5Item):
    def __init__(self, name="", filename=""):
        super().__init__(name=name, filename=filename)
        self.data = None
        self.get_data_called = False
        self.dtype = np.dtype(
            [("PosCounter", "<i4"), (name.split("/")[-1], "<f8")]
        )

    @property
    def shape(self):
        if self.data is not None:
            shape = self.data.shape
        else:
            shape = (0,)
        return shape

    def get_data(self):
        self.get_data_called = True


class MockHDF5Group(MockHDF5Item):
    def __init__(self, name="", filename=""):
        super().__init__(name=name, filename=filename)
        self._items = {}

    def __iter__(self):
        for item in self._items.values():
            yield item

    def add_item(self, item):
        name = item.name.split("/")[-1]
        setattr(self, name, item)
        self._items[name] = item

    def remove_item(self, item):
        name = item.name.split("/")[-1]
        delattr(self, name)
        self._items.pop(name)

    def item_names(self):
        return list(self._items.keys())


class MockEveH5(MockHDF5Group):

    # noinspection PyUnresolvedReferences
    def __init__(self):
        super().__init__()
        self.filename = "test.h5"
        self.name = "/"
        self.attributes = {
            "EVEH5Version": "7",
            "Location": "TEST",
            "Version": "2.0",
            "XMLversion": "9.2",
            "Comment": "",
            "Simulation": "no",
            "SCML-Author": "biskup02@a23bashful",
            "SCML-Name": "test.scml",
            "StartDate": "03.06.2024",
            "StartTime": "12:01:32",
            "StartTimeISO": "2024-06-03T12:01:32",
            "EndTimeISO": "2024-06-03T12:01:37",
        }
        self.add_item(MockHDF5Group(name="/c1", filename=self.filename))
        self.c1.attributes = {
            "EndTimeISO": "2024-06-03T12:01:37",
            "StartDate": "03.06.2024",
            "StartTime": "12:01:32",
            "StartTimeISO": "2024-06-03T12:01:32",
            "preferredAxis": "OMS58:io1501003",
            "preferredChannel": "A2980:22704chan1",
            "preferredNormalizationChannel": "A2980:22704chan1",
        }
        self.c1.add_item(
            MockHDF5Group(name="/c1/meta", filename=self.filename)
        )
        poscounttimer = MockHDF5Dataset(
            name="/c1/meta/PosCountTimer", filename=self.filename
        )
        poscounttimer.dtype = np.dtype(
            [("PosCounter", "<i4"), ("PosCountTimer", "<i4")]
        )
        poscounttimer.attributes = {"Unit": "msecs"}
        self.c1.meta.add_item(poscounttimer)


class MockFile:
    pass


class TestVersionMapperFactory(unittest.TestCase):

    def setUp(self):
        self.factory = version_mapping.VersionMapperFactory()
        self.eveh5 = MockEveH5()
        self.logger = logging.getLogger(name="evedata")

    def test_instantiate_class(self):
        pass

    def test_has_attributes(self):
        attributes = [
            "eveh5",
        ]
        for attribute in attributes:
            with self.subTest(attribute=attribute):
                self.assertTrue(hasattr(self.factory, attribute))

    def test_get_mapper_returns_mapper(self):
        self.factory.eveh5 = self.eveh5
        mapper = self.factory.get_mapper()
        self.assertIsInstance(mapper, version_mapping.VersionMapper)

    def test_get_mapper_with_eveh5_argument_sets_eveh5_property(self):
        self.factory.get_mapper(eveh5=self.eveh5)
        self.assertEqual(self.factory.eveh5, self.eveh5)

    def test_get_mapper_without_eveh5_raises(self):
        with self.assertRaises(ValueError):
            self.factory.get_mapper()

    def test_get_mapper_returns_correct_mapper(self):
        self.factory.eveh5 = self.eveh5
        mapper = self.factory.get_mapper()
        self.assertIsInstance(mapper, version_mapping.VersionMapperV7)

    def test_get_mapper_with_fractional_version_returns_correct_mapper(self):
        self.eveh5.attributes["EVEH5Version"] = "7.0"
        self.factory.eveh5 = self.eveh5
        mapper = self.factory.get_mapper()
        self.assertIsInstance(mapper, version_mapping.VersionMapperV7)

    def test_get_mapper_with_unknown_version_raises(self):
        self.eveh5.attributes["EVEH5Version"] = "0"
        self.factory.eveh5 = self.eveh5
        with self.assertRaises(AttributeError):
            self.factory.get_mapper()

    def test_get_mapper_with_unknown_version_logs(self):
        self.eveh5.attributes["EVEH5Version"] = "0"
        self.factory.eveh5 = self.eveh5
        self.logger.setLevel(logging.ERROR)
        self.logger.addHandler(logging.NullHandler())
        with self.assertLogs(level=logging.ERROR) as captured:
            with self.assertRaises(AttributeError):
                self.factory.get_mapper()
            self.assertEqual(len(captured.records), 1)
            self.assertEqual(
                captured.records[0].getMessage(),
                "No mapper for version 0",
            )

    def test_get_mapper_sets_source_in_mapper(self):
        self.factory.eveh5 = self.eveh5
        mapper = self.factory.get_mapper()
        self.assertEqual(mapper.source, self.eveh5)


class TestVersionMapper(unittest.TestCase):
    def setUp(self):
        self.mapper = version_mapping.VersionMapper()

    def test_instantiate_class(self):
        pass

    def test_has_attributes(self):
        attributes = [
            "source",
            "destination",
        ]
        for attribute in attributes:
            with self.subTest(attribute=attribute):
                self.assertTrue(hasattr(self.mapper, attribute))

    def test_map_without_source_raises(self):
        self.mapper.source = None
        with self.assertRaises(ValueError):
            self.mapper.map()

    def test_map_without_destination_raises(self):
        self.mapper.source = MockEveH5()
        with self.assertRaises(ValueError):
            self.mapper.map()

    def test_map_with_source_and_destination_parameters(self):
        self.mapper.source = None
        self.mapper.map(source=MockEveH5(), destination=MockFile())

    def test_get_hdf5_dataset_importer_returns_importer(self):
        self.assertIsInstance(
            self.mapper.get_hdf5_dataset_importer(dataset=MockHDF5Dataset()),
            evefile.entities.data.HDF5DataImporter,
        )

    def test_get_hdf5_dataset_importer_sets_source_and_item(self):
        dataset = MockHDF5Dataset(filename="test.h5", name="/c1/main/foobar")
        importer = self.mapper.get_hdf5_dataset_importer(dataset=dataset)
        self.assertEqual(dataset.filename, importer.source)
        self.assertEqual(dataset.name, importer.item)

    def test_get_hdf5_dataset_importer_sets_mapping(self):
        dataset = MockHDF5Dataset(filename="test.h5", name="/c1/main/foobar")
        mapping = {0: "foobar", 1: "barbaz"}
        importer = self.mapper.get_hdf5_dataset_importer(
            dataset=dataset, mapping=mapping
        )
        mapping_dict = {
            dataset.dtype.names[0]: mapping[0],
            dataset.dtype.names[1]: mapping[1],
        }
        self.assertDictEqual(mapping_dict, importer.mapping)


class TestVersionMapperV7(unittest.TestCase):
    def setUp(self):
        self.mapper = version_mapping.VersionMapperV7()
        self.destination = evefile.boundaries.evefile.EveFile()

    def test_instantiate_class(self):
        pass
