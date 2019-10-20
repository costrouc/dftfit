"""Defines objective functions used in DFTFIT

"""
import numpy
import numba


def force_objective_function(md_calculations, dft_calculations):
    md_calculations = numpy.array([_.forces for _ in md_calculations])
    dft_calculations = numpy.array([_.forces for _ in dft_calculations])

    return _force_objective_function(md_calculations, dft_calculations)


def _force_objective_function(md_calculations, dft_calculations):
    n_force_sq_error = 0.0
    d_force_sq_error = 0.0
    for i in range(len(md_calculations)):
        n_force_sq_error += numpy.sum((md_calculations[i] - dft_calculations[i])**2.0)
        d_force_sq_error += numpy.sum(dft_calculations[i]**2.0)
    return numpy.sqrt(n_force_sq_error / d_force_sq_error)


def stress_objective_function(md_calculations, dft_calculations):
    md_calculations = numpy.array([_.stress for _ in md_calculations])
    dft_calculations = numpy.array([_.stress for _ in dft_calculations])

    return _stress_objective_function(md_calculations, dft_calculations)


@numba.njit
def _stress_objective_function(md_calculations, dft_calculations):
    n_stress_sq_error = 0.0
    d_stress_sq_error = 0.0
    for i in range(len(md_calculations)):
        n_stress_sq_error += numpy.sum((md_calculations[i] - dft_calculations[i])**2.0)
        d_stress_sq_error += numpy.sum(dft_calculations[i]**2.0)
    return numpy.sqrt(n_stress_sq_error / d_stress_sq_error)


def energy_objective_function(md_calculations, dft_calculations):
    # cannot calculate energy error if only one set of calculations
    if len(md_calculations) == 1:
        return 0.0

    md_calculations = numpy.array([_.energy for _ in md_calculations])
    dft_calculations = numpy.array([_.energy for _ in dft_calculations])

    return _energy_objective_function(md_calculations, dft_calculations)


@numba.njit
def _energy_objective_function(md_calculations, dft_calculations):
    n_energy_sq_error: float = 0.0
    d_energy_sq_error: float = 0.0

    for i in range(len(md_calculations)):
        for j in range(i, len(dft_calculations)):
            md_calc_i, dft_calc_i = md_calculations[i], dft_calculations[i]
            md_calc_j, dft_calc_j = md_calculations[j], dft_calculations[j]
            n_energy_sq_error += ((md_calc_i - md_calc_j) - (dft_calc_i - dft_calc_j))**2.0
            d_energy_sq_error += (dft_calc_i - dft_calc_j)**2.0
    return numpy.sqrt(n_energy_sq_error / d_energy_sq_error)


# material properties
def lattice_constant_objective_function(lattice, measured_lattice_constants):
    # not going to include angles in calculation (different units need to reconcile)
    lengths, angles = lattice.lengths_and_angles

    n_lc_sq_error = 0.0
    d_lc_sq_error = 0.0

    for m_lengths, m_angles in measured_lattice_constants:
        n_lc_sq_error += numpy.sum((lengths - m_lengths)**2.0)
        d_lc_sq_error += numpy.sum(m_lengths**2.0)
    return numpy.sqrt(n_lc_sq_error / d_lc_sq_error)


def elastic_constants_objective_function(elastic_constants, measured_elastic_constants):
    elastic_constants_voigt = elastic_constants.voigt

    n_ec_sq_error = 0.0
    d_ec_sq_error = 0.0

    for m_elastic_constants in measured_elastic_constants:
        n_ec_sq_error = numpy.sum((elastic_constants_voigt - m_elastic_constants)**2.0)
        d_ec_sq_error = numpy.sum(m_elastic_constants**2.0)
    return numpy.sqrt(n_ec_sq_error / d_ec_sq_error)


def bulk_modulus_objective_function(elastic_constants, measured_bulk_modulus):
    bulk_modulus = elastic_constants.k_vrh # Voigt-Reuss-Hill average bulk modulus

    n_bm_sq_error = 0.0
    d_bm_sq_error = 0.0

    for m_bulk_modulus in measured_bulk_modulus:
        n_bm_sq_error += (m_bulk_modulus - bulk_modulus)**2.0
        d_bm_sq_error += m_bulk_modulus**2.0
    return numpy.sqrt(n_bm_sq_error / d_bm_sq_error)


def shear_modulus_objective_function(elastic_constants, measured_shear_modulus):
    shear_modulus = elastic_constants.g_vrh # Voigt-Reuss-Hill average shear modulus

    n_sm_sq_error = 0.0
    d_sm_sq_error = 0.0

    for m_shear_modulus in measured_shear_modulus:
        n_sm_sq_error += (m_shear_modulus - shear_modulus)**2.0
        d_sm_sq_error += m_shear_modulus**2.0
    return numpy.sqrt(n_sm_sq_error / d_sm_sq_error)
