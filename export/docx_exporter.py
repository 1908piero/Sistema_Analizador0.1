from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import pandas as pd
import io


APA_FONT = "Times New Roman"
APA_SIZE = Pt(12)


def _set_cell_borders(cell, top=None, bottom=None, start=None, end=None):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}></w:tcBorders>')
    if top:
        tcBorders.append(parse_xml(
            f'<w:top {nsdecls("w")} w:val="single" w:sz="{top}" w:space="0" w:color="000000"/>'))
    if bottom:
        tcBorders.append(parse_xml(
            f'<w:bottom {nsdecls("w")} w:val="single" w:sz="{bottom}" w:space="0" w:color="000000"/>'))
    if start:
        tcBorders.append(parse_xml(
            f'<w:start {nsdecls("w")} w:val="nil"/>'))
    if end:
        tcBorders.append(parse_xml(
            f'<w:end {nsdecls("w")} w:val="nil"/>'))
    tcPr.append(tcBorders)


def _remove_vertical_borders(table):
    for row in table.rows:
        for cell in row.cells:
            _set_cell_borders(cell, start=True, end=True)


def _set_row_borders(row, sz_top=None, sz_bottom=None):
    for cell in row.cells:
        _set_cell_borders(cell, top=sz_top, bottom=sz_bottom)
        _set_cell_borders(cell, start=True, end=True)


