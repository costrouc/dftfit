import itertools
import collections

import numpy as np
from sklearn import manifold
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pymatgen as pmg

from .db_actions import filter_evaluations, list_evaluations


def normalize_parameters(optimization_bounds, parameters_array):
    optimization_bounds = np.array(optimization_bounds)
    min_norm_vector = optimization_bounds[:, 0]
    range_norm_vector = optimization_bounds[:, 1] - optimization_bounds[:, 0]
    return (parameters_array - min_norm_vector) / range_norm_vector


def tsne_evaluations(dbm, ax, potential, run_id, limit=1000, condition='best', labels=None):
    cursor = filter_evaluations(dbm, potential, limit, condition, run_id, labels)
    parameters_array = []
    scores = []
    for row in cursor:
        parameters_array.append(row['parameters'])
        scores.append(row['score'])
    parameters_array = np.array(parameters_array)
    scores = np.array(scores)

    with dbm.connection:
        optimization_bounds = dbm.connection.execute(
            'SELECT bounds FROM run WHERE id = ?', (run_id,)).fetchone()['bounds']

    normalized_parameters = normalize_parameters(optimization_bounds, parameters_array)

    tsne = manifold.TSNE(n_components=2, init='pca', random_state=0)
    Y = tsne.fit_transform(normalized_parameters)
    return ax.scatter(Y[:, 0], Y[:, 1], c=scores, cmap=plt.cm.Spectral, alpha=0.2)


def visualize_progress(dbm, run_id, window=100, title=None, filename=None, show=True):
    df = list_evaluations(dbm, run_id)
    title = title or f'Optimization progress for run {run_id}'

    linewidth = 0.5
    fig, axes = plt.subplots(1, 3, sharey=True, sharex=True)
    axes[0].plot(df['score'].rolling(window=window, center=False).mean(), linewidth=linewidth)
    axes[0].set_title('mean')
    axes[0].set_ylabel('normalized score')
    axes[0].set_xlabel('iterations')
    axes[0].ticklabel_format(axis='x', style='sci', scilimits=(-2, 2))
    axes[1].plot(df['score'].rolling(window=window, center=False).median(), linewidth=linewidth)
    axes[1].set_title('median')
    axes[1].set_xlabel('iterations')
    axes[2].plot(df['score'].rolling(window=window, center=False).min(), linewidth=linewidth)
    axes[2].set_title('minimum')
    axes[2].set_xlabel('iterations')
    fig.set_size_inches((15, 5))

    if filename:
        fig.savefig(filename, transparent=True)
    if show:
        plt.show()


