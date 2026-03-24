import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

from flask_cors import CORS
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    CORS(app, origins=app.config.get('CORS_ORIGINS', '*'), supports_credentials=True)

    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'ok',
            'message': 'Flask server is running'
        }), 200

    from api.evidence import evidence_bp
    from api.auth import auth_bp

    app.register_blueprint(evidence_bp, url_prefix='/api/evidence')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app


# Expose application object for gunicorn: gunicorn "app:create_app()"
application = create_app()

if __name__ == '__main__':
    debug = os.environ.get('FLASK_ENV') != 'production'
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, debug=debug)
