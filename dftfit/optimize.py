"""
DFTFIT a package for developing Molecular Dynamics Packages

"""
# stdlib imports
import os
from subprocess import Popen, PIPE
from time import time
from itertools import combinations
from math import sqrt
from copy import deepcopy

# third-party imports
import numpy as np
from scipy.optimize import minimize

# library specific imports
from .io import (
    read_lammps_forces_dump,
    read_lammps_logfile,
    write_lammps_data_file,
    filetypes
)
from shutil import which


class Dftfit:
    """Class responsible for dft optimization

    Configuration variables must be set for optimization with LAMMPS
    to run.

    Default Units
      Force: eV/Angstrom
      Stress: GPa
      Energy: eV
    """

    # Config Definitions
    # lammps_command - command for running lammps execuatable
    # lammps_prefix - arguments for prepending lammps command
    # lammps_postfix - arguments for appending to lammps command
    # lammps_logfile - filename of lammps logfile
    # lammps_datafile - filename for package to write lammps atoms position data file
    # lammps_forces_dumpfile - filename of force dump from lammps
    # lammps_inputfile - filename to of lammps input file
    # lammps_template_files - files that are templated if the format
    #                         dictionary of 'filename': template_string
    #                         each string is formated with str.format() with
    #                         supplied parameters
    # lammps_unit_conversions - to allow for packages to have custom units
    #                     force conversion factor  = (eV/Angstrom)/unit
    #                     stress conversion factor = (GPa)/unit
    #                     energy conversion factor = (eV)/unit
    # lammps_total_energy_scaled - some versions of LAMMPS scale the total energy
    #                              by number of atoms [True/False]
    # weights - how dftfit assigns weights (must add to 1.0). Default only uses forces
    default_config = {
        'lammps_command': 'lmp_ubuntu',
        'lammps_prefix': '',
        'lammps_postfix': '',
        'lammps_logfile': 'log.lammps',
        'lammps_datafile': '',
        'lammps_forces_dumpfile': '',
        'lammps_inputfile': '',
        'lammps_template_files': {},
        'lammps_unit_conversions': {
            'force': 1.0,
            'stress': 1.0,
            'energy': 1.0
        },
        'lammps_total_energy_scaled': False,
        'weights': {
            'forces': 1.0,
            'stresses': 0.0,
            'total-energy': 0.0
        },
        'dftfit_logfile': 'dftfit.log',
        'DEBUG': False
    }

    def __init__(self, config={}):
        self.config = deepcopy(Dftfit.default_config)
        self.config.update(config)

        self.initial_parameters = []
        self.bounds = []
        self.system_configs = []
        self.atom_types = {}
        self.logger = create_logger(
            debug=self.config['DEBUG'],
            log_filename=self.config['dftfit_logfile'])

        self.iteration = {
            'previous_value': None,
            'previous_parameters': None,
            'step': 0,
        }

    def add_system_config(self, filename, filetype):
        """Adds VASP or Quantum Espresso output file
        to system configurations.

        Currently supports:
         - VASP OUTCAR
         - VASP vasprum.xml
         - QE stdout

        It is required that each run output the forces on each atom.
        """
        if filetype not in filetypes.keys():
            raise Exception("Filetype not accepted")

        system_config = filetypes[filetype](filename)
        system_config.update({'filename': filename})

        self.system_configs.append(system_config)

    def _validate_run(self):
        """Validates that dftfit run is setup to run correctly

        """
        self.logger.info("validating configuration for run")

        # Check that there are system configurations
        if len(self.system_configs) == 0:
            error_str = 'Error: [config] must add system configurations "add_system_config"'
            raise Exception(error_str)

        # run validation
        # Check that a lammps input file exists
        if (self.config['lammps_inputfile'] not in self.config['lammps_template_files'].keys() and
            not os.path.isfile(self.config['lammps_inputfile'])):
            error_str = (
                '[config] lammps input file not found and not in template files "{0}"'
            ).format(self.config['lammps_inputfile'])
            self.logger.error(error_str)
            raise Exception(error_str)

        # Check that the number of initial parameters matches bounds
        if len(self.initial_parameters) != len(self.bounds):
            error_str = 'number of parameters must match bounds'
            self.logger.error(error_str)
            raise Exception(error_str)

        # Check that parameters are within the bounds
        for i, (parameter, (lower_bound, upper_bound)) in enumerate(zip(
                self.initial_parameters, self.bounds)):
            if not lower_bound < parameter < upper_bound:
                error_str = (
                    '{} parameter not within bounds.'
                    '{:.3g} < {:.3g} < {:.3g} not satisfied'
                ).format(i, lower_bound, parameter, upper_bound)
                self.logger.error(error_str)
                raise Exception(error_str)

        # Warn user if no template files are setup
        if len(self.config['lammps_template_files']) == 0:
            self.logger.warning("no template files supplied for dftfit")

        # Warn User if weights are zero
        for unit, weight in self.config['weights'].items():
            if weight == 0.0:
                warning_str = (
                    "{} will not be used in optimization since weight is zero"
                ).format(unit)
                self.logger.warning(warning_str)

        # If total-energy is non-zero at least 2 configurations are required
        if self.config['weights']['total-energy'] != 0.0 and \
           len(self.system_configs) < 2:
            error_str = (
                "at least 2 system configurations required if "
                "total-energy weight is non-zero"
            )
            self.logger.error(error_str)
            raise Exception(error_str)

    def _validate_config(self):
        """Validates that dftfit configuration is correct

        """
        self.logger.info("validating configuration from initialization")

        # Check if lammps execuate is in path or absolute path is given
        if which(self.config['lammps_command']) is None:
            error_str = (
                '[config] lammps execuatable not found "{0}"'
            ).format(self.config['lammps_command'])
            self.logger.error(error_str)
            raise Exception(error_str)

        # Check that user has supplied an datafilename
        if self.config['lammps_datafile'] is '':
            error_str = '[config] user must supply a name for lammps datafile'
            self.logger.error(error_str)
            raise Exception(error_str)

        # Check that user has supplied an dumpfile
        if self.config['lammps_forces_dumpfile'] is '':
            error_str = '[config] user must supply a name for lammps dumpfile'
            self.logger.error(error_str)
            raise Exception(error_str)

        # Check that unit conversions are non-zero
        for unit, conversion in self.config['lammps_unit_conversions'].items():
            if conversion == 0.0:
                error_str = (
                    "unit {} conversion factor must be non-zero"
                ).format(unit)
                self.logger.error(error_str)
                raise Exception(error_str)

    def _run_lammps(self):
        """Runs LAMMPS executable on given input file.

        Notice that this executable is *not* run in the shell. Thus
        environment varaibles will not be available. See
        Popen(shell=False) doc. The LAMMPS '-i' flag is not used
        becuase older versions of LAMMPS do not support this argument.

        """
        with open(self.config['lammps_inputfile']) as f:
            lammps_input = f.read()

        # TODO split works as long as there are no spaces in each
        # argument
        lammps_command = self.config['lammps_command'].split()
        lammps_prefix = self.config.get('lammps_prefix', "").split()
        lammps_postfix = self.config.get('lammps_postfix', "").split()

        proc = Popen(lammps_prefix + lammps_command + lammps_postfix,
                     stdin=PIPE, stdout=PIPE, stderr=PIPE)

        lammps_output = proc.communicate(lammps_input.encode())
        proc.wait()

        stdout = lammps_output[0].decode()
        stderr = lammps_output[1].decode()

        if proc.returncode != 0:
            error_str = (
                "Lammps run exited {} check lammps logfile:\n{}"
            ).format(proc.returncode, stderr)
            self.logger.error(error_str)
            raise Exception(error_str)

    def _calculate_lammps(self, structure, atom_types, parameters):
        """Glue function to write input filesm, run lammps, and collect the
        forces, stress, and total_energy from a given static
        calculation.

        Collects (if resepective weight is non-zero):
         - Forces
         - Stresses
         - Total Energy

        The LAMMPS data file has all of the atomic coordinates along
        with lattice dimmensions. DFTFIT considers all other files
        required by lammps as templates. Templates must currently be
        supplied as strings.

        """
        # Write the atomic positions file
        write_lammps_data_file(structure, atom_types, self.config['lammps_datafile'])

        # Write Lammps Template Files (fill with parameters)
        for filename, template in self.config['lammps_template_files'].items():
            with open(filename, "w") as f:
                f.write(template.format(*parameters))

        self._run_lammps()

        # TODO should we really read the last value
        thermo = read_lammps_logfile(self.config['lammps_logfile'])['thermo']
        stresses = np.array(
            [[thermo['Pxx'][-1], thermo['Pxy'][-1], thermo['Pxz'][-1]],
             [thermo['Pxy'][-1], thermo['Pyy'][-1], thermo['Pyz'][-1]],
             [thermo['Pxz'][-1], thermo['Pyz'][-1], thermo['Pzz'][-1]]])

        total_energy = thermo['TotEng'][-1]
        if self.config['lammps_total_energy_scaled']:
            total_energy *= structure.get_number_of_atoms()

        forces = read_lammps_forces_dump(self.config['lammps_forces_dumpfile'])

        return {
            'forces': forces * self.config['lammps_unit_conversions']['force'],
            'stresses': stresses * self.config['lammps_unit_conversions']['stress'],
            'total-energy': total_energy * self.config['lammps_unit_conversions']['energy'],
        }

    def __str__(self):
        config_str = (
            "\nLammps Configuration:\n"
            "  command   : {0}\n"
            "  inputfile : {1}\n"
            "  logfile   : {2}\n"
            "  datafile  : {3}\n"
            "  force dump: {4}\n"
        ).format(
            self.config['lammps_prefix'] + ' ' + self.config['lammps_command'] + ' ' + self.config['lammps_postfix'],
            self.config['lammps_inputfile'],
            self.config['lammps_logfile'],
            self.config['lammps_datafile'],
            self.config['lammps_forces_dumpfile'])

        template_str = "Templated Files\n"
        for filename, template in self.config['lammps_template_files'].items():
            template_str += "  {0}\n".format(filename)

        parameters_str = "Parameters:\n"
        for i, (parameter, bound) in enumerate(zip(self.initial_parameters, self.bounds), start=1):
            parameters_str += (
                "Parameter {0:>2}: initial value: {1}\n"
                "              bounds: {2:.4g} <-> {3:.4g}\n"
            ).format(i, parameter, *bound)

        system_configs_str = (
            "Number of system configurations: {0}\n"
            "filename\tchemical formula\tnumber of atoms\n"
        ).format(len(self.system_configs))
        for system_config in self.system_configs:
            system_configs_str += "{0}\t{1}\t{2}\n".format(
                system_config.get('filename'),
                system_config['system'].get_chemical_formula(),
                len(system_config['system']))

        return "\n".join([config_str,
                          template_str,
                          parameters_str,
                          system_configs_str])

    def __repr__(self):
        return "<DFTFIT: {0} system configs {1} parameters>".format(
            len(self.system_configs), len(self.initial_parameters))

    def optimize(self, package='scipy'):
        """
        High level routine to optimize dft structure
        """
        self._validate_run()
        self.logger.info(self)

        # Calculate Least Square Error according to
        # http://dx.doi.org/10.1063/1.1513312
        # forces / stresses / total-energy
        def optimize_function(p, grad=None):
            # n_ -> numerator term
            # d_ -> denomenator term
            n_force_sq_error = 0.0
            d_force_sq_error = 0.0
            n_stress_sq_error = 0.0
            d_stress_sq_error = 0.0
            n_energy_sq_error = 0.0
            d_energy_sq_error = 0.0

            # Run MD for each system configuration
            for system_config in self.system_configs:
                if self.config.get('DEBUG'):
                    start_time = time()

                system_config.update({
                    'md': self._calculate_lammps(
                        system_config['system'], self.atom_types, p)
                })

                if self.config.get('DEBUG'):
                    self.logger.debug("LAMMPS Calculation time: {0}".format(time() - start_time))

                md_forces = system_config['md']['forces']
                dft_forces = system_config['dft']['forces']
                n_force_sq_error += np.sum((md_forces - dft_forces)**2.0)
                d_force_sq_error += np.sum(dft_forces**2.0)

                self.logger.debug((
                    "\nDFT force:\n {}\n"
                    "MD force:\n {}\n"
                ).format(dft_forces, md_forces))

                md_stresses = system_config['md']['stresses']
                dft_stresses = system_config['dft']['stresses']
                n_stress_sq_error += np.sum((md_stresses - dft_stresses)**2.0)
                d_stress_sq_error += np.sum(dft_stresses**2.0)

                self.logger.debug((
                    "\nDFT stresses:\n {}\n"
                    "MD stresses:\n {}\n"
                ).format(dft_stresses, md_stresses))

            for system_config_i, system_config_j in combinations(self.system_configs, 2):
                md_energy_i = system_config_i['md']['total-energy']
                md_energy_j = system_config_j['md']['total-energy']

                dft_energy_i = system_config_i['dft']['total-energy']
                dft_energy_j = system_config_j['dft']['total-energy']

                n_energy_sq_error += ((md_energy_i - md_energy_j) - (dft_energy_i - dft_energy_j))**2.0
                d_energy_sq_error += (dft_energy_i - dft_energy_j)**2.0

            w_force = self.config['weights']['forces']
            w_stress = self.config['weights']['stresses']
            w_energy = self.config['weights']['total-energy']

            force_sq_error = sqrt(n_force_sq_error / d_force_sq_error)
            stress_sq_error = sqrt(n_stress_sq_error / d_stress_sq_error)

            # TODO hack to allow one system config if energy weight is zero
            if len(self.system_configs) == 1 and \
               self.config['weights']['total-energy'] == 0.0:
                energy_sq_error = 0.0
            else:
                energy_sq_error = sqrt(n_energy_sq_error / d_energy_sq_error)

            sq_error = (w_force * force_sq_error +
                        w_stress * stress_sq_error +
                        w_energy * energy_sq_error)

            self.logger.debug((
                "\nForce  SQ Error : {} Weight: {}\n"
                "Stress SQ Error : {} Weight: {}\n"
                "Energy SQ Error : {} Weight: {}\n"
                "Total  SQ Error : {}"
            ).format(force_sq_error, w_force,
                     stress_sq_error, w_stress,
                     energy_sq_error, w_energy,
                     sq_error))

            self.logger.info((
                'Step: {:3d} Value: {:>20.16} Parameters: {}'
            ).format(self.iteration['step'], sq_error, p))

            self.iteration['previous_parameters'] = p.copy()
            self.iteration['previous_value'] = sq_error
            self.iteration['step'] += 1

            return sq_error

        # Choose a python non-linear optimization solver (scipy)
        # See http://docs.scipy.org/doc/scipy/reference/optimize.html
        # For detailed informaion
        # def optimize_message(p):
        #     print("Current Iteration Parameters: {0}".format(p))
        #
        if package == 'scipy':
            minimize(
                fun=optimize_function,
                x0=self.initial_parameters,
                method="L-BFGS-B",
                #method="powell",
                #method="COBYLA",
                #method="TNC",
                #method="SLSQP",
                jac=False,
                bounds=self.bounds,
                options={'disp': True},
            )
        elif package == 'nlopt':
            # NLOPT optimization solver
            # used because reference exists that shows algorithm works
            # Using BOBYQA algorithm
            # http://ab-initio.mit.edu/wiki/index.php/NLopt_Algorithms#BOBYQA
            opt = nlopt.opt(nlopt.LN_BOBYQA, len(self.initial_parameters))
            lower_bounds, upper_bounds = zip(*self.bounds)

            self.logger.info((
                "Using {} optimization algorithm with {} parameters\n"
                "{}\n"
            ).format(opt.get_algorithm(), opt.get_dimension(), opt.get_algorithm_name()))

            opt.set_lower_bounds(lower_bounds)
            opt.set_upper_bounds(upper_bounds)

            self.logger.info((
                "\nBounded Problem:\n"
                "Lower Bound: {}\n"
                "Upper Bound: {}\n"
            ).format(opt.get_lower_bounds(), opt.get_upper_bounds()))

            opt.set_min_objective(optimize_function)
            opt.set_ftol_rel(1e-6)
            # opt.set_maxeval(0) # 0 or negative for no limit
            # opt.set_maxtime(0) # seconds (0 or negative for no limit)
            optimized_parameters = opt.optimize(list(self.initial_parameters))
            min_objective_value = opt.last_optimum_value()

            self.logger.info((
                "\nOptimized Parameters: {}\n"
                "Minimum Value: {}\n"
            ).format(optimized_parameters, min_objective_value))
        else:
            raise ValueError('Optimzation Packages %s not recognized' % package)
