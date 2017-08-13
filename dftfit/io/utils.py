from pymatgen.core import Specie, Element


def element_type_to_symbol(specie):
    if isinstance(specie, Specie):
        return specie.element.symbol
    elif isinstance(specie, Element):
        return specie.symbol
    elif isinstance(specie, str):
        return specie
    else:
        raise TypeError('Unsure how to convert to element symbol')
