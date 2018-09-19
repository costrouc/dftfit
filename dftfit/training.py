""" Handles collection of trial and testing data.

Has a caching layer as to speed up future runs
"""
import json
import shelve
import os
import hashlib
import collections

import yaml
import pymatgen as pmg
from pymatgen.io.cif import CifParser
from pymatgen.io.vasp import Poscar

from .schema import TrainingSchema
from .io.mattoolkit import MTKReader
from .io.siesta import SiestaReader
from . import utils


class Training:
    def __init__(self, schema, cache_filename=None):
        schema_load, errors = TrainingSchema().load(schema)
        self.schema = schema_load
        self._gather_calculations(cache_filename=cache_filename)
        self._gather_material_properties()

    def _gather_calculations(self, cache_filename=None):
        self._calculations = []
        for calculation in self.schema['spec']:
            if calculation['type'] == 'mattoolkit':
                self._calculations.extend(self.download_mattoolkit_calculations(calculation['selector'], cache_filename=cache_filename))
            elif calculation['type'] == 'Siesta':
                self._calculations.extend(SiestaReader.from_selector(calculation['selector']))

    def _gather_material_properties(self):
        self._material_properties_reference_ground_state = None
        self._material_properties = collections.defaultdict(list)
        for material_property in self.schema['spec']:
            if material_property['type'] == 'ground_state':
                if self._material_properties_reference_ground_state:
                    raise ValueError('current cannot have more than one reference ground state')
                self._material_properties_reference_ground_state = self._parse_structure(material_property)
            elif material_property['type'] == 'lattice_constants':
                self._material_properties['lattice_constants'].append(material_property['data'])
            elif material_property['type'] == 'elastic_constants':
                self._material_properties['elastic_constants'].append(material_property['data'])
            elif material_property['type'] == 'bulk_modulus':
                self._material_properties['bulk_modulus'].append(material_property['data'])
            elif material_property['type'] == 'shear_modulus':
                self._material_properties['shear_modulus'].append(material_property['data'])

        if self._material_properties and self._material_properties_reference_ground_state is None:
            raise ValueError('calculating material properties requires a reference ground state structure')

    def _parse_structure(self, structure_schema):
        data = structure_schema['data']
        format = structure_schema['format']
        if format == 'cif':
            # cif lattice can be weird non standard shape
            structure = (CifParser.from_string(data)).get_structures()[0]
            lattice = pmg.Lattice.from_parameters(*structure.lattice.abc, *structure.lattice.angles)
            structure = pmg.Structure(lattice, structure.species, structure.frac_coords, coords_are_cartesian=False)
        elif format == 'POSCAR':
            structure = (Poscar.from_string(data)).structure
        return structure

    @property
    def calculations(self):
        return self._calculations

    @property
    def material_properties(self):
        return self._material_properties

    @property
    def reference_ground_state(self):
        return self._material_properties_reference_ground_state

    def __iter__(self):
        return iter(self._calculations)

    def __len__(self):
        return len(self._calculations)

    def download_mattoolkit_calculations(self, selector, cache_filename=None):
        if cache_filename:
            cache_directory, filename = os.path.split(cache_filename)
            os.makedirs(cache_directory, exist_ok=True)
            key = f'mattoolkit.calculation.' + '.'.join(selector['labels'])
            with shelve.open(cache_filename) as cache:
                if key in cache:
                    calc_ids = cache[key]
                else:
                    from mattoolkit.api import CalculationResourceList

                    calculations = CalculationResourceList()
                    calculations.get(params={'labels': selector['labels']})
                    calc_ids = [c.id for c in calculations.items]
                    cache[key] = calc_ids
        else:
            from mattoolkit.api import CalculationResourceList

            calculations = CalculationResourceList()
            calculations.get(params={'labels': selector['labels']})
            calc_ids = [c.id for c in calculations.items]
        return [MTKReader(calc_id, cache_filename=cache_filename) for calc_id in calc_ids]

    @classmethod
    def from_file(cls, filename, format=None, **kwargs):
        if format not in {'json', 'yaml'}:
            if filename.endswith('json'):
                format = 'json'
            elif filename.endswith('yaml') or filename.endswith('yml'):
                format = 'yaml'
            else:
                raise ValueError('unrecognized filetype from filename %s' % filename)

        if format == 'json':
            with open(filename) as f:
                return cls(json.load(f))
        elif format in {'yaml', 'yml'}:
            with open(filename) as f:
                return cls(yaml.load(f), **kwargs)

    def __str__(self):
        return json.dumps(self.schema, sort_keys=True, cls=utils.NumpyEncoder)

    @property
    def md5hash(self):
        return hashlib.md5(str(self).encode('utf-8')).hexdigest()
