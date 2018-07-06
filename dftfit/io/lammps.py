from pathlib import Path
from collections import OrderedDict
import asyncio

import numpy as np
from pymatgen.core import Element
from pmg_lammps.output import LammpsRun, LammpsData
from pmg_lammps.inputs import LammpsInput, LammpsScript
from pmg_lammps.calculator.client import LammpsLocalClient

from .base import MDReader, MDCalculator, DFTFITCalculator
from .utils import element_type_to_symbol


class LammpsReader(MDReader):
    def __init__(self, directory, data_filename='initial.data', log_filename='lammps.log', dump_filename='mol.lammpstrj'):
        self.directory = Path(directory)
        self.data_filename = data_filename
        self.log_filename = log_filename
        self.dump_filename = dump_filename
        self._parse()

    def _parse(self):
        dump_path = list(self.directory.glob('**/%s' % self.dump_filename))
        if len(dump_path) > 1:
            raise ValueError('multiple %s files found within directory' % self.dump_filename)
        elif len(dump_path) == 0:
            raise ValueError('could not find %s file within directory' % self.dump_filename)

        log_path = list(self.directory.glob('**/%s' % self.log_filename))
        if len(log_path) > 1:
            raise ValueError('multiple %s files found within directory' % self.log_filename)
        elif len(log_path) == 0:
            raise ValueError('could not find %s file within directory' % self.log_filename)

        data_path = list(self.directory.glob('**/%s' % self.data_filename))
        if len(data_path) > 1:
            raise ValueError('multiple %s files found within directory' % self.data_filename)
        elif len(data_path) == 0:
            raise ValueError('could not find %s file within directory' % self.data_filename)

        data = LammpsData.from_file(str(data_path[0]))
        output = LammpsRun(str(data_path[0]), lammps_log=str(log_path[0]), lammps_dump=str(dump_path[0]))
        # TODO: check units
        self._forces = output.get_forces(-1)
        self._stress = output.get_stress(-1)
        self._energy = output.get_energy(-1)
        self._structure = output.get_structure(-1)


lammps_dftfit_set = OrderedDict([
    ('echo', 'both'),
    ('log', 'lammps.log'),
    ('units', 'metal'),
    ('dimension', 3),
    ('boundary', 'p p p'),
    ('atom_style', 'full'),
    ('read_data', 'initial.data'),
    ('kspace_style', []),
    ('pair_style', []),
    ('pair_coeff', []),
    ('set', []),
    ('dump', '1 all custom 1 mol.lammpstrj id type x y z fx fy fz'),
    ('dump_modify', '1 sort id'),
    ('thermo_modify', 'flush yes'),
    ('thermo_style', 'custom step etotal pxx pyy pzz pxy pxz pyz'),
    ('run', 0),
])


