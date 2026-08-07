"""
SEDAS - Report Figure Generation
MIS5320 Part B | Generates publication-quality charts from the model
comparison results for inclusion in the final report.
Outputs PNG files to docs/figures/
Run: python services/detection/generate_charts.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent.parent / "docs" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BRAND = "#1f4e5f"
ACCENT = "#c0392b"
LIGHT = "#7fb3c4"
GREY = "#95a5a6"

# ---------------- Results data (from our experiments) ----------------
models = ["SVC /\nLinearSVC", "Random\nForest", "Logistic\nRegression",
          "XGBoost", "Multinomial\nNaive Bayes"]
our_f1 = [99.16, 98.71, 98.65, 97.56, 97.47]
paper_f1 = [99.0, 98.0, None, None, 98.0]   # None = not tested in paper

# Full metrics for the three replicated models
repl_models = ["SVC / LinearSVC", "Random Forest", "Multinomial NB"]
our_metrics = {
    "Accuracy":  [99.12, 98.66, 97.41],
    "Precision": [99.13, 98.80, 99.06],
    "Recall":    [99.18, 98.62, 95.93],
    "F1":        [99.16, 98.71, 97.47],
}
paper_metrics = {
    "Accuracy":  [99.1, 98.4, 97.8],
    "Precision": [99.0, 98.0, 97.0],
    "Recall":    [99.0, 99.0, 99.0],
    "F1":        [99.0, 98.0, 98.0],
}

# Confusion matrices (TN, FP, FN, TP)
confusions = {
    "SVC / LinearSVC":  (7844, 75, 70, 8509),
    "Random Forest":    (7816, 103, 118, 8461),
    "Multinomial NB":   (7841, 78, 349, 8230),
    "XGBoost":          (7595, 324, 100, 8479),
}

# Experiment plateau data
experiments = ["SVC\nbaseline", "SVC +\nengineered\nfeatures",
               "Equal-weight\nensemble", "Weighted\nensemble",
               "SVC tuned\n(C=2.0)"]
exp_f1 = [99.16, 99.16, 99.13, 99.17, 99.17]


def fig1_model_comparison():
    """All five models vs the paper's reported results."""
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(models))
    width = 0.38

    ax.bar(x - width/2, our_f1, width, label="SEDAS (our results)",
           color=BRAND, edgecolor="white")
    paper_vals = [v if v is not None else 0 for v in paper_f1]
    ax.bar(x + width/2, paper_vals, width,
           label="Paper [41] reported", color=LIGHT, edgecolor="white")

    for i, v in enumerate(paper_f1):
        if v is None:
            ax.text(x[i] + width/2, 1, "not tested\nin paper", ha="center",
                    va="bottom", fontsize=8, style="italic", color=GREY,
                    rotation=90)

    for i, v in enumerate(our_f1):
        ax.text(x[i] - width/2, v + 0.15, f"{v:.2f}", ha="center",
                fontsize=9, fontweight="bold")
    for i, v in enumerate(paper_f1):
        if v is not None:
            ax.text(x[i] + width/2, v + 0.15, f"{v:.1f}", ha="center", fontsize=9)

    ax.set_ylabel("F1 Score (%)", fontsize=11)
    ax.set_title("Figure 1: Model comparison - SEDAS replication vs published benchmark [41]\n"
                 "(identical dataset, 82,486 emails)", fontsize=12, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=9)
    ax.set_ylim(95, 100.5)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig1_model_comparison.png", dpi=300)
    plt.close()
    print("  fig1_model_comparison.png")


