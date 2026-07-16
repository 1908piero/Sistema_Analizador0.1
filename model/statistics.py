import numpy as np
import pandas as pd


class VariableClassifier:
    @staticmethod
    def classify(df: pd.DataFrame) -> dict:
        classification = {}
        for col in df.columns:
            col_data = df[col].dropna()
            if col_data.empty:
                classification[col] = "desconocido"
                continue

            unique_count = col_data.nunique()
            total = len(col_data)
            raw_dtype = col_data.dtype

            if pd.api.types.is_float_dtype(raw_dtype):
                classification[col] = "cuantitativa_continua"
            elif pd.api.types.is_integer_dtype(raw_dtype):
                classification[col] = "cuantitativa_discreta"
            elif pd.api.types.is_object_dtype(raw_dtype) or pd.api.types.is_string_dtype(raw_dtype):
                classification[col] = "cualitativa_nominal"
            else:
                classification[col] = "desconocido"
        return classification

    @staticmethod
    def reclassify(df: pd.DataFrame, col: str, new_type: str, current_classification: dict) -> dict:
        current_classification[col] = new_type
        return current_classification


class FrequencyAnalyzer:
    @staticmethod
    def compute(data: pd.Series, var_type: str, var_name: str) -> dict:
        data = data.dropna()
        n = len(data)
        if n == 0:
            return None

        try:
            min_val = float(data.min())
            max_val = float(data.max())
        except (ValueError, TypeError):
            min_val = None
            max_val = None

        result = {
            "var_name": var_name,
            "var_type": var_type,
            "n": n,
            "is_grouped": False,
            "table": None,
            "min": min_val,
            "max": max_val,
            "unique_values": int(data.nunique()),
        }

        if var_type.startswith("cualitativa"):
            result["table"] = FrequencyAnalyzer._ungrouped_table(data, var_name)
            result["is_grouped"] = False
        elif var_type == "cuantitativa_discreta":
            if data.nunique() <= 15:
                result["table"] = FrequencyAnalyzer._ungrouped_table(data, var_name)
                result["is_grouped"] = False
            else:
                grouped = FrequencyAnalyzer._grouped_table(data, var_name, n)
                result.update(grouped)
                result["is_grouped"] = True
        else:
            grouped = FrequencyAnalyzer._grouped_table(data, var_name, n)
            result.update(grouped)
            result["is_grouped"] = True

        return result

    @staticmethod
    def _ungrouped_table(data: pd.Series, var_name: str) -> pd.DataFrame:
        n = len(data)
        freq = data.value_counts().reset_index()
        freq.columns = [var_name, "fi"]
        if pd.api.types.is_numeric_dtype(freq[var_name]):
            freq = freq.sort_values(var_name).reset_index(drop=True)
        else:
            freq = freq.reset_index(drop=True)
        freq["Fi"] = freq["fi"].cumsum()
        freq["hi"] = freq["fi"] / n
        freq["hi%"] = freq["hi"] * 100
        freq["Hi%"] = freq["hi%"].cumsum()
        return freq

    @staticmethod
    def _grouped_table(data: pd.Series, var_name: str, n: int) -> dict:
        R = float(data.max() - data.min())
        m = max(2, int(np.ceil(1 + 3.322 * np.log10(n))))
        C = max(1, np.ceil(R / m) if R > 0 else 1)

        min_val = float(data.min())

        intervals = []
        for i in range(m):
            lower = min_val + i * C
            upper = lower + C
            intervals.append((lower, upper))

        labels = []
        fi_list = []
        xi_list = []

        for idx, (lower, upper) in enumerate(intervals):
            if idx == m - 1:
                count = int(((data >= lower) & (data <= upper)).sum())
                label = f"[{lower:.2f}, {upper:.2f}]"
            else:
                count = int(((data >= lower) & (data < upper)).sum())
                label = f"[{lower:.2f}, {upper:.2f})"
            labels.append(label)
            fi_list.append(count)
            xi_list.append((lower + upper) / 2)

        table = pd.DataFrame({
            "Intervalo": labels,
            "Xi": xi_list,
            "fi": fi_list,
        })
        table["Fi"] = table["fi"].cumsum()
        table["hi"] = table["fi"] / n
        table["hi%"] = table["hi"] * 100
        table["Hi%"] = table["hi%"].cumsum()

        return {"table": table, "R": R, "m": m, "C": C}


