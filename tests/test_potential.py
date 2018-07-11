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
            'pair': {
                'type': 'buckingham',
                'cutoff': 10.0,
                'parameters': [{
                    'elements': ['Mg', 'O'],
                    'coefficients': [1.0, 0.0, 3.0]
                }]
            }
        }
    }
    Potential(schema)


@pytest.mark.parametrize('filename, num_opt_params, num_params', [
    ('test_files/potential/mgo.yaml', 0, 13),
    ('test_files/potential/mgo-fitting.yaml', 8, 13),
#    ('test_files/potential/litao3-tersoff.yaml', 0), # not added to schema yet
])
def test_potential_from_file(filename, num_opt_params, num_params):
    p = Potential.from_file(filename)
    assert len(p.optimization_parameters) == num_opt_params
    assert len(p.parameters) == num_params
