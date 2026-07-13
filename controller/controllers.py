import pandas as pd
import os
import json
import traceback

from model.sampling import calculate_sample_size
from model.statistics import VariableClassifier, FrequencyAnalyzer, MeasuresCalculator, DatasetSummary
from model.charts import ChartGenerator
from export.docx_exporter import APA7Exporter


COUNTER_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "contador_export.json")


def _get_export_count():
    try:
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, "r") as f:
                data = json.load(f)
                return data.get("count", 0)
    except:
        pass
    return 0


def _increment_export_count():
    count = _get_export_count() + 1
    show_payment = count >= 3
    try:
        with open(COUNTER_FILE, "w") as f:
            json.dump({"count": count if not show_payment else 3}, f)
    except:
        pass
    return show_payment


def _reset_export_counter():
    try:
        with open(COUNTER_FILE, "w") as f:
            json.dump({"count": 0}, f)
    except:
        pass


class SamplingController:
    def __init__(self):
        pass

    def calculate(self, confidence: int, p: float, e: float, N: int = None) -> dict:
        try:
            result = calculate_sample_size(confidence, p, e, N)
            return {"success": True, "data": result}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Error inesperado: {str(e)}"}


class DatasetController:
    def __init__(self):
        self.df = None
        self.filepath = None
        self.classification = None
        self.freq_results = {}
        self.measures_results = {}
        self.charts_results = {}
        self._current_var = None

    def load_file(self, filepath: str) -> dict:
        if not os.path.exists(filepath):
            return {"success": False, "error": "El archivo no existe."}

        ext = os.path.splitext(filepath)[1].lower()
        try:
            if ext == ".csv":
                self.df = pd.read_csv(filepath, encoding="utf-8")
            elif ext in (".xls", ".xlsx"):
                self.df = pd.read_excel(filepath, engine="openpyxl")
            else:
                return {"success": False, "error": "Formato no soportado. Use CSV o Excel."}

            if self.df.empty:
                return {"success": False, "error": "El archivo está vacío."}

            self.filepath = filepath
            self.classification = VariableClassifier.classify(self.df)
            self.freq_results = {}
            self.measures_results = {}
            self.charts_results = {}
            self._current_var = None

            empty_cols = [col for col in self.df.columns if self.df[col].isna().all()]
            empty_msg = ""
            if empty_cols:
                empty_msg = f"columnas vacías detectadas: {', '.join(empty_cols)}"

            return {
                "success": True,
                "data": {
                    "rows": len(self.df),
                    "cols": len(self.df.columns),
                    "columns": list(self.df.columns),
                    "classification": self.classification,
                    "empty_columns": empty_cols,
                    "empty_msg": empty_msg,
                    "has_empty_cells": bool(self.df.isna().any().any()),
                },
            }
        except Exception as e:
            return {"success": False, "error": f"Error al cargar archivo: {str(e)}"}

    def load_from_google_sheets(self, url_or_id: str) -> dict:
        try:
            import gspread
            from gspread_dataframe import get_as_dataframe
            gc = gspread.service_account()
            try:
                sh = gc.open_by_url(url_or_id)
            except Exception:
                sh = gc.open_by_key(url_or_id)
            worksheet = sh.sheet1
            df = get_as_dataframe(worksheet, evaluate_formulas=True, dropna=False)
            df = df.dropna(how="all").reset_index(drop=True)
            if df.empty:
                return {"success": False, "error": "La hoja de cálculo está vacía."}
            self.df = df
            self.filepath = f"gsheet://{sh.id}"
            self.classification = VariableClassifier.classify(self.df)
            self.freq_results = {}
            self.measures_results = {}
            self.charts_results = {}
            self._current_var = None
            return {"success": True, "data": {"rows": len(df), "cols": len(df.columns)}}
        except ImportError:
            return {"success": False, "error": "Falta gspread. Instale con: pip install gspread gspread-dataframe"}
        except Exception as e:
            return {"success": False, "error": f"Error al importar de Google Sheets: {str(e)}"}

    def load_from_sql(self, conn_str: str, query: str) -> dict:
        try:
            from sqlalchemy import create_engine
            engine = create_engine(conn_str)
            df = pd.read_sql(query, engine)
            engine.dispose()
            if df.empty:
                return {"success": False, "error": "La consulta no devolvió datos."}
            self.df = df
            self.filepath = f"sql://{conn_str.split('@')[-1] if '@' in conn_str else conn_str}"
            self.classification = VariableClassifier.classify(self.df)
            self.freq_results = {}
            self.measures_results = {}
            self.charts_results = {}
            self._current_var = None
            return {"success": True, "data": {"rows": len(df), "cols": len(df.columns)}}
        except ImportError:
            return {"success": False, "error": "Falta SQLAlchemy. Instale con: pip install sqlalchemy mysql-connector-python"}
        except Exception as e:
            return {"success": False, "error": f"Error al conectar a base de datos: {str(e)}"}

    def validate_data(self) -> dict:
        if self.df is None:
            return {"valid": False, "msg": "No hay datos cargados."}

        issues = []
        for col in self.df.columns:
            n_null = self.df[col].isna().sum()
            if n_null > 0:
                issues.append(f"'{col}': {n_null} celda(s) vacía(s)")

        if issues:
            return {"valid": False, "msg": "Se encontraron problemas:", "issues": issues}
        return {"valid": True, "msg": "Datos válidos."}

    def analyze_variable(self, var_name: str) -> dict:
        if self.df is None:
            return {"success": False, "error": "No hay datos cargados."}

        if var_name not in self.df.columns:
            return {"success": False, "error": f"Variable '{var_name}' no encontrada."}

        try:
            var_type = self.classification.get(var_name, "desconocido")
            if var_type == "desconocido":
                return {"success": False, "error": f"Tipo de variable desconocido para '{var_name}'."}

            data = self.df[var_name]

            n_null = data.isna().sum()
            if n_null > 0:
                pass

            freq_result = FrequencyAnalyzer.compute(data, var_type, var_name)
            if freq_result is None:
                return {"success": False, "error": f"No se pudo calcular la distribución para '{var_name}'."}

            measures = MeasuresCalculator.compute(freq_result)
            charts = ChartGenerator.generate_all_charts(freq_result, var_name)

            self.freq_results[var_name] = freq_result
            self.measures_results[var_name] = measures
            self.charts_results[var_name] = charts
            self._current_var = var_name

            return {
                "success": True,
                "data": {
                    "freq_result": freq_result,
                    "measures": measures,
                    "charts": charts,
                    "n_null": int(n_null),
                    "var_type": var_type,
                },
            }
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": f"Error al analizar variable: {str(e)}"}

    def analyze_all(self) -> dict:
        if self.df is None:
            return {"success": False, "error": "No hay datos cargados."}
        try:
            summary = DatasetSummary.summary_statistics(self.df, self.classification)
            quant_vars = [c for c, t in self.classification.items() if t.startswith("cuantitativa")]
            qual_vars = [c for c, t in self.classification.items() if t.startswith("cualitativa")]
            return {
                "success": True,
                "data": {
                    "summary": summary,
                    "quant_vars": quant_vars,
                    "qual_vars": qual_vars,
                },
            }
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": f"Error: {str(e)}"}

    def export_report(self, sampling_result: dict = None, var_name: str = None,
                      output_path: str = "Reporte_Estadistico_APA7.docx") -> dict:
        try:
            exporter = APA7Exporter()

            all_analyses = []
            vars_to_export = [var_name] if var_name else list(self.df.columns)
            for v in vars_to_export:
                if v in self.freq_results:
                    all_analyses.append({
                        "freq_result": self.freq_results.get(v),
                        "measures": self.measures_results.get(v),
                        "charts": self.charts_results.get(v),
                    })

            summary = DatasetSummary.summary_statistics(self.df, self.classification)

            interpretations = {}
            for v in self.df.columns:
                if v in self.measures_results:
                    interpretations[v] = DatasetSummary.generate_interpretation(
                        self.measures_results[v], v)

            exporter.export_full_analysis(
                sampling_result=sampling_result,
                classification=self.classification,
                all_analyses=all_analyses,
                summary=summary,
                interpretations=interpretations,
                filepath=output_path,
            )
            show_payment = _increment_export_count()
            return {"success": True, "path": output_path, "show_payment": show_payment}
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": f"Error al exportar: {str(e)}"}
