import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.size": 14,
    "axes.titlesize": 14,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12
})

# Data
data = {
    "MinTotalSwitches": {
        "Weaving": (1.34, 14.87),
        "Stacking": (1.34, 14.94),
        "Realizable": (1.34, 14.87),
    },
    "MaxTotalSwitches": {
        "Weaving": (15.27, 126.28),
        "Stacking": (9.40, 43.60),
        "Realizable": (15.27, 126.28),
    },
    "MinMaxSwitches": {
        "Weaving": (0.59, 1.47),
        "Stacking": (0.59, 1.69),
        "Realizable": (0.59, 1.47),
    },
    "MinSwitchEdges": {
        "Weaving": (1.04, 8.05),
        "Stacking": (1.04, 7.88),
        "Realizable": (1.04, 8.05),
    },
}

goals = list(data.keys())
models = ["Weaving", "Stacking", "Realizable"]

x_labels = ["Small", "Large"]
x = np.arange(len(x_labels))
bar_width = 0.4

# Create subplot grid
fig, axes = plt.subplots(len(goals), len(models), figsize=(11, 9), sharex='row')

for i, goal in enumerate(goals):
    # Compute y-limits for the row
    row_values = [v for model_vals in data[goal].values() for v in model_vals]
    y_min, y_max = 0, max(row_values) * 1.1  # add 10% padding

    for j, model in enumerate(models):
        ax = axes[i, j]
        values = data[goal][model]
        ax.bar(x, values, width=bar_width, color=["tab:blue", "tab:orange"])

        # Set shared y-limits per row
        ax.set_ylim(y_min, y_max)

        ax.set_xticks(x)
        if j == 0:
            ax.set_ylabel(r"\textsc{" + goal + "}", rotation=90, va="center", ha="center", labelpad=10)
        if i == len(goals) - 1:
            ax.set_xticklabels(x_labels, rotation=0)
        else:
            ax.set_xticklabels([])
        if i == 0:
            ax.set_title(model)

# Common legend
handles = [axes[0,0].patches[0], axes[0,0].patches[1]]
fig.legend(handles, ["Small", "Large"], loc="upper right", frameon=False)

fig.text(0.5, 0.04, "Instance Size", ha="center")
fig.text(0.04, 0.5, "Cost", va="center", rotation="vertical")

plt.tight_layout(rect=[0.08, 0.05, 0.85, 0.95])
plt.savefig("experiment_costs2.pdf")
plt.show()
