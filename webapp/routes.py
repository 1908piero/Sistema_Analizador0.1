import os
import io
import json
import base64
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, send_file

from model.statistics import VariableClassifier, FrequencyAnalyzer, MeasuresCalculator, DatasetSummary
from model.charts import ChartGenerator
from model.sampling import calculate_sample_size
from model.anova import ANOVAOneWay, ANOVATwoWay
from model.i18n import _, set_language, current_lang
from export.docx_exporter import APA7Exporter

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html', lang=current_lang())

@main_bp.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return render_template('error.html', message='No se envió ningún archivo.')

    file = request.files['file']
    if file.filename == '':
        return render_template('error.html', message='Nombre de archivo vacío.')

    ext = os.path.splitext(file.filename)[1].lower()
    try:
        if ext == '.csv':
            df = pd.read_csv(io.StringIO(file.stream.read().decode('utf-8')))
        elif ext in ('.xls', '.xlsx'):
            df = pd.read_excel(file, engine='openpyxl')
        else:
            return render_template('error.html', message='Formato no soportado. Use CSV o Excel.')
    except Exception as e:
        return render_template('error.html', message=f'Error al leer archivo: {str(e)}')

    if df.empty:
        return render_template('error.html', message='El archivo está vacío.')

    df.columns = df.columns.str.strip().str.replace(r'\s+', '_', regex=True)
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip().replace('nan', pd.NA)
    classification = VariableClassifier.classify(df)
    session['df_json'] = df.to_json(orient='split')
    session['classification'] = classification
    session['filename'] = file.filename
    session['n_rows'] = len(df)
    session['n_cols'] = len(df.columns)

    return redirect(url_for('main.analysis'))


@main_bp.route('/analysis')
def analysis():
    if 'df_json' not in session:
        return redirect(url_for('main.index'))

    df = pd.read_json(io.StringIO(session['df_json']), orient='split')
    classification = session['classification']
    filename = session.get('filename', 'Dataset')
    n_rows = session.get('n_rows', len(df))
    n_cols = session.get('n_cols', len(df.columns))

    has_empty = bool(df.isna().any().any())
    completeness = 100 - round(df.isna().sum().sum() / (n_rows * n_cols) * 100, 1)

    return render_template('analysis.html',
                           lang=current_lang(),
                           filename=filename,
                           n_rows=n_rows,
                           n_cols=n_cols,
                           has_empty=has_empty,
                           completeness=completeness,
                           columns=list(df.columns),
                           classification=classification)


@main_bp.route('/api/analyze/<var_name>')
def api_analyze(var_name):
    if 'df_json' not in session:
        return jsonify({'success': False, 'error': 'No hay datos cargados.'})

    df = pd.read_json(io.StringIO(session['df_json']), orient='split')
    classification = session['classification']

    if var_name not in df.columns:
        return jsonify({'success': False, 'error': f'Variable "{var_name}" no encontrada.'})

    var_type = classification.get(var_name, 'desconocido')
    if var_type == 'desconocido':
        return jsonify({'success': False, 'error': f'Tipo desconocido para "{var_name}".'})

    data = df[var_name]

    freq_result = FrequencyAnalyzer.compute(data, var_type, var_name)
    if freq_result is None:
        return jsonify({'success': False, 'error': f'No se pudo calcular distribución para "{var_name}".'})

    measures = MeasuresCalculator.compute(freq_result)
    charts = ChartGenerator.generate_all_charts(freq_result, var_name)

    interpretation = DatasetSummary.generate_interpretation(measures, var_name)

    result = {
        'success': True,
        'data': {
            'var_name': var_name,
            'var_type': var_type,
            'n_null': int(df[var_name].isna().sum()),
            'freq_table': _serialize_freq(freq_result),
            'measures': _serialize_measures(measures),
            'interpretation': interpretation,
            'charts': _serialize_charts(charts),
        }
    }
    return jsonify(result)


