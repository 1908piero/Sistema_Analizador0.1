import numpy as np
from scipy import stats
import pandas as pd


class ANOVAOneWay:
    def __init__(self, groups: list, alpha: float = 0.05):
        self.groups = [np.array(g, dtype=float) for g in groups]
        self.alpha = alpha
        self.k = len(groups)
        self.N = sum(len(g) for g in groups)
        self.result = None

    def compute(self) -> dict:
        groups = self.groups
        k = self.k
        N = self.N
        alpha = self.alpha

        all_data = np.concatenate(groups)
        grand_mean = np.mean(all_data)

        group_means = [np.mean(g) for g in groups]
        group_sizes = [len(g) for g in groups]

        SC_trat = sum(ni * (xi - grand_mean) ** 2 for ni, xi in zip(group_sizes, group_means))
        SC_error = sum(sum((x - xi) ** 2 for x in g) for g, xi in zip(groups, group_means))
        SC_total = SC_trat + SC_error

        GL_trat = k - 1
        GL_error = N - k
        GL_total = N - 1

        MC_trat = SC_trat / GL_trat if GL_trat > 0 else 0
        MC_error = SC_error / GL_error if GL_error > 0 else 0

        F_calc = MC_trat / MC_error if MC_error > 0 else 0

        p_value = 1 - stats.f.cdf(F_calc, GL_trat, GL_error) if F_calc > 0 else 1.0

        F_tab = stats.f.ppf(1 - alpha, GL_trat, GL_error)

        conclusion = (
            f"Como F_cal ({F_calc:.4f}) > F_tab ({F_tab:.4f}) → H0 se rechaza. Existe diferencia significativa."
            if F_calc > F_tab
            else f"Como F_cal ({F_calc:.4f}) < F_tab ({F_tab:.4f}) → H0 se acepta. No existe diferencia significativa."
        )

        table = pd.DataFrame({
            "FV": ["Entre grupos", "Dentro de grupos", "Total"],
            "SC": [SC_trat, SC_error, SC_total],
            "GL": [GL_trat, GL_error, GL_total],
            "MC": [MC_trat, MC_error, None],
            "F": [F_calc, None, None],
            "p-value": [p_value, None, None],
        })

        self.result = {
            "table": table,
            "F_calc": F_calc,
            "F_tab": F_tab,
            "p_value": p_value,
            "alpha": alpha,
            "conclusion": conclusion,
            "group_means": group_means,
            "grand_mean": grand_mean,
            "k": k,
            "N": N,
        }
        return self.result

    def tukey_hsd(self) -> list:
        if self.result is None:
            return []
        groups = self.groups
        k = self.k
        N = self.N
        MS_error = self.result["table"].loc[1, "MC"]
        df_error = self.result["table"].loc[1, "GL"]

        group_means = [np.mean(g) for g in groups]
        group_sizes = [len(g) for g in groups]
        group_labels = [f"Grupo {i+1}" for i in range(k)]

        q_crit = stats.studentized_range.ppf(1 - self.alpha, k, df_error) if df_error > 0 else 0

        comparisons = []
        for i in range(k):
            for j in range(i + 1, k):
                diff = abs(group_means[i] - group_means[j])
                se = np.sqrt(MS_error / 2 * (1 / group_sizes[i] + 1 / group_sizes[j]))
                hsd = q_crit * se if q_crit > 0 else 0
                comparisons.append({
                    "group1": group_labels[i],
                    "group2": group_labels[j],
                    "mean1": group_means[i],
                    "mean2": group_means[j],
                    "diff": diff,
                    "hsd": hsd,
                    "significant": diff > hsd,
                })
        return comparisons


