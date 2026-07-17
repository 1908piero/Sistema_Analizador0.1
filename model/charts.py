import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import pandas as pd
import io

plt.style.use("default")
sns.set_palette(["#6366f1", "#a855f7", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6"])


class ChartGenerator:
    @staticmethod
    def _fig_to_bytes(fig) -> io.BytesIO:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", pad_inches=0.1,
                    facecolor="white", edgecolor="none", transparent=False)
        buf.seek(0)
        plt.close(fig)
        return buf

    @staticmethod
    def _configure_axes(ax, title: str, xlabel: str, ylabel: str):
        ax.set_title(title, fontsize=12, fontweight="bold", color="black")
        ax.set_xlabel(xlabel, fontsize=10, color="black")
        ax.set_ylabel(ylabel, fontsize=10, color="black")
        ax.tick_params(labelsize=8, colors="black")
        ax.grid(True, alpha=0.3, color="gray")
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_edgecolor("black")
        ax.set_facecolor("white")
        ax.figure.patch.set_facecolor("white")

    @staticmethod
    def _limit_categories(values, fi, max_cat=10):
        if len(values) <= max_cat:
            return values, fi
        top_idx = np.argsort(fi)[-max_cat + 1:]
        top_idx = sorted(top_idx)
        new_values = list(values[top_idx]) + ["Otros"]
        new_fi = list(fi[top_idx]) + [int(np.sum(fi) - np.sum(fi[top_idx]))]
        return np.array(new_values), np.array(new_fi)

    @staticmethod
    def bar_chart(freq_result: dict, var_name: str) -> io.BytesIO:
        table = freq_result["table"]
        n = freq_result["n"]
        values = table.iloc[:, 0].astype(str)
        fi = table["fi"].values

        if len(values) > 10:
            values, fi = ChartGenerator._limit_categories(values, fi)

        fig, ax = plt.subplots(figsize=(8, 4.5))
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        colors = sns.color_palette("deep", len(values))
        x_pos = np.arange(len(values))
        bars = ax.bar(x_pos, fi, color=colors, edgecolor="black", linewidth=0.5)

        for bar, val in zip(bars, fi):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(fi) * 0.01,
                    str(int(val)), ha="center", va="bottom", fontsize=8)

        ax.set_xticks(x_pos)
        rot = 90 if len(values) > 8 else 45
        ax.set_xticklabels(values, rotation=rot, ha="right", fontsize=7)
        ChartGenerator._configure_axes(ax, f"Distribución de {var_name} (n={n})", var_name, "Frecuencia absoluta")
        fig.tight_layout()
        return ChartGenerator._fig_to_bytes(fig)

    @staticmethod
    def pie_chart(freq_result: dict, var_name: str) -> io.BytesIO:
        table = freq_result["table"]
        n = freq_result["n"]
        values = table.iloc[:, 0].astype(str)
        fi = table["fi"].values

        if len(values) > 8:
            values, fi = ChartGenerator._limit_categories(values, fi, max_cat=8)

        fig, ax = plt.subplots(figsize=(7, 5))
        if len(values) > 8:
            wedges, texts, autotexts = ax.pie(
                fi, labels=None, autopct=None,
                startangle=90, colors=sns.color_palette("deep", len(values)),
            )
            ax.legend(wedges, values, loc="center left", bbox_to_anchor=(1, 0.5),
                      fontsize=7, title_fontsize=8, framealpha=0.8)
        else:
            wedges, texts, autotexts = ax.pie(
                fi, labels=values, autopct="%1.1f%%",
                startangle=90, colors=sns.color_palette("deep", len(values)),
                textprops={"fontsize": 8},
            )
            for t in autotexts:
                t.set_fontsize(7)
        ax.set_title(f"Distribución porcentual de {var_name} (n={n})", fontsize=11, fontweight="bold", color="black")
        fig.tight_layout()
        return ChartGenerator._fig_to_bytes(fig)

    @staticmethod
    def discrete_bar_chart(freq_result: dict, var_name: str) -> io.BytesIO:
        table = freq_result["table"]
        n = freq_result["n"]
        values = table.iloc[:, 0].astype(float)
        fi = table["fi"].values
        Fi = table["Fi"].values

        fig, ax1 = plt.subplots(figsize=(9, 4.5))
        fig.patch.set_facecolor("white")
        ax1.set_facecolor("white")
        ax1.tick_params(colors="black", labelcolor="black")
        ax1.xaxis.label.set_color("black")
        ax1.yaxis.label.set_color("black")
        ax1.title.set_color("black")
        for spine in ax1.spines.values():
            spine.set_edgecolor("black")

        colors = sns.color_palette("Blues_d", len(values))
        bars = ax1.bar(values, fi, width=0.6, color=colors, edgecolor="navy", linewidth=0.5, label="fi")
        ax1.set_xlabel(var_name, fontsize=10)
        ax1.set_ylabel("Frecuencia absoluta (fi)", fontsize=10, color="navy")
        ax1.tick_params(axis="y", labelcolor="navy")

        ax2 = ax1.twinx()
        ax2.plot(values, Fi, "o-", color="crimson", linewidth=1.5, markersize=4, label="Fi (Ojiva)")
        ax2.set_ylabel("Frecuencia acumulada (Fi)", fontsize=10, color="crimson")
        ax2.tick_params(axis="y", labelcolor="crimson")

        ax2.tick_params(colors="black", labelcolor="black")
        ax2.yaxis.label.set_color("black")
        for spine in ax2.spines.values():
            spine.set_edgecolor("black")

        for bar, val in zip(bars, fi):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(fi) * 0.01,
                     str(int(val)), ha="center", va="bottom", fontsize=7, color="navy")

        ax1.set_title(f"Distribución de {var_name} con Ojiva (n={n})", fontsize=11, fontweight="bold")
        fig.tight_layout()
        return ChartGenerator._fig_to_bytes(fig)

    @staticmethod
    def histogram_chart(freq_result: dict, var_name: str) -> io.BytesIO:
        table = freq_result["table"]
        n = freq_result["n"]
        C = freq_result.get("C", 1)
        Xi = table["Xi"].values
        fi = table["fi"].values

        fig, ax = plt.subplots(figsize=(9, 4.5))
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        bins_edges = np.arange(Xi[0] - C / 2, Xi[-1] + C, C)
        ax.hist(Xi, bins=bins_edges, weights=fi, edgecolor="black", linewidth=0.8,
                color=sns.color_palette("Blues_r", 1)[0], alpha=0.85)

        for x, f in zip(Xi, fi):
            ax.text(x, f + max(fi) * 0.01, str(int(f)), ha="center", va="bottom", fontsize=7)

        ChartGenerator._configure_axes(ax, f"Histograma de {var_name} (n={n})", var_name, "Frecuencia absoluta")
        fig.tight_layout()
        return ChartGenerator._fig_to_bytes(fig)

    @staticmethod
    def freq_polygon_ogive_chart(freq_result: dict, var_name: str) -> io.BytesIO:
        table = freq_result["table"]
        n = freq_result["n"]
        Xi = table["Xi"].values
        fi = table["fi"].values
        Fi = table["Fi"].values
        C = freq_result.get("C", Xi[1] - Xi[0] if len(Xi) > 1 else 1)

        fig, ax1 = plt.subplots(figsize=(9, 4.5))
        fig.patch.set_facecolor("white")
        ax1.set_facecolor("white")
        ax1.tick_params(colors="black", labelcolor="black")
        ax1.xaxis.label.set_color("black")
        ax1.yaxis.label.set_color("black")
        ax1.title.set_color("black")
        for spine in ax1.spines.values():
            spine.set_visible(True)
            spine.set_edgecolor("black")

        poly_x = np.concatenate([[Xi[0] - C], Xi, [Xi[-1] + C]])
        poly_y = np.concatenate([[0], fi, [0]])
        ax1.plot(poly_x, poly_y, "bo-", linewidth=1.5, markersize=4, label="Polígono de frecuencias")
        ax1.fill_between(poly_x, poly_y, alpha=0.1, color="blue")
        ax1.set_xlabel(var_name, fontsize=10)
        ax1.set_ylabel("Frecuencia absoluta (fi)", fontsize=10, color="blue")
        ax1.tick_params(axis="y", labelcolor="blue")

        ax2 = ax1.twinx()
        ogive_x = np.concatenate([[Xi[0] - C], Xi])
        ogive_y = np.concatenate([[0], Fi])
        ax2.plot(ogive_x, ogive_y, "ro-", linewidth=1.5, markersize=4, label="Ojiva (Fi)")
        ax2.set_ylabel("Frecuencia acumulada (Fi)", fontsize=10, color="red")
        ax2.tick_params(axis="y", labelcolor="red")

        ax2.tick_params(colors="black", labelcolor="black", axis="y")
        ax2.yaxis.label.set_color("black")
        for spine in ax2.spines.values():
            spine.set_edgecolor("black")

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)

        ax1.set_title(f"Polígono de frecuencias y Ojiva de {var_name} (n={n})", fontsize=11, fontweight="bold")
        fig.tight_layout()
        return ChartGenerator._fig_to_bytes(fig)

    @staticmethod
    def generate_all_charts(freq_result: dict, var_name: str) -> dict:
        var_type = freq_result["var_type"]
        charts = {}

        if var_type.startswith("cualitativa"):
            charts["bar"] = ChartGenerator.bar_chart(freq_result, var_name)
            charts["pie"] = ChartGenerator.pie_chart(freq_result, var_name)
        elif var_type == "cuantitativa_discreta":
            charts["bar_ogive"] = ChartGenerator.discrete_bar_chart(freq_result, var_name)
        else:
            charts["histogram"] = ChartGenerator.histogram_chart(freq_result, var_name)
            charts["freq_poly_ogive"] = ChartGenerator.freq_polygon_ogive_chart(freq_result, var_name)

        return charts
