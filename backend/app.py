from flask_cors import CORS
from flask import Flask, jsonify
import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    CORS(app)

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


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