class ANOVATwoWay:
    def __init__(self, data: pd.DataFrame, alpha: float = 0.05):
        self.data = data
        self.alpha = alpha
        self.result = None

    def compute(self) -> dict:
        df = self.data
        alpha = self.alpha

        required = ["Factor1", "Factor2", "Valor"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Columna '{col}' requerida")

        df["Factor1"] = df["Factor1"].astype("category")
        df["Factor2"] = df["Factor2"].astype("category")

        a = df["Factor1"].nunique()
        b = df["Factor2"].nunique()
        n = len(df) // (a * b)
        N = len(df)

        grand_mean = df["Valor"].mean()

        SC_total = sum((x - grand_mean) ** 2 for x in df["Valor"])

        means_A = df.groupby("Factor1")["Valor"].mean()
        means_B = df.groupby("Factor2")["Valor"].mean()
        means_AB = df.groupby(["Factor1", "Factor2"])["Valor"].mean()

        SC_A = b * n * sum((means_A[level] - grand_mean) ** 2 for level in means_A.index)
        SC_B = a * n * sum((means_B[level] - grand_mean) ** 2 for level in means_B.index)

        SC_AB = 0
        for (f1, f2), val in means_AB.items():
            SC_AB += n * (val - means_A[f1] - means_B[f2] + grand_mean) ** 2

        SC_error = SC_total - SC_A - SC_B - SC_AB

        GL_A = a - 1
        GL_B = b - 1
        GL_AB = (a - 1) * (b - 1)
        GL_error = N - a * b
        GL_total = N - 1

        MC_A = SC_A / GL_A if GL_A > 0 else 0
        MC_B = SC_B / GL_B if GL_B > 0 else 0
        MC_AB = SC_AB / GL_AB if GL_AB > 0 else 0
        MC_error = SC_error / GL_error if GL_error > 0 else 0

        F_A = MC_A / MC_error if MC_error > 0 else 0
        F_B = MC_B / MC_error if MC_error > 0 else 0
        F_AB = MC_AB / MC_error if MC_error > 0 else 0

        p_A = 1 - stats.f.cdf(F_A, GL_A, GL_error) if F_A > 0 else 1.0
        p_B = 1 - stats.f.cdf(F_B, GL_B, GL_error) if F_B > 0 else 1.0
        p_AB = 1 - stats.f.cdf(F_AB, GL_AB, GL_error) if F_AB > 0 else 1.0

        F_tab_A = stats.f.ppf(1 - alpha, GL_A, GL_error)
        F_tab_B = stats.f.ppf(1 - alpha, GL_B, GL_error)
        F_tab_AB = stats.f.ppf(1 - alpha, GL_AB, GL_error)

        def make_conclusion(label, F_c, F_t):
            if F_c > F_t:
                return f"Como F_cal ({F_c:.4f}) > F_tab ({F_t:.4f}) → H0 se rechaza. {label} tiene efecto significativo."
            return f"Como F_cal ({F_c:.4f}) < F_tab ({F_t:.4f}) → H0 se acepta. {label} no tiene efecto significativo."

        rows = [
            {"FV": f"Factor A (F1)", "SC": SC_A, "GL": GL_A, "MC": MC_A, "F": F_A, "p-value": p_A},
            {"FV": f"Factor B (F2)", "SC": SC_B, "GL": GL_B, "MC": MC_B, "F": F_B, "p-value": p_B},
            {"FV": "Interacción AxB", "SC": SC_AB, "GL": GL_AB, "MC": MC_AB, "F": F_AB, "p-value": p_AB},
            {"FV": "Error", "SC": SC_error, "GL": GL_error, "MC": MC_error, "F": None, "p-value": None},
            {"FV": "Total", "SC": SC_total, "GL": GL_total, "MC": None, "F": None, "p-value": None},
        ]

        table = pd.DataFrame(rows)

        self.result = {
            "table": table,
            "conclusions": {
                "Factor A (F1)": make_conclusion("Factor A (F1)", F_A, F_tab_A),
                "Factor B (F2)": make_conclusion("Factor B (F2)", F_B, F_tab_B),
                "Interacción AxB": make_conclusion("Interacción AxB", F_AB, F_tab_AB),
            },
            "F_calc": {"A": F_A, "B": F_B, "AB": F_AB},
            "F_tab": {"A": F_tab_A, "B": F_tab_B, "AB": F_tab_AB},
            "p_values": {"A": p_A, "B": p_B, "AB": p_AB},
            "alpha": alpha,
            "a": a,
            "b": b,
            "n": n,
            "N": N,
        }
        return self.result