def fig2_metrics_grouped():
    """Four metrics across the three replicated models."""
    fig, axes = plt.subplots(1, 4, figsize=(15, 4.5), sharey=True)
    x = np.arange(len(repl_models))
    width = 0.38

    for ax, metric in zip(axes, ["Accuracy", "Precision", "Recall", "F1"]):
        ax.bar(x - width/2, our_metrics[metric], width, label="SEDAS",
               color=BRAND, edgecolor="white")
        ax.bar(x + width/2, paper_metrics[metric], width, label="Paper [41]",
               color=LIGHT, edgecolor="white")
        ax.set_title(metric, fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(["SVC", "RF", "MNB"], fontsize=9)
        ax.set_ylim(94, 100.5)
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.set_axisbelow(True)

    axes[0].set_ylabel("Score (%)", fontsize=11)
    axes[0].legend(fontsize=9)
    fig.suptitle("Figure 2: Evaluation metrics - SEDAS vs published benchmark [41]",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig2_metrics_grouped.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("  fig2_metrics_grouped.png")


def fig3_confusion_matrices():
    """Confusion matrix heatmaps for four models."""
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    for ax, (name, (tn, fp, fn, tp)) in zip(axes, confusions.items()):
        matrix = np.array([[tn, fp], [fn, tp]])
        ax.imshow(matrix, cmap="Blues", aspect="auto")
        for i in range(2):
            for j in range(2):
                val = matrix[i, j]
                colour = "white" if val > matrix.max() * 0.5 else "black"
                ax.text(j, i, f"{val:,}", ha="center", va="center",
                        color=colour, fontsize=12, fontweight="bold")
        ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
        ax.set_xticklabels(["Pred.\nLegitimate", "Pred.\nPhishing"], fontsize=9)
        ax.set_yticklabels(["Actual\nLegitimate", "Actual\nPhishing"], fontsize=9)
        ax.set_title(name, fontsize=11, fontweight="bold", pad=10)
    fig.suptitle("Figure 3: Confusion matrices on the 16,498-email held-out test set",
                 fontsize=13, fontweight="bold", y=1.05)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig3_confusion_matrices.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("  fig3_confusion_matrices.png")


def fig4_false_positives():
    """False positive comparison - operationally important, not reported in paper."""
    fig, ax = plt.subplots(figsize=(9, 5))
    names = list(confusions.keys())
    fps = [confusions[n][1] for n in names]
    colours = [BRAND if f < 150 else ACCENT for f in fps]

    bars = ax.bar(names, fps, color=colours, edgecolor="white", width=0.55)
    for bar, v in zip(bars, fps):
        ax.text(bar.get_x() + bar.get_width()/2, v + 5, str(v),
                ha="center", fontsize=11, fontweight="bold")

    ax.set_ylabel("False positives (legitimate emails wrongly flagged)", fontsize=10)
    ax.set_title("Figure 4: False positive counts - an operational metric\n"
                 "not reported in the benchmark paper [41]",
                 fontsize=12, fontweight="bold", pad=15)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    plt.xticks(fontsize=9)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig4_false_positives.png", dpi=300)
    plt.close()
    print("  fig4_false_positives.png")


def fig5_plateau():
    """The performance ceiling finding - supports the significance argument."""
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(experiments))

    ax.plot(x, exp_f1, marker="o", markersize=10, linewidth=2.5,
            color=BRAND, label="SEDAS experiments")
    ax.axhline(99.0, color=ACCENT, linestyle="--", linewidth=2,
               label="Paper [41] benchmark (99.0%)")

    for i, v in enumerate(exp_f1):
        ax.text(x[i], v + 0.02, f"{v:.2f}", ha="center",
                fontsize=10, fontweight="bold")

    ax.fill_between([-0.5, len(experiments)-0.5], 99.13, 99.17,
                    alpha=0.15, color=BRAND,
                    label="Observed ceiling (99.13-99.17%)")

    ax.set_ylabel("F1 Score (%)", fontsize=11)
    ax.set_title("Figure 5: Performance ceiling across five optimisation attempts\n"
                 "TF-IDF with linear classifiers converges to ~99.15% on this dataset",
                 fontsize=12, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(experiments, fontsize=9)
    ax.set_xlim(-0.5, len(experiments) - 0.5)
    ax.set_ylim(98.9, 99.3)
    ax.legend(fontsize=9, loc="lower right")
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "fig5_performance_ceiling.png", dpi=300)
    plt.close()
    print("  fig5_performance_ceiling.png")


if __name__ == "__main__":
    print(f"Generating figures into: {OUT_DIR}\n")
    fig1_model_comparison()
    fig2_metrics_grouped()
    fig3_confusion_matrices()
    fig4_false_positives()
    fig5_plateau()
    print(f"\nDone. 5 figures written to {OUT_DIR}")
