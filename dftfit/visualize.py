from .db_actions import filter_evaluations, list_evaluations

import numpy as np
from sklearn import manifold
import matplotlib.pyplot as plt


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
