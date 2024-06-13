import pickle

import pandas as pd
import seaborn as sns

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from gdMetriX import common


def smooth(y, box_pts):
    box = np.ones(box_pts) / box_pts
    y_smooth = np.convolve(y, box, mode='same')
    n = len(y)
    y_smooth[n-1] = y[n-1]
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

    cor_data = { property: [] for property in properties}


    for graph_key, graph_data in data.items():

        for property in properties:
            if property in graph_data:
                cor_data[property].append(graph_data[property])
            else:
                cor_data[property].append(None)

    df = pd.DataFrame(cor_data)
    sns.pairplot(df, diag_kind='kde')
    plt.savefig('sym_scatter.svg')
    plt.show()


    correlation_matrix = df.corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.savefig('sym_corr.svg')
    plt.show()


def correlation_matrix_2(data, row_prop, column_prop):

    cor_data = { property: [] for property in row_prop + column_prop}
    for graph_key, graph_data in data.items():

        for property in row_prop + column_prop:
            if property in graph_data:
                cor_data[property].append(graph_data[property])
            else:
                cor_data[property].append(None)

    df = pd.DataFrame(cor_data)

    # Scatter plot
    fig, axes = plt.subplots(len(row_prop), len(column_prop), figsize=(len(row_prop)*3, len(column_prop)*3))

    for i, g1 in enumerate(row_prop):
        for j, g2 in enumerate(column_prop):
            axes[i, j].scatter(df[g2], df[g1])

            # Label axes
            if i == len(row_prop) - 1:
                axes[i, j].set_xlabel(g2)
            if j == 0:
                axes[i, j].set_ylabel(g1)

    plt.tight_layout()
    plt.savefig('sym_scatter_2.svg')
    plt.show()



    # Correlation matrix

    group1 = df[row_prop]
    group2 = df[column_prop]

    correlation_matrix = pd.DataFrame(index=group1.columns, columns=group2.columns)
    for col1 in group1.columns:
        for col2 in group2.columns:
            correlation_matrix.loc[col1,col2] = group1[col1].corr(group2[col2])
    correlation_matrix = correlation_matrix.astype(float)

    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.savefig('sym_corr_2.svg')
    plt.show()



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


def draw_data(data, properties, names, xlim=None, ylim=None):
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
        ylim = max(max(y for y in property_dic[property] if y is not None) for property in properties if any(y is not None for y in property_dic[property]))
    if xlim is None:
        xlim = max(x for x in property_dic['n'] if x is not None)


    for i in range(1, 10):
        density_value = i * 10

        filtered_dic = {property: [x for x, t in zip(property_dic[property], property_dic['den']) if t == density_value]
                        for property in property_dic if property != 'den'}

        print(filtered_dic)

        if i == 1:
            labels = [_plot(axes[i - 1], filtered_dic['n'], filtered_dic[property], str(i)) for property in properties]
        else:
            for property in properties:
                _plot(axes[i - 1], filtered_dic['n'], filtered_dic[property], str(i))


        axes[i - 1].set_ylim(0, ylim)
        axes[i - 1].set_xlim(0, xlim)

        # Adding labels and legend
        axes[i - 1].set_title(f"{density_value}%")
        axes[i - 1].set_xlabel('n')
        axes[i - 1].set_ylabel('Time [s]')

    fig.legend(labels,
               labels=names,
               loc="lower right")

    # Display the plot
    plt.tight_layout()
    plt.savefig(f"sym_runtime.svg")
    plt.show()


draw_data(timedata, ['pur', 'tra', 'rot', 'ref', 'str', 'for', 'viz'],
          ['Node-based', 'Edge-based - translational', 'Edge-based - rotational', 'Edge-based - reflective', 'Stress',
           'Even neighborhood distribution', 'Pixel-based']
          )

draw_data(timedata, ['str', 'for', 'viz'],
          ['Stress',
           'Even neighborhood distribution', 'Pixel-based'],
          )