def visualize_single_calculation(dft_calculations, md_calculations, plot='forces', show=True, filename=None):
    dft_forces = []
    md_forces = []
    dft_c = []
    md_c = []
    c_ij = [(0, 0), (1, 1), (2, 2), (0, 1), (0, 2), (1, 2)]
    for dft_calc, md_calc in zip(dft_calculations, md_calculations):
        dft_forces.extend(np.linalg.norm(dft_calc.forces, axis=1).tolist())
        md_forces.extend(np.linalg.norm(md_calc.forces, axis=1).tolist())
        dft_c.append([dft_calc.stress[ij] for ij in c_ij])
        md_c.append([md_calc.stress[ij] for ij in c_ij])

    dft_rel_energies = []
    md_rel_energies = []
    for (dft_calc_i, md_calc_i), (dft_calc_j, md_calc_j) in itertools.combinations(zip(dft_calculations, md_calculations), 2):
        dft_rel_energies.append(dft_calc_i.energy - dft_calc_j.energy)
        md_rel_energies.append(md_calc_i.energy - md_calc_j.energy)

    point_alpha = 0.1
    point_size = 3
    def plot_equal_line(axes, x, y):
        axes.plot([np.min(x), np.max(x)], [np.min(x), np.max(x)], '--', color='#E65933', alpha=0.5)

    if plot == 'forces':
        fig, axes = plt.subplots(1, 1)
        axes.scatter(dft_forces, md_forces, alpha=point_alpha, s=point_size)
        axes.set_xlabel(r'DFT force magnitude [$eV/\AA$]')
        axes.set_ylabel(r'MD force magnitude [$eV/\AA$]')
        plot_equal_line(axes, dft_forces, md_forces)
    elif plot == 'energy':
        fig, axes = plt.subplots(1, 1)
        axes.scatter(dft_rel_energies, md_rel_energies, alpha=point_alpha, s=point_size)
        axes.set_xlabel(r'DFT relative energies [$eV$]')
        axes.set_ylabel(r'MD relative energies [$eV$]')
        plot_equal_line(axes, dft_rel_energies, md_rel_energies)
    elif plot == 'stress':
        fig, axes = plt.subplots(2, 3)
        axes[0,0].scatter(dft_c[0], md_c[0])
        axes[0,0].set_xlabel(r'DFT $\sigma_{xx} [bar]$')
        axes[0,0].set_ylabel(r'MD $\sigma_{xx} [bar]$')
        plot_equal_line(axes[0,0], dft_c[0], md_c[0])

        axes[0,1].scatter(dft_c[1], md_c[1])
        axes[0,1].set_xlabel(r'DFT $\sigma_{yy} [bar]$')
        axes[0,1].set_ylabel(r'MD $\sigma_{yy} [bar]$')
        plot_equal_line(axes[0,1], dft_c[1], md_c[1])

        axes[0,2].scatter(dft_c[2], md_c[2])
        axes[0,2].set_xlabel(r'DFT $\sigma_{zz} [bar]$')
        axes[0,2].set_ylabel(r'MD $\sigma_{zz} [bar]$')
        plot_equal_line(axes[0,2], dft_c[2], md_c[2])

        axes[1,0].scatter(dft_c[3], md_c[3])
        axes[1,0].set_xlabel(r'DFT $\sigma_{xy} [bar]$')
        axes[1,0].set_ylabel(r'MD $\sigma_{xy} [bar]$')
        plot_equal_line(axes[1,0], dft_c[3], md_c[3])

        axes[1,1].scatter(dft_c[4], md_c[4])
        axes[1,1].set_xlabel(r'DFT $\sigma_{xz} [bar]$')
        axes[1,1].set_ylabel(r'MD $\sigma_{xz} [bar]$')
        plot_equal_line(axes[1,1], dft_c[4], md_c[4])

        axes[1,2].scatter(dft_c[5], md_c[5])
        axes[1,2].set_xlabel(r'DFT $\sigma_{yz} [bar]$')
        axes[1,2].set_ylabel(r'MD $\sigma_{yz} [bar]$')
        plot_equal_line(axes[1,2], dft_c[5], md_c[5])
        fig.set_size_inches((12, 15))
        plt.tight_layout()

    if filename:
        fig.savefig(filename, transparen=True)
    if show:
        plt.show()
    return fig, axes


def visualize_radial_pair_distribution(calculations, distance=10, filename=None, show=True):
    """visualize the radial pair distributions for each atom in training set"""
    specie_types = set()
    for calculation in calculations:
        specie_types.update(calculation.structure.types_of_specie)

    distances = collections.defaultdict(list)

    for calculation in calculations:
        for original_site, sites in zip(calculation.structure, calculation.structure.get_all_neighbors(10, include_index=True)):
            for (site, distance, index) in sites:
                distances[tuple(sorted([original_site.specie, site.specie]))].append(distance)

    fig, axes = plt.subplots(len(distances), 1, sharex=True, sharey=True)
    for pair, ax in zip(distances, axes.ravel()):
        ax.set_xlabel('distance [angstroms]')
        ax.set_ylabel('count')
        ax.set_title(f'{pair[0].symbol} - {pair[1].symbol}')
        ax.hist(distances[pair], bins=int(distance*10))
    fig.set_size_inches((10, len(distances)*4))
    if filename:
        fig.savefig(filename, transparent=True)
    if show:
        plt.show()
    return fig, axes


def visualize_pair_energies(separations, pair_energies, filename=None, show=True):
    fig, axes = plt.subplots(len(pair_energies), 1, sharex=True, sharey=True)
    for ax, (label, energies) in zip(np.ravel(axes), pair_energies.items()):
        ax.plot(separations, energies)
        ax.axhline(y=0, c='k', linewidth=1, linestyle='dotted')
        ax.set_ylabel('Energy [eV]')
        ax.set_yscale('symlog')
        while len(ax.get_yticks()) > 5: # would be nice if i could just specify 5...
            ax.set_yticks(ax.get_yticks()[::2])
        ax.set_title(label)
    axes[-1].set_xlabel(r'Separation [$\AA$]')
    plt.show()
