import pickle

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

IMAGES_DIR = "../doc/images"

# Human-readable labels for the shorthand property keys used in data.pkl,
# used only for plot display - the keys themselves are unchanged.
METRIC_LABELS = {
    "pur": "Node-based",
    "tra": "Edge-based\n(translational)",
    "rot": "Edge-based\n(rotational)",
    "ref": "Edge-based\n(reflective)",
    "str": "Stress",
    "for": "Even neighborhood\ndistribution",
    "viz": "Visual (pixel-based)",
    "n": "Node count",
    "m": "Edge count",
    "m_dens": "Edge density",
    "area": "Area",
    "area_tight": "Tight area",
    "concentration": "Concentration",
    "crossings": "Crossings",
}


def smooth(y, box_pts):
    box = np.ones(box_pts) / box_pts
    y_smooth = np.convolve(y, box, mode='same')
    n = len(y)
    y_smooth[n - 1] = y[n - 1]
    return y_smooth


def _append(list, data, graph, property):
    if property in data[graph]:
        list.append(data[graph][property])
    else:
        list.append(None)


data = {}

with open('data.pkl', 'rb') as pickle_file:
    data = pickle.load(pickle_file)


# Draw correlation matrix
def correlation_matrix(data, properties):
    cor_data = {property: [] for property in properties}

    for graph_key, graph_data in data.items():
        for property in properties:
            cor_data[property].append(graph_data.get(property))

    df = pd.DataFrame(cor_data).rename(columns=METRIC_LABELS)
    sns.pairplot(df, diag_kind='kde', height=1.8)
    plt.savefig(f'{IMAGES_DIR}/sym_scatter.svg', bbox_inches='tight')
    plt.close('all')

    correlation_matrix = df.corr()
    n = len(properties)
    plt.figure(figsize=(max(8, n * 1.4), max(6, n * 1.2)))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, annot_kws={"size": 10})
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(f'{IMAGES_DIR}/sym_corr.svg', bbox_inches='tight')
    plt.close('all')


def correlation_matrix_2(data, row_prop, column_prop):
    cor_data = {property: [] for property in row_prop + column_prop}
    for graph_key, graph_data in data.items():
        for property in row_prop + column_prop:
            cor_data[property].append(graph_data.get(property))

    df = pd.DataFrame(cor_data)

    row_labels = [METRIC_LABELS.get(p, p) for p in row_prop]
    column_labels = [METRIC_LABELS.get(p, p) for p in column_prop]

    # Scatter plot
    fig, axes = plt.subplots(len(row_prop), len(column_prop),
                              figsize=(len(column_prop) * 2.5, len(row_prop) * 2.2))

    for i, g1 in enumerate(row_prop):
        for j, g2 in enumerate(column_prop):
            axes[i, j].scatter(df[g2], df[g1], s=10)

            # Label axes
            if i == len(row_prop) - 1:
                axes[i, j].set_xlabel(column_labels[j])
            if j == 0:
                axes[i, j].set_ylabel(row_labels[i])

    plt.tight_layout()
    plt.savefig(f'{IMAGES_DIR}/sym_scatter_2.svg', bbox_inches='tight')
    plt.close('all')

    # Correlation matrix

    group1 = df[row_prop]
    group2 = df[column_prop]

    correlation_matrix = pd.DataFrame(index=row_labels, columns=column_labels)
    for col1, label1 in zip(row_prop, row_labels):
        for col2, label2 in zip(column_prop, column_labels):
            correlation_matrix.loc[label1, label2] = group1[col1].corr(group2[col2])
    correlation_matrix = correlation_matrix.astype(float)

    plt.figure(figsize=(max(8, len(column_prop) * 1.4), max(6, len(row_prop) * 1.2)))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, annot_kws={"size": 10})
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(f'{IMAGES_DIR}/sym_corr_2.svg', bbox_inches='tight')
    plt.close('all')


correlation_matrix(data, ['pur', 'tra', 'rot', 'ref', 'str', 'for', 'viz'])
correlation_matrix_2(data, ['pur', 'tra', 'rot', 'ref', 'str', 'for', 'viz'],
                      ['n', 'm', 'm_dens', 'area', 'area_tight', 'concentration', 'crossings'])

# Time data

timedata = {}

with open('timedata.pkl', 'rb') as pickle_file:
    timedata = pickle.load(pickle_file)


def _plot(plt, x_values, y_values, label):
    filtered_x = [a for a, b in zip(x_values, y_values) if a is not None and b is not None]
    filtered_y = [b for a, b in zip(x_values, y_values) if a is not None and b is not None]

    try:
        filtered_y = smooth(filtered_y, 3)
        return plt.plot(filtered_x, filtered_y, label=label)
    except ValueError:
        print("Empty dataset")
        return None


def draw_data(data, properties, names, filename, xlim=None, ylim=None):
    property_dic = {property: [] for property in properties}
    property_dic['n'] = []
    property_dic['den'] = []

    for graph in data:
        for key in property_dic:
            _append(property_dic[key], data, graph, key)

    sorted_indices = np.argsort(property_dic['n'])
    for key, property in property_dic.items():
        property_dic[key] = np.array(property)[sorted_indices]

    width = 2
    height = 5
    fig, axes = plt.subplots(height, width, figsize=(width * 6, height * 3))
    axes[-1, -1].axis('off')
    axes = axes.flatten()

    if ylim is None:
        ylim = max(max(y for y in property_dic[property] if y is not None) for property in properties if
                   any(y is not None for y in property_dic[property]))
    if xlim is None:
        xlim = max(x for x in property_dic['n'] if x is not None)

    for i in range(1, 10):
        density_value = 10 + (i - 1) * 10

        filtered_dic = {
            property: [x for x, t in zip(property_dic[property], property_dic['den']) if t == density_value]
            for property in property_dic if property != 'den'}

        if i == 1:
            labels = [_plot(axes[i - 1], filtered_dic['n'], filtered_dic[property], str(i)) for property in
                      properties]
        else:
            for property in properties:
                _plot(axes[i - 1], filtered_dic['n'], filtered_dic[property], str(i))

        # Linear y-axis with plain (non-scientific) tick labels, e.g. "10"
        # instead of the log formatter's "10^1".
        axes[i - 1].set_yscale('linear')
        axes[i - 1].ticklabel_format(style='plain', axis='y', useOffset=False)
        axes[i - 1].set_ylim(0, ylim)
        axes[i - 1].set_xlim(0, xlim)

        # Adding labels and legend
        axes[i - 1].set_title(f"{density_value}%")
        axes[i - 1].set_xlabel('n')
        axes[i - 1].set_ylabel('Time [s]')

    handle_label_pairs = [(h[0], name) for h, name in zip(labels, names) if h is not None]
    if handle_label_pairs:
        handles, handle_names = zip(*handle_label_pairs)
        fig.legend(handles=list(handles), labels=list(handle_names), loc="lower right")

    plt.tight_layout()
    plt.savefig(filename)
    plt.close('all')


draw_data(timedata, ['pur', 'tra', 'rot', 'ref', 'str', 'for', 'viz'],
          ['Node-based', 'Edge-based - translational', 'Edge-based - rotational', 'Edge-based - reflective',
           'Stress-based',
           'Even neighborhood distribution', 'Visual Symmetry'],
          f'{IMAGES_DIR}/sym_runtime_all.svg'
          )

draw_data(timedata, ['str', 'for', 'viz'],
          ['Stress',
           'Even neighborhood distribution', 'Pixel-based'],
          f'{IMAGES_DIR}/sym_runtime.svg'
          )
