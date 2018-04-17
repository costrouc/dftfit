from pathlib import Path
from xml.etree import ElementTree

import numpy as np
import pymatgen as pmg

from .base import DFTReader


class SiestaReader(DFTReader):
    def __init__(self, directory, output_filename='output.xml'):
        self.directory = Path(directory)
        self.output_filename = output_filename
        if not self.directory.is_dir():
            raise ValueError('path %s must exist and be directory' % self.directory)
        self._parse()

    def _parse(self, step=-1):
        # for now just take the last step
        self._namespaces = {'xml': 'http://www.xml-cml.org/schema'}
        root = ElementTree.parse(self.directory / self.output_filename).getroot()
        self._parse_structure(root, step)
        self._parse_energy(root, step)
        self._parse_stresses(root, step)
        self._parse_forces(root, step)

    def _parse_structure(self, root, step=-1):
        XML_ATOMARRAY = './/xml:module[@dictRef="MD"]/xml:molecule[1]/xml:atomArray'
        xml_structures = root.findall(XML_ATOMARRAY, namespaces=self._namespaces)
        coordinates = []
        symbols = []
        for atom in xml_structures[step]:
            symbols.append(atom.attrib["elementType"])
            coordinates.append([atom.attrib["x3"], atom.attrib["y3"], atom.attrib["z3"]])
        coordinates = np.array(coordinates).reshape(-1, 3).astype(float)

        XML_LATTICE = './/xml:crystal[@title="Lattice Parameters"]'
        xml_lattices = root.findall(XML_LATTICE, namespaces=self._namespaces)
        xml_lattice = xml_lattices[step]
        XML_LATTICE_LENGTHS = './xml:cellParameter[@parameterType="length"]'
        XML_LATTICE_ANGLES = './xml:cellParameter[@parameterType="angle"]'
        lattice_lengths = [float(_) for _ in xml_lattice.find(XML_LATTICE_LENGTHS, namespaces=self._namespaces).text.split()]
        lattice_angles = [float(_) for _ in xml_lattice.find(XML_LATTICE_ANGLES, namespaces=self._namespaces).text.split()]

        lattice = pmg.Lattice.from_parameters(*lattice_lengths, *lattice_angles)
        self._structure = pmg.Structure(lattice, symbols, coordinates, coords_are_cartesian=True)

    def _parse_energy(self, root, step=-1):
        XML_ENERGIES = './/xml:propertyList[@title="Final KS Energy"]/xml:property/xml:scalar'
        energies = root.findall(XML_ENERGIES, namespaces=self._namespaces)
        self._energy = float(energies[step].text)

    def _parse_stresses(self, root, step=-1):
        eVA32GPa = 160.21766208 # http://greif.geo.berkeley.edu/~driver/conversions.html
        XML_STRESS = './/xml:property[@title="Total Stress"]/xml:matrix'
        xml_stresses = root.findall(XML_STRESS, namespaces=self._namespaces)
        self._stress = np.array([float(_) for _ in xml_stresses[step].text.split()]).reshape(3, 3) * eVA32GPa

    def _parse_forces(self, root, step=-1):
        XML_FORCES = './/xml:propertyList[@title="Forces"]/xml:property/xml:matrix'
        xml_forces = root.findall(XML_FORCES, namespaces=self._namespaces)
        self._forces = np.array([float(_) for _ in xml_forces[step].text.split()]).reshape(-1, 3)

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
