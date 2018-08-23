from pathlib import Path
from xml.etree import ElementTree
import glob

import numpy as np
import pymatgen as pmg

from .base import DFTReader


class SiestaReader(DFTReader):
    def __init__(self, xml_structure, xml_lattice, xml_energy, xml_stress, xml_forces):
        self._structure = self._parse_structure(xml_structure, xml_lattice)
        self._energy = self._parse_energy(xml_energy)
        self._stress = self._parse_stress(xml_stress)
        self._forces = self._parse_forces(xml_forces)

    @classmethod
    def from_file(cls, directory, output_filename='output.xml', step=-1):
        directory = Path(directory)
        if not directory.is_dir():
            raise ValueError('path %s must exist and be directory' % directory)
        filename = directory / output_filename
        xml_structures, xml_lattices, xml_energies, xml_stresses, xml_forces = cls.xml_parts_from_root(filename)
        return cls(xml_structures[step], xml_lattices[step], xml_energies[step], xml_stresses[step], xml_forces[step])

    @classmethod
    def from_selector(cls, selector):
        data = []
        if 'filename' in selector:
            filename = selector['filename']
            data.extend(cls._from_selector_with_filename(filename, selector))
        elif 'fileglob' in selector:
            for filename in glob.glob(selector['fileglob'], recursive=True):
                data.extend(cls._from_selector_with_filename(filename, selector))
        else:
            raise ValueError('no way for selector to select data need filename or fileglob')
        return data

    @classmethod
    def _from_selector_with_filename(cls, filename, selector):
        filename = Path(filename)
        if not filename.is_file():
            raise ValueError('path %s must exist and be file' % filename)

        xml_structures, xml_lattices, xml_energies, xml_stresses, xml_forces = xml_parts = cls.xml_parts_from_root(filename)
        results = []
        if ('num_samples' in selector) and selector.get('strategy', 'max-separation') == 'max-separation':
            indicies = np.linspace(0, len(xml_structures)-1, selector['num_samples']).astype('int')
            for i in indicies:
                results.append(cls(xml_structures[i], xml_lattices[i], xml_energies[i], xml_stresses[i], xml_forces[i]))
        elif ('num_samples' not in selector) and selector['strategy'] == 'all':
            for xml_parts in zip(xml_structures, xml_lattices, xml_energies, xml_stresses, xml_forces):
                results.append(cls(*xml_parts))
        else:
            raise ValueError('not able to handle selector type yet')
        return results

    @staticmethod
    def xml_parts_from_root(filename):
        namespaces = {'xml': 'http://www.xml-cml.org/schema'}
        root = ElementTree.parse(filename).getroot()

        # throw away last structure (no calculation for last step)
        XML_ATOMARRAY = './/xml:module[@dictRef="MD"]/xml:molecule[1]/xml:atomArray'
        xml_structures = root.findall(XML_ATOMARRAY, namespaces=namespaces)[:-1]

        XML_LATTICE = './/xml:crystal[@title="Lattice Parameters"]'
        xml_lattices = root.findall(XML_LATTICE, namespaces=namespaces)[:-1]

        XML_ENERGIES = './/xml:propertyList[@title="Final KS Energy"]/xml:property[@dictRef="siesta:E_KS"]/xml:scalar'
        xml_energies = root.findall(XML_ENERGIES, namespaces=namespaces)

        XML_STRESS = './/xml:property[@title="Total Stress"]/xml:matrix'
        xml_stresses = root.findall(XML_STRESS, namespaces=namespaces)

        XML_FORCES = './/xml:propertyList[@title="Forces"]/xml:property/xml:matrix'
        xml_forces = root.findall(XML_FORCES, namespaces=namespaces)

        return (xml_structures, xml_lattices, xml_energies, xml_stresses, xml_forces)

    def _parse_structure(self, xml_structure, xml_lattice):
        coordinates = []
        symbols = []
        for atom in xml_structure:
            symbols.append(atom.attrib["elementType"])
            coordinates.append([atom.attrib["x3"], atom.attrib["y3"], atom.attrib["z3"]])
        coordinates = np.array(coordinates).reshape(-1, 3).astype(float)

        namespaces = {'xml': 'http://www.xml-cml.org/schema'}
        XML_LATTICE_LENGTHS = './xml:cellParameter[@parameterType="length"]'
        XML_LATTICE_ANGLES = './xml:cellParameter[@parameterType="angle"]'
        lattice_lengths = [float(_) for _ in xml_lattice.find(XML_LATTICE_LENGTHS, namespaces=namespaces).text.split()]
        lattice_angles = [float(_) for _ in xml_lattice.find(XML_LATTICE_ANGLES, namespaces=namespaces).text.split()]

        lattice = pmg.Lattice.from_parameters(*lattice_lengths, *lattice_angles)
        return pmg.Structure(lattice, symbols, coordinates, coords_are_cartesian=True)

    def _parse_energy(self, xml_energy):
        return float(xml_energy.text)

    def _parse_stress(self, xml_stress):
        eVA32GPa = 160.21766208 # http://greif.geo.berkeley.edu/~driver/conversions.html
        GPa2Bar = 1e4 # GPa -> Bar
        return np.array([float(_) for _ in xml_stress.text.split()]).reshape(3, 3) * eVA32GPa * GPa2Bar

    def _parse_forces(self, xml_forces):
        return np.array([float(_) for _ in xml_forces.text.split()]).reshape(-1, 3)

    @property
    def forces(self):
        return self._forces

    @property
    def stress(self):
        return self._stress

    @property
    def energy(self):
        return self._energy

    @property
    def structure(self):
        return self._structure
