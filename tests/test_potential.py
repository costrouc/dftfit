import os

import pytest

from dftfit.potential import Potential


def test_potential_from_schema():
    schema = {
        'version': 'v1',
        'kind': 'Potential',
        'spec': {
            'charge': {
                'Mg': 2.0,
                'O': -2.0
            },
            'kspace': {
                'type': 'pppm',
                'tollerance': 10.0
            },
            'pair': [{
                'type': 'buckingham',
                'cutoff': [10.0],
                'parameters': [{
                    'elements': ['O', 'Mg'],
                    'coefficients': [1.0, 0.0, 3.0]
                }]
            }],
        }
    }
    potential = Potential(schema)
    # Ordering does matter (in some cases)
    assert potential.schema['spec']['pair'][0]['parameters'][0]['elements'] == ['O', 'Mg']


@pytest.mark.parametrize('filename, num_opt_params, num_params', [
    ('Ne-lennard-jones.yaml', 0, 3),
    ('He-beck.yaml', 0, 6),
    ('MgO-charge-buck.yaml', 0, 13),
    ('MgO-charge-buck-fitting.yaml', 8, 13),
    ('MgO-charge-func.yaml', 0, 14),
    ('LiTaO3-tersoff-2.yaml', 0, 36),
    ('LiTaO3-tersoff-2-charge.yaml', 0, 40),
    ('LiNbO3-charge-buck-harmonic.yaml', 0, 25),
    ('SiC-tersoff.yaml', 0, 112),
    ('SiC-gao-weber.yaml', 0, 112),
    ('SiCGe-tersoff-2.yaml', 0, 44),
    ('SiCGe-tersoff.yaml', 0, 210),
    ('CdTe-stillinger-weber.yaml', 0, 88)
])
def test_potential_from_file(filename, num_opt_params, num_params):
    filename = os.path.join('test_files/potential', filename)
    p = Potential.from_file(filename)
    assert len(p.optimization_parameters) == num_opt_params
    assert len(p.parameters) == num_params