class MeasuresCalculator:
    @staticmethod
    def compute(freq_result: dict) -> dict:
        if freq_result is None:
            return None

        table = freq_result["table"]
        var_type = freq_result["var_type"]
        is_grouped = freq_result["is_grouped"]
        n = freq_result["n"]

        if var_type.startswith("cualitativa"):
            return MeasuresCalculator._categorical_measures(table, n)

        if is_grouped:
            return MeasuresCalculator._grouped_measures(freq_result, table, n)
        else:
            return MeasuresCalculator._ungrouped_measures(table, n)

    @staticmethod
    def _categorical_measures(table: pd.DataFrame, n: int) -> dict:
        mode_idx = table["fi"].idxmax()
        mode = table.iloc[mode_idx, 0]
        return {
            "n": n,
            "mode": mode,
            "type": "cualitativa",
        }

    @staticmethod
    def _grouped_measures(freq_result: dict, table: pd.DataFrame, n: int) -> dict:
        Xi = table["Xi"].values.astype(float)
        fi = table["fi"].values.astype(float)
        Fi = table["Fi"].values.astype(float)
        C = freq_result.get("C", Xi[1] - Xi[0] if len(Xi) > 1 else 1)

        mean = float(np.sum(fi * Xi) / n)

        half_n = n / 2
        median_idx = int(np.searchsorted(Fi, half_n, side="right"))
        if median_idx >= len(table):
            median_idx = len(table) - 1
        Li_med = float(table["Intervalo"].iloc[median_idx].strip("[]()").split(",")[0])
        Fi_med_prev = Fi[median_idx - 1] if median_idx > 0 else 0
        fi_med = fi[median_idx]
        median = float(Li_med + ((half_n - Fi_med_prev) / fi_med) * C) if fi_med > 0 else mean

        mode_idx = int(np.argmax(fi))
        if mode_idx == 0:
            d1 = fi[0]
            d2 = fi[0] - (fi[1] if len(fi) > 1 else 0)
        elif mode_idx == len(fi) - 1:
            d1 = fi[mode_idx] - fi[mode_idx - 1]
            d2 = fi[mode_idx]
        else:
            d1 = fi[mode_idx] - fi[mode_idx - 1]
            d2 = fi[mode_idx] - fi[mode_idx + 1]
        if d1 + d2 > 0:
            Li_mod = float(table["Intervalo"].iloc[mode_idx].strip("[]()").split(",")[0])
            mode = float(Li_mod + (d1 / (d1 + d2)) * C)
        else:
            mode = float(mean)

        with np.errstate(all="ignore"):
            safe_Xi = np.where(Xi > 0, Xi, 1e-10)
            geo_mean = float(np.exp(np.sum(fi * np.log(safe_Xi)) / n))
            safe_Xi_h = np.where(np.abs(Xi) > 1e-10, Xi, 1e10)
            harm_mean = float(n / np.sum(fi / safe_Xi_h))

        variance = float(np.sum(fi * (Xi - mean) ** 2) / (n - 1)) if n > 1 else 0
        std_dev = float(np.sqrt(variance))
        cv = float((std_dev / abs(mean)) * 100) if abs(mean) > 1e-10 else 0

        skewness = float(np.sum(fi * (Xi - mean) ** 3) / (n * std_dev ** 3)) if std_dev > 1e-10 else 0
        kurtosis = float(np.sum(fi * (Xi - mean) ** 4) / (n * std_dev ** 4) - 3) if std_dev > 1e-10 else 0

        Q1 = MeasuresCalculator._position_measure(table, n, 1, "q", C)
        Q2 = MeasuresCalculator._position_measure(table, n, 2, "q", C)
        Q3 = MeasuresCalculator._position_measure(table, n, 3, "q", C)
        D1 = MeasuresCalculator._position_measure(table, n, 1, "d", C)
        D5 = MeasuresCalculator._position_measure(table, n, 5, "d", C)
        D9 = MeasuresCalculator._position_measure(table, n, 9, "d", C)
        P10 = MeasuresCalculator._position_measure(table, n, 10, "p", C)
        P25 = MeasuresCalculator._position_measure(table, n, 25, "p", C)
        P50 = MeasuresCalculator._position_measure(table, n, 50, "p", C)
        P75 = MeasuresCalculator._position_measure(table, n, 75, "p", C)
        P90 = MeasuresCalculator._position_measure(table, n, 90, "p", C)

        return {
            "n": n,
            "mean": mean,
            "median": median,
            "mode": mode,
            "geometric_mean": geo_mean,
            "harmonic_mean": harm_mean,
            "range": freq_result.get("R", float(Xi[-1] - Xi[0])),
            "variance": variance,
            "std_dev": std_dev,
            "cv": cv,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "Q1": Q1, "Q2": Q2, "Q3": Q3,
            "D1": D1, "D5": D5, "D9": D9,
            "P10": P10, "P25": P25, "P50": P50, "P75": P75, "P90": P90,
            "C": C,
            "type": "cuantitativa",
        }

    @staticmethod
    def _ungrouped_measures(table: pd.DataFrame, n: int) -> dict:
        values_col = table.columns[0]
        Xi = table[values_col].values.astype(float)
        fi = table["fi"].values.astype(float)

        mean = float(np.sum(fi * Xi) / n)

        values_repeated = np.repeat(Xi, fi.astype(int))
        sorted_vals = np.sort(values_repeated)
        if n % 2 == 0:
            median = float((sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2)
        else:
            median = float(sorted_vals[n // 2])

        mode_idx = int(np.argmax(fi))
        mode = float(Xi[mode_idx])

        with np.errstate(all="ignore"):
            valid_g = Xi > 0
            geo_mean = float(np.exp(np.sum(fi[valid_g] * np.log(Xi[valid_g])) / n)) if valid_g.any() else 0
            valid_h = np.abs(Xi) > 1e-10
            harm_mean = float(n / np.sum(fi[valid_h] / Xi[valid_h])) if valid_h.any() else 0

        variance = float(np.sum(fi * (Xi - mean) ** 2) / (n - 1)) if n > 1 else 0
        std_dev = float(np.sqrt(variance))
        cv = float((std_dev / abs(mean)) * 100) if abs(mean) > 1e-10 else 0

        skewness = float(np.sum(fi * (Xi - mean) ** 3) / (n * std_dev ** 3)) if std_dev > 1e-10 else 0
        kurtosis = float(np.sum(fi * (Xi - mean) ** 4) / (n * std_dev ** 4) - 3) if std_dev > 1e-10 else 0

        Q1 = float(np.percentile(sorted_vals, 25))
        Q2 = float(np.percentile(sorted_vals, 50))
        Q3 = float(np.percentile(sorted_vals, 75))
        D1 = float(np.percentile(sorted_vals, 10))
        D5 = float(np.percentile(sorted_vals, 50))
        D9 = float(np.percentile(sorted_vals, 90))
        P10 = float(np.percentile(sorted_vals, 10))
        P25 = float(np.percentile(sorted_vals, 25))
        P50 = float(np.percentile(sorted_vals, 50))
        P75 = float(np.percentile(sorted_vals, 75))
        P90 = float(np.percentile(sorted_vals, 90))

        return {
            "n": n,
            "mean": mean,
            "median": median,
            "mode": mode,
            "geometric_mean": geo_mean,
            "harmonic_mean": harm_mean,
            "range": float(Xi[-1] - Xi[0]),
            "variance": variance,
            "std_dev": std_dev,
            "cv": cv,
            "skewness": skewness,
            "kurtosis": kurtosis,
            "Q1": Q1, "Q2": Q2, "Q3": Q3,
            "D1": D1, "D5": D5, "D9": D9,
            "P10": P10, "P25": P25, "P50": P50, "P75": P75, "P90": P90,
            "type": "cuantitativa",
        }

    @staticmethod
    def _position_measure(table: pd.DataFrame, n: int, k: int, kind: str, C: float) -> float:
        if kind == "q":
            pos = k * n / 4
        elif kind == "d":
            pos = k * n / 10
        else:
            pos = k * n / 100

        Fi = table["Fi"].values.astype(float)
        idx = int(np.searchsorted(Fi, pos, side="right"))
        if idx >= len(table):
            idx = len(table) - 1

        interval_str = table["Intervalo"].iloc[idx]
        lower = float(interval_str.strip("[]()").split(",")[0])
        Fi_prev = Fi[idx - 1] if idx > 0 else 0
        fi = float(table["fi"].values[idx])

        if fi > 0:
            return float(lower + ((pos - Fi_prev) / fi) * C)
        return float(lower)


class DatasetSummary:
    @staticmethod
    def summary_statistics(df: pd.DataFrame, classification: dict) -> pd.DataFrame:
        quant_vars = [col for col, typ in classification.items()
                      if typ.startswith("cuantitativa")]
        if not quant_vars:
            return None
        rows = []
        for col in quant_vars:
            data = df[col].dropna()
            n = len(data)
            if n == 0:
                continue
            mean = float(data.mean())
            std = float(data.std(ddof=1))
            mini = float(data.min())
            maxi = float(data.max())
            q1 = float(data.quantile(0.25))
            q2 = float(data.median())
            q3 = float(data.quantile(0.75))
            skew = float(data.skew())
            kurt = float(data.kurtosis())
            cv = float((std / abs(mean)) * 100) if abs(mean) > 1e-10 else 0
            rows.append([col, n, mean, std, mini, q1, q2, q3, maxi, skew, kurt, cv])
        if not rows:
            return None
        return pd.DataFrame(rows, columns=[
            "Variable", "n", "Media", "D.E.", "Min", "Q1", "Mediana", "Q3", "Max",
            "Asimetría", "Curtosis", "CV%"
        ])

    @staticmethod
    def generate_interpretation(measures: dict, var_name: str) -> str:
        if measures is None:
            return ""
        if measures.get("type") == "cualitativa":
            mode_val = measures.get("mode", "N/A")
            return (
                f"En cuanto a '{var_name}', la categoría que más se repite es "
                f"'{mode_val}', lo que significa que es el valor predominante "
                f"dentro del conjunto de datos analizado."
            )
        mean = measures["mean"]
        median = measures["median"]
        std = measures["std_dev"]
        cv = measures["cv"]
        skew = measures["skewness"]
        kurt = measures["kurtosis"]
        n = measures["n"]
        diff = abs(mean - median)
        parts = []
        parts.append(
            f"Al analizar '{var_name}' se obtuvieron {n} observaciones válidas. "
            f"En promedio, los valores rondan los {mean:.2f} puntos, "
            f"y al ordenar los datos de menor a mayor, el valor central (mediana) "
            f"se ubica en {median:.2f}. "
        )
        if diff < 0.5:
            parts.append(
                f"Como la media y la mediana son muy cercanas, los datos "
                f"tienen una distribución bastante simétrica. "
            )
        elif mean > median:
            parts.append(
                f"Notamos que la media es un poco más alta que la mediana, "
                f"lo que sugiere que hay algunos valores elevados que jalan "
                f"el promedio hacia arriba (asimetría positiva). "
            )
        else:
            parts.append(
                f"La mediana es más alta que la media, indicando que existen "
                f"valores bajos que están jalando el promedio hacia abajo "
                f"(asimetría negativa). "
            )
        parts.append(
            f"Los datos se dispersan en promedio {std:.2f} unidades alrededor "
            f"de la media, con un coeficiente de variación del {cv:.2f}%. "
        )
        if cv < 15:
            parts.append(
                f"Esto indica que los datos son bastante homogéneos, "
                f"es decir, no hay mucha variabilidad entre ellos. "
            )
        elif cv < 35:
            parts.append(
                f"Esto nos dice que la variabilidad es moderada, "
                f"ni muy poca ni excesiva. "
            )
        else:
            parts.append(
                f"Esto revela una alta heterogeneidad en los datos, "
                f"es decir, los valores están bastante dispersos entre sí. "
            )
        if kurt > 0.5:
            parts.append(
                f"En cuanto a la forma de la distribución, tiene una curtosis "
                f"de {kurt:.2f}, lo que significa que es más puntiaguda "
                f"que una campana normal (leptocúrtica), con valores más "
                f"concentrados en el centro. "
            )
        elif kurt < -0.5:
            parts.append(
                f"Respecto a la forma, presenta una curtosis de {kurt:.2f}, "
                f"indicando que es más aplanada que la distribución normal "
                f"(platicúrtica), con los datos más dispersos hacia los extremos. "
            )
        else:
            parts.append(
                f"La curtosis de {kurt:.2f} sugiere que la forma de la "
                f"distribución es similar a la de una campana normal "
                f"(mesocúrtica). "
            )
        return "".join(parts)
