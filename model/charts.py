import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import pandas as pd
import io

plt.style.use("seaborn-v0_8-darkgrid")
sns.set_palette(["#6366f1", "#a855f7", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6"])


class ChartGenerator:
    white_bg = False

    @staticmethod
    def _fig_to_bytes(fig) -> io.BytesIO:
        buf = io.BytesIO()
        kwargs = dict(format="png", dpi=200, bbox_inches="tight", pad_inches=0.1)
        if ChartGenerator.white_bg:
            kwargs.update(facecolor="white", edgecolor="none", transparent=False)
        fig.savefig(buf, **kwargs)
        buf.seek(0)
        plt.close(fig)
        return buf

    @staticmethod
    def _apply_white_bg_style(fig, ax):
        plt.style.use("default")
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        ax.tick_params(colors="black", labelcolor="black")
        ax.xaxis.label.set_color("black")
        ax.yaxis.label.set_color("black")
        ax.title.set_color("black")
        ax.grid(True, alpha=0.3, color="gray")
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_edgecolor("black")

    @staticmethod
    def _configure_axes(ax, title: str, xlabel: str, ylabel: str):
        if ChartGenerator.white_bg:
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
        else:
            ax.set_title(title, fontsize=12, fontweight="bold", color="#e2e8f0")
            ax.set_xlabel(xlabel, fontsize=10, color="#94a3b8")
            ax.set_ylabel(ylabel, fontsize=10, color="#94a3b8")
            ax.tick_params(labelsize=8, colors="#64748b")
            ax.grid(False)
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.set_facecolor("#0b0e14")
            ax.figure.patch.set_facecolor("#0b0e14")

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

        if ChartGenerator.white_bg:
            plt.style.use("default")
        fig, ax = plt.subplots(figsize=(8, 4.5))
        if ChartGenerator.white_bg:
            fig.patch.set_facecolor("white")
            ax.set_facecolor("white")

        edge_c = "white" if not ChartGenerator.white_bg else "black"
        colors = sns.color_palette("deep", len(values))
        x_pos = np.arange(len(values))
        bars = ax.bar(x_pos, fi, color=colors, edgecolor=edge_c, linewidth=0.5)

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
        ax.set_title(f"Distribución porcentual de {var_name} (n={n})", fontsize=11, fontweight="bold")
        fig.tight_layout()
        return ChartGenerator._fig_to_bytes(fig)

    @staticmethod
    def discrete_bar_chart(freq_result: dict, var_name: str) -> io.BytesIO:
        table = freq_result["table"]
        n = freq_result["n"]
        values = table.iloc[:, 0].astype(float)
        fi = table["fi"].values
        Fi = table["Fi"].values

        if ChartGenerator.white_bg:
            plt.style.use("default")
        fig, ax1 = plt.subplots(figsize=(9, 4.5))
        if ChartGenerator.white_bg:
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

        if ChartGenerator.white_bg:
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

        if ChartGenerator.white_bg:
            plt.style.use("default")
        fig, ax = plt.subplots(figsize=(9, 4.5))
        if ChartGenerator.white_bg:
            fig.patch.set_facecolor("white")
            ax.set_facecolor("white")

        edge_c = "white" if not ChartGenerator.white_bg else "black"
        bins_edges = np.arange(Xi[0] - C / 2, Xi[-1] + C, C)
        ax.hist(Xi, bins=bins_edges, weights=fi, edgecolor=edge_c, linewidth=0.8,
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

        if ChartGenerator.white_bg:
            plt.style.use("default")
        fig, ax1 = plt.subplots(figsize=(9, 4.5))
        if ChartGenerator.white_bg:
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

        if ChartGenerator.white_bg:
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
    def box_plot_chart(freq_result: dict, var_name: str) -> io.BytesIO:
        table = freq_result["table"]
        is_grouped = freq_result["is_grouped"]
        n = freq_result["n"]

        if is_grouped:
            values = np.repeat(table["Xi"].values, table["fi"].values.astype(int))
        else:
            first_col = table.columns[0]
            raw_series = pd.to_numeric(table[first_col], errors="coerce")
            if raw_series.isna().any():
                return None
            values = np.repeat(raw_series.values, table["fi"].values.astype(int))

        stats = {
            "med": float(np.percentile(values, 50)),
            "q1": float(np.percentile(values, 25)),
            "q3": float(np.percentile(values, 75)),
            "whislo": float(values.min()),
            "whishi": float(values.max()),
        }
        iqr = stats["q3"] - stats["q1"]
        stats["fliers"] = values[(values < stats["q1"] - 1.5 * iqr) | (values > stats["q3"] + 1.5 * iqr)].tolist()

        fig, ax = plt.subplots(figsize=(7, 4))
        if ChartGenerator.white_bg:
            edge_c = "black"
            tick_c = "black"
            grid_c = "gray"
            bg_c = "white"
        else:
            edge_c = "#e2e8f0"
            tick_c = "#64748b"
            grid_c = "#64748b"
            bg_c = "#0b0e14"
        ax.bxp([stats], vert=True, widths=0.4, patch_artist=True,
               boxprops={"facecolor": "#6366f1", "edgecolor": edge_c, "linewidth": 1.2},
               whiskerprops={"color": edge_c, "linewidth": 1.2},
               capprops={"color": edge_c, "linewidth": 1.2},
               medianprops={"color": "#f59e0b", "linewidth": 2},
               flierprops={"marker": "o", "markerfacecolor": "#ef4444", "markersize": 5, "markeredgecolor": "#ef4444"})
        ax.set_xticklabels([var_name], fontsize=10)
        ax.set_ylabel("Valores", fontsize=10)
        ax.set_title(f"Diagrama de caja y bigotes de {var_name} (n={n})", fontsize=11, fontweight="bold", color=tick_c)
        ax.tick_params(labelsize=8, colors=tick_c)
        ax.grid(axis="y", alpha=0.3 if ChartGenerator.white_bg else 0.2, color=grid_c)
        for spine in ax.spines.values():
            spine.set_visible(ChartGenerator.white_bg)
        ax.set_facecolor(bg_c)
        ax.figure.patch.set_facecolor(bg_c)
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
            bp = ChartGenerator.box_plot_chart(freq_result, var_name)
            if bp is not None:
                charts["boxplot"] = bp
        else:
            charts["histogram"] = ChartGenerator.histogram_chart(freq_result, var_name)
            charts["freq_poly_ogive"] = ChartGenerator.freq_polygon_ogive_chart(freq_result, var_name)
            bp = ChartGenerator.box_plot_chart(freq_result, var_name)
            if bp is not None:
                charts["boxplot"] = bp

        return charts
