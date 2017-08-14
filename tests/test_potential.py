from dftfit.potential import Potential

def test_potential_lammps():
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
    potential = Potential(schema)


def test_potential_from_file():
    potential = Potential.from_file('test_files/potential/mgo.yaml')


def test_potential_from_file_read_parameters():
    potential = Potential.from_file('test_files/potential/mgo.yaml')
    print(potential.parameters)
