from dftfit.potential import Potential

def test_potential_lammps():
    schema = {
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
                'atoms': ['Mg', 'O'],
                'parameters': [1.0, 0.0, 3.0]
            }]
        }
    }
    potential = Potential(schema)
    print(potential)
    assert False