def modify_input_for_potential(lammps_input, potential):
    symbol_indicies = {element_type_to_symbol(s): i for s, i in lammps_input.lammps_data.symbol_indicies.items()}

    # Ensure that even if element missing from structure
    # element is included in lammps script and lammps data
    max_indicie = max(symbol_indicies.values())
    for element in potential.elements:
        if element not in symbol_indicies:
            max_indicie += 1
            elem = Element(element)
            lammps_input.lammps_data.symbol_indicies[elem] = max_indicie
            lammps_input.lammps_data.masses[elem] = elem.atomic_mass
            symbol_indicies[element] = max_indicie

    def charge(potential):
        spec = potential.schema['spec']
        set_commands = []
        element_index_charge = sorted([(symbol_indicies[element], float(charge)) for element, charge in spec.get('charge', {}).items()], key=lambda e: e[0])
        for element_index, charge in element_index_charge:
            set_commands.append('type %d charge %f' % (element_index, charge))
        return ('set', set_commands)

    def kspace_style(potential):
        spec = potential.schema['spec']
        if 'kspace' in spec:
            style = spec['kspace']['type']
            tollerance = spec['kspace']['tollerance']
            return ('kspace_style', '%s %f' % (style, float(tollerance)))
        return ('kspace_style', [])

    def tersoff_file(potential):
        spec = potential.schema['spec']
        if 'pair' in spec and spec['pair']['type'] == 'tersoff':
            lines = []
            for parameter in spec['pair']['parameters']:
                lines.append(' '.join(parameter['elements'] + [float(c) for c in parameter['coefficients']]))
            return ('\n'.join(lines), 'potential.tersoff')
        return []

    def pair_style(potential):
        pair_map = {
            'buckingham': ('buck', '{style} {cutoff}'),
            'tersoff': ('tersoff', '{style}')
        }

        spec = potential.schema['spec']
        if 'pair' in spec:
            style, pair_style_format = pair_map[spec['pair']['type']]
            cutoff = spec['pair'].get('cutoff', 10) # angstroms
            if 'kspace'in spec and spec['kspace']['type'] in {'ewald', 'pppm'}:
                style += '/coul/long'
            return ('pair_style', pair_style_format.format(**{'style': style, 'cutoff': float(cutoff)}))
        return ('pair_style', [])

    def pair_coeff(potential):
        spec = potential.schema['spec']
        if 'pair' in spec:
            if spec['pair']['type'] in ['buckingham']:
                symbols_to_indicies = lambda symbols: [symbol_indicies[s] for s in symbols]
                pair_coeffs = []
                for coeff in spec['pair']['parameters']:
                    # lammps requires that indicies be accending
                    pair_coeffs.append(' '.join(list(map(str, sorted(symbols_to_indicies(coeff['elements'])) + coeff['coefficients']))))
                return ('pair_coeff', pair_coeffs)
            elif spec['pair']['type'] == 'tersoff':
                return '* * potential.tersoff Si C Si'; # TODO: find out how to determine
        return ('pair_coeff', [])

    lammps_input.lammps_script.update([
        charge(potential),
        kspace_style(potential),
        pair_style(potential),
        pair_coeff(potential)
    ])
    lammps_input.additional_files.extend(tersoff_file(potential))


class LammpsLocalDFTFITCalculator(DFTFITCalculator):
    def __init__(self, structures, command='lammps_ubuntu', num_workers=1):
        self.num_cores = 1
        self.command = command
        self.lammps_local_client = LammpsLocalClient(command=command, num_workers=num_workers)
        self.structures = structures

    async def create(self):
        await self.lammps_local_client.create()

    @staticmethod
    def _convert_to_reader(structure, lammps_result):
            return MDReader(
                forces=np.array(lammps_result['results']['forces']),
                stress=np.array(lammps_result['results']['stress']),
                energy=lammps_result['results']['energy'],
                structure=structure
            )

    async def submit(self, potential, properties=None):
        lammps_set = lammps_dftfit_set
        properties = properties or {'stress', 'energy', 'forces'}

        futures = []
        for structure in self.structures:
            lammps_input = LammpsInput(
                LammpsScript(lammps_set),
                LammpsData.from_structure(structure))
            modify_input_for_potential(lammps_input, potential)
            data_filename = lammps_input.lammps_script.data_filenames[0]
            stdin = str(lammps_input.lammps_script)
            files = {data_filename: str(lammps_input.lammps_data)}
            futures.append(await self.lammps_local_client.submit(
                stdin, files, properties))
        results = await asyncio.gather(*futures)
        return [self._convert_to_reader(s, r) for s, r in zip(self.structures, results)]

    def shutdown(self):
        self.lammps_local_client.shutdown()



class LammpsLocalMDCalculator(MDCalculator):
    def __init__(self, command='lammps_ubuntu', num_workers=1):
        self.num_cores = 1
        self.command = command
        self.lammps_local_client = LammpsLocalClient(command=command, num_workers=num_workers)

    async def create(self):
        await self.lammps_local_client.create()

    async def submit(self, structure, potential, properties=None, lammps_set=None):
        lammps_set = lammps_set or lammps_dftfit_set
        properties = properties or {'stress', 'energy', 'forces'}
        lammps_input = LammpsInput(
            LammpsScript(lammps_set),
            LammpsData.from_structure(structure))
        modify_input_for_potential(lammps_input, potential)
        data_filename = lammps_input.lammps_script.data_filenames[0]
        stdin = str(lammps_input.lammps_script)
        files = {data_filename: str(lammps_input.lammps_data)}
        return await self.lammps_local_client.submit(stdin, files, properties)

    def shutdown(self):
        self.lammps_local_client.shutdown()