@main_bp.route('/api/summary')
def api_summary():
    if 'df_json' not in session:
        return jsonify({'success': False, 'error': 'No hay datos cargados.'})

    df = pd.read_json(io.StringIO(session['df_json']), orient='split')
    classification = session['classification']

    summary_df = DatasetSummary.summary_statistics(df, classification)
    if summary_df is None:
        return jsonify({'success': False, 'error': 'No hay variables cuantitativas para resumir.'})

    return jsonify({
        'success': True,
        'data': {
            'columns': list(summary_df.columns),
            'rows': summary_df.values.tolist(),
        }
    })


@main_bp.route('/sampling', methods=['GET', 'POST'])
def sampling():
    result = None
    if request.method == 'POST':
        try:
            confidence = int(request.form.get('confidence', 95))
            p = float(request.form.get('p', 0.5))
            e = float(request.form.get('e', 0.05))
            N_str = request.form.get('N', '').strip()
            N = int(N_str) if N_str else None
            result = calculate_sample_size(confidence, p, e, N)
        except ValueError as e:
            result = {'error': str(e)}
        except Exception as e:
            result = {'error': f'Error inesperado: {str(e)}'}

    return render_template('sampling.html', lang=current_lang(), result=result)


def _parse_grupos(form, k):
    grupos = []
    for i in range(k):
        raw = form.get(f'grupo_{i}', '')
        valores = [float(x.strip()) for x in raw.split(',') if x.strip()]
        if valores:
            grupos.append(valores)
    return grupos


@main_bp.route('/anova1', methods=['GET', 'POST'])
def anova1():
    k = None
    n = None
    alpha = None
    grupos = None
    grupos_serialized = None
    result = None
    if request.method == 'POST':
        try:
            k = int(request.form.get('k', 3))
            n = int(request.form.get('n', 5))
            alpha = float(request.form.get('alpha', 0.05))
            grupos = _parse_grupos(request.form, k)
            if len(grupos) < 2:
                return render_template('anova1.html', lang=current_lang(), error="Ingrese al menos 2 grupos con datos.",
                                       k=k, n=n, alpha=alpha, grupos=grupos, enumerate=enumerate, int=int)
            anova = ANOVAOneWay(grupos, alpha)
            result = anova.compute()
            import json as _json
            grupos_serialized = _json.dumps(grupos)
        except Exception as e:
            return render_template('anova1.html', lang=current_lang(), error=str(e),
                                   k=k, n=n, alpha=alpha, grupos=grupos, enumerate=enumerate, int=int)
    return render_template('anova1.html', lang=current_lang(), result=result,
                           k=k, n=n, alpha=alpha, grupos=grupos,
                           grupos_serialized=grupos_serialized,
                           enumerate=enumerate, int=int)


@main_bp.route('/anova1/tukey')
def anova1_tukey():
    try:
        import json as _json
        k = int(request.args.get('k', 3))
        alpha = float(request.args.get('alpha', 0.05))
        grupos_raw = request.args.get('grupos', '[]')
        grupos = _json.loads(grupos_raw)
        anova = ANOVAOneWay(grupos, alpha)
        anova.compute()
        comparisons = anova.tukey_hsd()
        return render_template('tukey.html', lang=current_lang(), comparisons=comparisons, int=int)
    except Exception as e:
        return str(e)


@main_bp.route('/anova1/pdf')
def anova1_pdf():
    try:
        import json as _json
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        k = int(request.args.get('k', 3))
        alpha = float(request.args.get('alpha', 0.05))
        grupos_raw = request.args.get('grupos', '[]')
        grupos = _json.loads(grupos_raw)
        anova = ANOVAOneWay(grupos, alpha)
        result = anova.compute()

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Estadística ANOVA RL", styles['Title']))
        elements.append(Paragraph("Análisis de Varianza Un Factor", styles['Heading2']))
        elements.append(Spacer(1, 12))

        anova_data = [[r['FV'], f"{r['SC']:.4f}", str(int(r['GL'])) if r['GL'] else '-',
                       f"{r['MC']:.4f}" if r['MC'] else '-',
                       f"{r['F']:.4f}" if r['F'] else '-',
                       f"{r['p-value']:.4f}" if r['p-value'] else '-']
                      for _, r in result['table'].iterrows()]
        anova_data.insert(0, ['FV', 'SC', 'GL', 'MC', 'F', 'p-value'])

        t = Table(anova_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(result['conclusion'], styles['Normal']))
        elements.append(Spacer(1, 24))
        elements.append(Paragraph("Gracias por utilizar la aplicación. Cualquier sugerencia, por favor comentarla.", styles['Normal']))

        doc.build(elements)
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name='ANOVA_UnFactor.pdf')
    except Exception as e:
        return str(e)