class APA7Exporter:
    def __init__(self):
        self.doc = Document()
        self._setup_document()
        self.table_counter = 0
        self.figure_counter = 0

    def _setup_document(self):
        style = self.doc.styles["Normal"]
        font = style.font
        font.name = APA_FONT
        font.size = APA_SIZE
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.line_spacing = 1.5

        sections = self.doc.sections
        for section in sections:
            section.top_margin = Cm(2.54)
            section.bottom_margin = Cm(2.54)
            section.left_margin = Cm(2.54)
            section.right_margin = Cm(2.54)

    def _add_title(self, text: str, level: int = 1):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 0 else WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(text)
        run.bold = True
        run.font.name = APA_FONT
        run.font.size = Pt(14 if level == 0 else 12)
        p.paragraph_format.space_after = Pt(12)
        return p

    def _add_heading_apa(self, text: str, level: int = 1):
        p = self.doc.add_paragraph()
        run = p.add_run(text)
        run.bold = True
        run.font.name = APA_FONT
        run.font.size = APA_SIZE
        if level == 1:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif level == 2:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        return p

    def _add_paragraph(self, text: str):
        p = self.doc.add_paragraph()
        run = p.add_run(text)
        run.font.name = APA_FONT
        run.font.size = APA_SIZE
        return p

    def _format_table_title(self, title: str):
        self.table_counter += 1
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(f"Tabla {self.table_counter}")
        run.bold = True
        run.font.name = APA_FONT
        run.font.size = APA_SIZE
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(12)

        p2 = self.doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run2 = p2.add_run(title)
        run2.italic = True
        run2.font.name = APA_FONT
        run2.font.size = APA_SIZE
        p2.paragraph_format.space_after = Pt(6)
        return p2

    def _format_figure_title(self, title: str):
        self.figure_counter += 1
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(f"Figura {self.figure_counter}")
        run.bold = True
        run.font.name = APA_FONT
        run.font.size = APA_SIZE
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(12)

        p2 = self.doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run2 = p2.add_run(title)
        run2.italic = True
        run2.font.name = APA_FONT
        run2.font.size = APA_SIZE
        p2.paragraph_format.space_after = Pt(6)
        return p2

    def _add_note(self, text: str = "Datos procesados automáticamente por el software estadístico."):
        p = self.doc.add_paragraph()
        run_label = p.add_run("Nota. ")
        run_label.italic = True
        run_label.font.name = APA_FONT
        run_label.font.size = Pt(10)
        run_text = p.add_run(text)
        run_text.font.name = APA_FONT
        run_text.font.size = Pt(10)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(12)
        return p

    def _apa_table_from_df(self, df: pd.DataFrame, title: str):
        self._format_table_title(title)
        n_rows, n_cols = df.shape
        table = self.doc.add_table(rows=n_rows + 1, cols=n_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        for j, col_name in enumerate(df.columns):
            cell = table.rows[0].cells[j]
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(str(col_name))
            run.bold = True
            run.font.name = APA_FONT
            run.font.size = Pt(10)

        for i in range(n_rows):
            for j in range(n_cols):
                cell = table.rows[i + 1].cells[j]
                val = df.iloc[i, j]
                if isinstance(val, float):
                    val = f"{val:.4f}"
                else:
                    val = str(val)
                cell.text = ""
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(val)
                run.font.name = APA_FONT
                run.font.size = Pt(10)

        _remove_vertical_borders(table)
        _set_row_borders(table.rows[0], sz_top="12", sz_bottom="6")
        for i in range(1, n_rows):
            _set_row_borders(table.rows[i], sz_bottom="0")
        _set_row_borders(table.rows[n_rows], sz_bottom="12")
        self._add_note("Elaboración propia a partir de los datos procesados.")

    def export_sampling(self, result: dict):
        self._add_title("Cálculo del Tamaño de Muestra - Muestreo Aleatorio Simple (M.A.S.)", level=0)

        data = [
            ["Nivel de confianza", f"{result['confidence']}%"],
            ["Valor Z", f"{result['Z']:.3f}"],
            ["Probabilidad de éxito (p)", f"{result['p']}"],
            ["Probabilidad de fracaso (q)", f"{result['q']:.4f}"],
            ["Error admisible (e)", f"{result['e']}"],
        ]

        if result["N"] is not None:
            data.append(["Tamaño de la población (N)", str(result["N"])])
            data.append(["Muestra inicial (n₀)", str(result["n0"])])
            data.append(["Muestra corregida (nf)", str(result["nf"])])
        else:
            data.append(["Tamaño de muestra (n)", str(result["n_unknown"])])

        df = pd.DataFrame(data, columns=["Parámetro", "Valor"])
        self._apa_table_from_df(df, "Parámetros de entrada y resultados del cálculo muestral")

    def export_variable_classification(self, classification: dict):
        data = [["Variable", "Tipo"]]
        for var, tipo in classification.items():
            data.append([var, tipo.replace("_", " ").title()])
        df = pd.DataFrame(data[1:], columns=data[0])
        self._apa_table_from_df(df, "Clasificación automática de variables del dataset")

    def export_frequency_table(self, freq_result: dict, measures: dict = None):
        var_name = freq_result["var_name"]
        var_type = freq_result["var_type"]
        table = freq_result["table"]
        is_grouped = freq_result["is_grouped"]

        type_label = var_type.replace("_", " ").title()
        title = f"Distribución de frecuencias de {var_name} ({type_label})"

        if is_grouped:
            R = freq_result.get("R", 0)
            m = freq_result.get("m", 0)
            C = freq_result.get("C", 0)
            self._add_paragraph(
                f"Rango (R) = {R:.2f}  |  Intervalos (Sturges: m = 1 + 3.322·log(n)) = {m}  |  Amplitud (C) = {C:.2f}"
            )
            display_cols = ["Intervalo", "Xi", "fi", "Fi", "hi", "hi%", "Hi%"]
        else:
            display_cols = [table.columns[0], "fi", "Fi", "hi", "hi%", "Hi%"]

        display_df = table[display_cols].copy()
        for col in display_df.columns:
            if display_df[col].dtype in ["float64", "float32"]:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.4f}")

        self._apa_table_from_df(display_df, title)

    def export_measures(self, measures: dict, var_name: str):
        if measures is None:
            return

        self._add_heading_apa(f"Medidas Estadísticas - {var_name}", level=2)

        if measures.get("type") == "cualitativa":
            data = [
                ["Tamaño de muestra (n)", str(measures["n"])],
                ["Moda (Mo)", str(measures["mode"])],
            ]
            df = pd.DataFrame(data, columns=["Medida", "Valor"])
            self._apa_table_from_df(df, "Medidas para variable cualitativa")
            return

        central_data = [
            ["Media aritmética (X̄)", f"{measures['mean']:.4f}"],
            ["Mediana (Me)", f"{measures['median']:.4f}"],
            ["Moda (Mo)", f"{measures['mode']:.4f}"],
            ["Media geométrica (X̄g)", f"{measures['geometric_mean']:.4f}"],
            ["Media armónica (Mh)", f"{measures['harmonic_mean']:.4f}"],
        ]
        df_central = pd.DataFrame(central_data, columns=["Medida", "Valor"])
        self._apa_table_from_df(df_central, "Medidas de tendencia central")

        dispersion_data = [
            ["Rango", f"{measures['range']:.4f}"],
            ["Varianza muestral (S²)", f"{measures['variance']:.4f}"],
            ["Desviación estándar (S)", f"{measures['std_dev']:.4f}"],
            ["Coeficiente de variación (CV%)", f"{measures['cv']:.2f}%"],
        ]
        df_disp = pd.DataFrame(dispersion_data, columns=["Medida", "Valor"])
        self._apa_table_from_df(df_disp, "Medidas de dispersión")

        position_data = [
            ["Cuartil 1 (Q₁)", f"{measures['Q1']:.4f}"],
            ["Cuartil 2 (Q₂) = Mediana", f"{measures['Q2']:.4f}"],
            ["Cuartil 3 (Q₃)", f"{measures['Q3']:.4f}"],
            ["Decil 1 (D₁)", f"{measures['D1']:.4f}"],
            ["Decil 5 (D₅)", f"{measures['D5']:.4f}"],
            ["Decil 9 (D₉)", f"{measures['D9']:.4f}"],
            ["Percentil 10 (P₁₀)", f"{measures['P10']:.4f}"],
            ["Percentil 25 (P₂₅)", f"{measures['P25']:.4f}"],
            ["Percentil 50 (P₅₀)", f"{measures['P50']:.4f}"],
            ["Percentil 75 (P₇₅)", f"{measures['P75']:.4f}"],
            ["Percentil 90 (P₉₀)", f"{measures['P90']:.4f}"],
        ]
        df_pos = pd.DataFrame(position_data, columns=["Medida", "Valor"])
        self._apa_table_from_df(df_pos, "Medidas de posición (cuartiles, deciles y percentiles)")

        shape_data = [
            ["Coeficiente de asimetría (Sesgo)", f"{measures['skewness']:.4f}"],
            ["Coeficiente de curtosis (Exceso)", f"{measures['kurtosis']:.4f}"],
        ]
        df_shape = pd.DataFrame(shape_data, columns=["Medida", "Valor"])
        self._apa_table_from_df(df_shape, "Medidas de forma (asimetría y curtosis)")

    def export_chart(self, chart_bytes: io.BytesIO, title: str):
        self._format_figure_title(title)
        self.doc.add_picture(chart_bytes, width=Inches(5.5))
        last_paragraph = self.doc.paragraphs[-1]
        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def save(self, path: str):
        self.doc.save(path)

    def export_full_analysis(self, sampling_result: dict = None,
                             classification: dict = None,
                             all_analyses: list = None,
                             summary: pd.DataFrame = None,
                             interpretations: dict = None,
                             filepath: str = "Reporte_Estadistico_APA7.docx"):
        if sampling_result:
            self.export_sampling(sampling_result)
            self.doc.add_page_break()

        if classification:
            self._add_title("Análisis del Dataset", level=0)
            self.export_variable_classification(classification)

        if summary is not None and not summary.empty:
            self._add_heading_apa("Estadísticos Descriptivos Generales", level=2)
            display_df = summary.copy()
            for col in display_df.columns:
                if display_df[col].dtype in ["float64", "float32", "float"]:
                    display_df[col] = display_df[col].apply(lambda x: f"{x:.4f}")
            self._apa_table_from_df(display_df,
                "Resumen de estadísticos descriptivos para todas las variables cuantitativas")

        if interpretations:
            self._add_heading_apa("Interpretación de Resultados", level=2)
            for var, text in interpretations.items():
                p = self.doc.add_paragraph()
                run = p.add_run(f"{var}: ")
                run.bold = True
                run.font.name = APA_FONT
                run.font.size = APA_SIZE
                run2 = p.add_run(text)
                run2.font.name = APA_FONT
                run2.font.size = APA_SIZE
                p.paragraph_format.space_after = Pt(8)

        if all_analyses:
            for i, analysis in enumerate(all_analyses):
                freq_result = analysis.get("freq_result")
                measures = analysis.get("measures")
                charts = analysis.get("charts")

                if not freq_result:
                    continue

                var_name = freq_result.get("var_name", f"Variable {i+1}")
                if i > 0:
                    self.doc.add_page_break()
                self._add_heading_apa(f"Análisis detallado de: {var_name}", level=1)

                self.export_frequency_table(freq_result, measures)

                if measures:
                    self.export_measures(measures, var_name)

                if charts:
                    self._add_heading_apa("Gráficos Estadísticos", level=2)
                    for chart_key, chart_bytes in charts.items():
                        titles = {
                            "bar": f"Gráfico de barras de {var_name}",
                            "pie": f"Gráfico de sectores de {var_name}",
                            "bar_ogive": f"Gráfico de barras con ojiva de {var_name}",
                            "histogram": f"Histograma de frecuencias de {var_name}",
                        }
                        self.export_chart(chart_bytes, titles.get(chart_key, f"Gráfico de {var_name}"))
                        self._add_note()

        self.save(filepath)
        return filepath
