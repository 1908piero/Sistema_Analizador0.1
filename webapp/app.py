import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))

import matplotlib
matplotlib.use('Agg')

from flask import Flask
try:
    from webapp.routes import main_bp
except ImportError:
    from routes import main_bp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'analizador-encuestas-secret-key-2024')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.register_blueprint(main_bp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
