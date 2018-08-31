def print_elastic_information(elastic):
    print('Stiffness Tensor')
    for row in elastic.voigt:
        print('{:+8.1f} {:+8.1f} {:+8.1f} {:+8.1f} {:+8.1f} {:+8.1f}\n'.format(*row))
    print('\n')
    print('Shear Modulus G_V', elastic.g_voigt)
    print('Shear Modulus G_R', elastic.g_reuss)
    print('Shear Modulus G_vrh', elastic.g_vrh)

    print('Bulk Modulus K_V', elastic.k_voigt)
    print('Bulk Modulus K_R', elastic.k_reuss)
    print('Bulk Modulus K_vrh', elastic.k_vrh)

    print('Elastic Anisotropy', elastic.universal_anisotropy)
    print('Poisons Ration', elastic.homogeneous_poisson)


def apply_structure_operations(structure, operations, tollerance=0.1):
    for operation in operations:
        cart_coords = operation['position']
        element = operation['element']
        if operation['opp'] == '+':
            structure.append(element, cart_coords)
        elif operation['opp'] == '-':
            sites = structure.get_sites_in_sphere(cart_coords, tollerance)
            if len(sites) != 1:
                raise ValueError('found %d sites at %s with radius %f needed only one' % (len(sites), cart_coords, tollerance))
            site = sites[0][0]
            structure.remove_sites([structure.index(site)])