@main_bp.route('/anova2', methods=['GET', 'POST'])
def anova2():
    a = None
    b = None
    n = None
    alpha = None
    celdas = None
    datos_serialized = None
    result = None
    action = None
    if request.method == 'POST':
        try:
            a = int(request.form.get('a', 2))
            b = int(request.form.get('b', 2))
            n = int(request.form.get('n', 3))
            alpha = float(request.form.get('alpha', 0.05))
            action = request.form.get('action', '')

            if action == 'generate':
                celdas = []
                for i in range(a):
                    for j in range(b):
                        key = f'celda_{i}_{j}'
                        existing = request.form.get(key, '')
                        celdas.append({
                            'i': i, 'j': j,
                            'label': f'F1-{i+1} × F2-{j+1}',
                            'valor': existing,
                        })
                return render_template('anova2.html', lang=current_lang(),
                                       a=a, b=b, n=n, alpha=alpha, celdas=celdas, int=int)

            rows = []
            for i in range(a):
                for j in range(b):
                    raw = request.form.get(f'celda_{i}_{j}', '')
                    valores = [float(x.strip()) for x in raw.split(',') if x.strip()]
                    for v in valores:
                        rows.append({'Factor1': f'F1-{i+1}', 'Factor2': f'F2-{j+1}', 'Valor': v})
            df = pd.DataFrame(rows)
            if len(df) < a * b:
                return render_template('anova2.html', lang=current_lang(),
                                       error="Ingrese datos en todas las casillas.",
                                       a=a, b=b, n=n, alpha=alpha, int=int)
            anova = ANOVATwoWay(df, alpha)
            result = anova.compute()
            import json as _json
            datos_serialized = _json.dumps(rows)
        except Exception as e:
            return render_template('anova2.html', lang=current_lang(), error=str(e),
                                   a=a, b=b, n=n, alpha=alpha, int=int)
    return render_template('anova2.html', lang=current_lang(), result=result,
                           a=a, b=b, n=n, alpha=alpha, celdas=celdas,
                           datos_serialized=datos_serialized, int=int)


@main_bp.route('/anova2/pdf')
def anova2_pdf():
    try:
        import json as _json
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        datos_raw = request.args.get('datos', '[]')
        alpha = float(request.args.get('alpha', 0.05))
        rows = _json.loads(datos_raw)
        df = pd.DataFrame(rows)
        anova = ANOVATwoWay(df, alpha)
        result = anova.compute()

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Estadística ANOVA RL", styles['Title']))
        elements.append(Paragraph("Análisis de Varianza Dos Factores", styles['Heading2']))
        elements.append(Spacer(1, 12))

        anova_data = [[r['FV'], f"{r['SC']:.4f}", str(int(r['GL'])) if r['GL'] else '-',
                       f"{r['MC']:.4f}" if r['MC'] else '-',
                       f"{r['F']:.4f}" if r['F'] else '-',
                       f"{r['p-value']:.4f}" if r['p-value'] else '-']
                      for _, r in result['table'].iterrows()]
        anova_data.insert(0, ['FV', 'SC', 'GL', 'MC', 'F', 'p-value'])

        t = Table(anova_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))
        for key, conclusion in result['conclusions'].items():
            elements.append(Paragraph(conclusion, styles['Normal']))
        elements.append(Spacer(1, 24))
        elements.append(Paragraph("Gracias por utilizar la aplicación. Cualquier sugerencia, por favor comentarla.", styles['Normal']))

        doc.build(elements)
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name='ANOVA_DosFactores.pdf')
    except Exception as e:
        return str(e)


