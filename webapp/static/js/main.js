function showToast(msg, type) {
    type = type || 'success';
    var el = document.createElement('div');
    el.className = 'app-toast ' + type;
    el.textContent = msg;
    document.body.appendChild(el);
    requestAnimationFrame(function() { el.classList.add('show'); });
    setTimeout(function() {
        el.classList.remove('show');
        setTimeout(function() { el.remove(); }, 400);
    }, 3000);
}

$(function () {
    // File upload drag & drop
    var dropZone = $('#drop-zone');
    var fileInput = $('#file-input');

    if (dropZone.length) {
        dropZone.on('dragover', function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropZone.addClass('drag-over');
        });

        dropZone.on('dragleave', function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropZone.removeClass('drag-over');
        });

        dropZone.on('drop', function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropZone.removeClass('drag-over');
            var files = e.originalEvent.dataTransfer.files;
            if (files.length) {
                fileInput[0].files = files;
                submitForm();
            }
        });

        fileInput.on('change', function () {
            if (this.files.length) submitForm();
        });
    }

    function submitForm() {
        $('#upload-status').show();
        $('#upload-form')[0].submit();
    }

    // Variable type change
    $(document).on('change', '.var-type-select', function () {
        var varName = $(this).data('var');
        var newType = $(this).val();
        $.ajax({
            url: '/api/reclassify',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ var_name: varName, new_type: newType }),
            success: function (resp) {
                if (resp.success && $('.variable-item.active').data('var') === varName) {
                    loadVariable(varName);
                }
            }
        });
    });

    // Variable click
    var variableItems = $('.variable-item');
    if (variableItems.length) {
        variableItems.on('click', function (e) {
            if ($(e.target).is('.var-type-select')) return;
            var varName = $(this).data('var');
            variableItems.removeClass('active');
            $(this).addClass('active');
            loadVariable(varName);
        });
    }

    function loadVariable(varName) {
        var content = $('#analysis-content');
        content.html('<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2 text-muted">Analizando variable...</p></div>');

        $.getJSON('/api/analyze/' + encodeURIComponent(varName))
            .done(function (resp) {
                if (!resp.success) {
                    content.html('<div class="alert alert-danger">' + resp.error + '</div>');
                    return;
                }
                renderAnalysis(content, resp.data);
            })
            .fail(function () {
                content.html('<div class="alert alert-danger">Error al comunicarse con el servidor.</div>');
            });
    }

    function renderAnalysis(container, data) {
        var html = '<div class="analysis-results">';

        // Variable header
        html += '<div class="d-flex align-items-center justify-content-between mb-3">';
        html += '<h4 class="mb-0"><i class="fas fa-chart-bar me-2 text-primary"></i>' + escHtml(data.var_name) + '</h4>';
        html += '<span class="var-badge badge-' + typeToClass(data.var_type) + '">' + typeToLabel(data.var_type) + '</span>';
        html += '</div>';

        // N info
        html += '<p class="text-muted small">n = ' + data.freq_table.n + ' observaciones' +
                (data.n_null > 0 ? ' (' + data.n_null + ' valores perdidos)' : '') + '</p>';

        if (data.freq_table.is_grouped && data.freq_table.R !== undefined) {
            html += '<div class="alert alert-info small py-2 mb-3">';
            html += 'Rango (R) = ' + data.freq_table.R + ' | Intervalos (Sturges: m) = ' + data.freq_table.m + ' | Amplitud (C) = ' + data.freq_table.C;
            html += '</div>';
        }

        // Frequency table
        html += '<div class="results-section">';
        html += '<h5><i class="fas fa-table me-2"></i>Tabla de Frecuencias</h5>';
        html += '<div class="table-responsive">';
        html += '<table class="table-custom">';
        html += '<thead><tr>';
        data.freq_table.columns.forEach(function (col) {
            html += '<th>' + escHtml(col) + '</th>';
        });
        html += '</tr></thead><tbody>';
        data.freq_table.rows.forEach(function (row) {
            html += '<tr>';
            row.forEach(function (val) {
                html += '<td>' + escHtml(formatVal(val)) + '</td>';
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        html += '</div></div>';

        // Measures
        if (data.measures) {
            html += '<div class="results-section">';
            html += '<h5><i class="fas fa-calculator me-2"></i>Medidas Estadísticas</h5>';

            if (data.measures.type === 'cualitativa') {
                html += '<div class="measures-grid">';
                html += '<div class="measure-item"><span class="measure-label">n</span><span class="measure-value">' + data.measures.n + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">Moda (Mo)</span><span class="measure-value">' + escHtml(String(data.measures.mode)) + '</span></div>';
                html += '</div>';
            } else {
                // Central tendency
                html += '<h6 class="text-success mb-2">Tendencia Central</h6>';
                html += '<div class="measures-grid">';
                html += '<div class="measure-item"><span class="measure-label">Media (X̄)</span><span class="measure-value">' + fmt(data.measures.mean) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">Mediana (Me)</span><span class="measure-value">' + fmt(data.measures.median) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">Moda (Mo)</span><span class="measure-value">' + fmt(data.measures.mode) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">Media Geom. (X̄g)</span><span class="measure-value">' + fmt(data.measures.geometric_mean) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">Media Arm. (Mh)</span><span class="measure-value">' + fmt(data.measures.harmonic_mean) + '</span></div>';
                html += '</div>';

                // Dispersion
                html += '<h6 class="text-info mb-2 mt-3">Dispersión</h6>';
                html += '<div class="measures-grid">';
                html += '<div class="measure-item"><span class="measure-label">Rango</span><span class="measure-value">' + fmt(data.measures.range) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">Varianza (S²)</span><span class="measure-value">' + fmt(data.measures.variance) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">D.E. (S)</span><span class="measure-value">' + fmt(data.measures.std_dev) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">CV%</span><span class="measure-value">' + fmt(data.measures.cv) + '%</span></div>';
                html += '</div>';

                // Position
                html += '<h6 class="text-warning mb-2 mt-3">Posición</h6>';
                html += '<div class="measures-grid">';
                html += '<div class="measure-item"><span class="measure-label">Q₁</span><span class="measure-value">' + fmt(data.measures.Q1) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">Q₂ (Mediana)</span><span class="measure-value">' + fmt(data.measures.Q2) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">Q₃</span><span class="measure-value">' + fmt(data.measures.Q3) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">D₁</span><span class="measure-value">' + fmt(data.measures.D1) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">D₅</span><span class="measure-value">' + fmt(data.measures.D5) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">D₉</span><span class="measure-value">' + fmt(data.measures.D9) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">P₁₀</span><span class="measure-value">' + fmt(data.measures.P10) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">P₂₅</span><span class="measure-value">' + fmt(data.measures.P25) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">P₅₀</span><span class="measure-value">' + fmt(data.measures.P50) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">P₇₅</span><span class="measure-value">' + fmt(data.measures.P75) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">P₉₀</span><span class="measure-value">' + fmt(data.measures.P90) + '</span></div>';
                html += '</div>';

                // Shape
                html += '<h6 class="text-secondary mb-2 mt-3">Forma</h6>';
                html += '<div class="measures-grid">';
                html += '<div class="measure-item"><span class="measure-label">Asimetría (Sesgo)</span><span class="measure-value">' + fmt(data.measures.skewness) + '</span></div>';
                html += '<div class="measure-item"><span class="measure-label">Curtosis (Exceso)</span><span class="measure-value">' + fmt(data.measures.kurtosis) + '</span></div>';
                html += '</div>';
            }

            html += '</div>';

            // Interpretation
            if (data.interpretation) {
                html += '<div class="results-section">';
                html += '<h5><i class="fas fa-align-left me-2"></i>Interpretación</h5>';
                html += '<p class="interpretation-text">' + escHtml(data.interpretation) + '</p>';
                html += '</div>';
            }
        }

        // Charts
        if (data.charts) {
            html += '<div class="results-section">';
            html += '<h5><i class="fas fa-chart-pie me-2"></i>Gráficos Estadísticos</h5>';
            html += '<div class="row">';
            var chartLabels = {
                bar: 'Gráfico de Barras',
                pie: 'Gráfico de Sectores (Pastel)',
                bar_ogive: 'Barras con Ojiva',
                histogram: 'Histograma de Frecuencias',
                freq_poly_ogive: 'Polígono de Frecuencias y Ojiva',
                boxplot: 'Diagrama de Caja y Bigotes'
            };
            Object.keys(data.charts).forEach(function (key) {
                html += '<div class="col-md-6">';
                html += '<div class="chart-container">';
                html += '<h6>' + (chartLabels[key] || key) + '</h6>';
                html += '<img src="' + data.charts[key] + '" alt="' + key + '" class="img-fluid">';
                html += '</div></div>';
            });
            html += '</div></div>';
        }

        html += '</div>';
        container.html(html);
    }

    // Summary button
    $('#summary-btn').on('click', function () {
        var modal = new bootstrap.Modal(document.getElementById('summary-modal'));
        modal.show();

        $.getJSON('/api/summary')
            .done(function (resp) {
                if (!resp.success) {
                    $('#summary-body').html('<div class="alert alert-warning">' + resp.error + '</div>');
                    return;
                }
                var html = '<div class="table-responsive"><table class="table-custom"><thead><tr>';
                resp.data.columns.forEach(function (col) {
                    html += '<th>' + escHtml(col) + '</th>';
                });
                html += '</tr></thead><tbody>';
                resp.data.rows.forEach(function (row) {
                    html += '<tr>';
                    row.forEach(function (val) {
                        html += '<td>' + escHtml(formatVal(val)) + '</td>';
                    });
                    html += '</tr>';
                });
                html += '</tbody></table></div>';
                $('#summary-body').html(html);
            })
            .fail(function () {
                $('#summary-body').html('<div class="alert alert-danger">Error al cargar resumen.</div>');
            });
    });

    // Export spinner
    $('#export-form').on('submit', function () {
        $('#export-btn').prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>Exportando...');
    });

    // Utility functions
    function escHtml(str) {
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function fmt(val) {
        if (typeof val === 'number') return val.toFixed(2);
        return String(val);
    }

    function formatVal(val) {
        if (val === null || val === undefined) return '-';
        if (typeof val === 'number') return val.toFixed(2);
        return String(val);
    }

    function typeToClass(type) {
        var map = {
            cualitativa_nominal: 'badge-qual-nom',
            cualitativa_ordinal: 'badge-qual-ord',
            cuantitativa_discreta: 'badge-quant-disc',
            cuantitativa_continua: 'badge-quant-cont'
        };
        return map[type] || '';
    }

    function typeToLabel(type) {
        var map = {
            cualitativa_nominal: 'Cual. Nominal',
            cualitativa_ordinal: 'Cual. Ordinal',
            cuantitativa_discreta: 'Cuan. Discreta',
            cuantitativa_continua: 'Cuan. Continua'
        };
        return map[type] || type;
    }
});
