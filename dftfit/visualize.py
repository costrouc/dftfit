import itertools

import numpy as np
from sklearn import manifold
import matplotlib.pyplot as plt

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
    title = title or f'Progress for run {run_id}'

    fontsize = 20
    fig, axes = plt.subplots(1, 3, sharey=True)
    axes[0].plot(df['score'].rolling(window=window, center=False).mean())
    axes[0].set_title('mean')
    axes[1].plot(df['score'].rolling(window=window, center=False).median())
    axes[1].set_title('median')
    axes[2].plot(df['score'].rolling(window=window, center=False).min())
    axes[2].set_title('minimum')
    fig.set_size_inches((15, 5))
    fig.suptitle(title, fontsize=fontsize)

    if filename:
        fig.savefig(filename, transparent=True)
    if show:
        plt.show()


def visualize_single_calculation(dft_calculations, md_calculations):
    dft_forces = []
    md_forces = []
    dft_c_11 = []
    md_c_11 = []
    dft_c_22 = []
    md_c_22 = []
    dft_c_33 = []
    md_c_33 = []
    for dft_calc, md_calc in zip(dft_calculations, md_calculations):
        dft_forces.extend(np.linalg.norm(dft_calc.forces, axis=1).tolist())
        md_forces.extend(np.linalg.norm(md_calc.forces, axis=1).tolist())
        dft_c_11.append(dft_calc.stress[0,0])
        md_c_11.append(md_calc.stress[0,0])
        dft_c_22.append(dft_calc.stress[1,1])
        md_c_22.append(md_calc.stress[1,1])
        dft_c_33.append(dft_calc.stress[2,2])
        md_c_33.append(md_calc.stress[2,2])

    dft_rel_energies = []
    md_rel_energies = []
    for (dft_calc_i, md_calc_i), (dft_calc_j, md_calc_j) in itertools.combinations(zip(dft_calculations, md_calculations), 2):
        dft_rel_energies.append(dft_calc_i.energy - dft_calc_j.energy)
        md_rel_energies.append(md_calc_i.energy - md_calc_j.energy)


    fig, axes = plt.subplots(3, 3)
    axes[0,0].scatter(dft_forces, md_forces)
    axes[0,1].scatter(dft_rel_energies, md_rel_energies)
    axes[1,0].scatter(dft_c_11, md_c_11, label='c_11')
    axes[1,1].scatter(dft_c_22, md_c_22, label='c_22')
    axes[1,2].scatter(dft_c_33, md_c_33, label='c_33')
    fig.set_size_inches((12, 15))
    plt.show()