@main_bp.route('/export_apa', methods=['POST'])
def export_apa():
    if 'df_json' not in session:
        return jsonify({'success': False, 'error': 'No hay datos cargados.'})

    df = pd.read_json(io.StringIO(session['df_json']), orient='split')
    classification = session['classification']

    all_analyses = []
    for col in df.columns:
        var_type = classification.get(col, 'desconocido')
        if var_type == 'desconocido':
            continue
        data = df[col]
        freq_result = FrequencyAnalyzer.compute(data, var_type, col)
        if freq_result is None:
            continue
        measures = MeasuresCalculator.compute(freq_result)
        charts = ChartGenerator.generate_all_charts(freq_result, col)
        all_analyses.append({
            'freq_result': freq_result,
            'measures': measures,
            'charts': charts,
        })

    summary = DatasetSummary.summary_statistics(df, classification)
    interpretations = {}
    for col in df.columns:
        data = df[col]
        var_type = classification.get(col, 'desconocido')
        if var_type == 'desconocido':
            continue
        freq_result = FrequencyAnalyzer.compute(data, var_type, col)
        if freq_result:
            measures = MeasuresCalculator.compute(freq_result)
            interpretations[col] = DatasetSummary.generate_interpretation(measures, col)

    exporter = APA7Exporter()
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'Reporte_Estadistico_APA7.docx')
    exporter.export_full_analysis(
        classification=classification,
        all_analyses=all_analyses,
        summary=summary,
        interpretations=interpretations,
        filepath=output_path,
    )

    return send_file(output_path, as_attachment=True,
                     download_name='Reporte_Estadistico_APA7.docx')


@main_bp.route('/api/reclassify', methods=['POST'])
def api_reclassify():
    if 'df_json' not in session:
        return jsonify({'success': False, 'error': 'No hay datos cargados.'})
    data = request.get_json()
    var_name = data.get('var_name')
    new_type = data.get('new_type')
    if not var_name or new_type not in ('cualitativa_nominal', 'cualitativa_ordinal', 'cuantitativa_discreta', 'cuantitativa_continua'):
        return jsonify({'success': False, 'error': 'Parámetros inválidos.'})
    classification = session.get('classification', {})
    classification[var_name] = new_type
    session['classification'] = classification
    return jsonify({'success': True})

@main_bp.route('/about')
def about():
    return render_template('about.html', lang=current_lang())

@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html', lang=current_lang())

@main_bp.route('/rate')
def rate():
    return render_template('rate.html', lang=current_lang())

@main_bp.route('/credits')
def credits():
    return redirect(url_for('main.about'))

@main_bp.route('/lang/<lang>')
def set_lang(lang):
    if lang in ('es', 'en', 'pt'):
        set_language(lang)
        session['lang'] = lang
    return redirect(request.referrer or url_for('main.index'))


def _serialize_freq(freq_result):
    if freq_result is None:
        return None
    table = freq_result['table']
    cols = list(table.columns)
    rows = table.values.tolist()
    for r in rows:
        for i, v in enumerate(r):
            if isinstance(v, float):
                r[i] = round(v, 2)
    return {
        'var_name': freq_result['var_name'],
        'var_type': freq_result['var_type'],
        'n': freq_result['n'],
        'is_grouped': freq_result['is_grouped'],
        'R': freq_result.get('R'),
        'm': freq_result.get('m'),
        'C': freq_result.get('C'),
        'min': freq_result.get('min'),
        'max': freq_result.get('max'),
        'unique_values': freq_result.get('unique_values'),
        'columns': cols,
        'rows': rows,
    }


def _serialize_measures(measures):
    if measures is None:
        return None
    return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in measures.items()}


def _serialize_charts(charts):
    result = {}
    for key, buf in charts.items():
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        result[key] = f'data:image/png;base64,{b64}'
    return result


try:
    from flask import current_app as app
except:
    pass
