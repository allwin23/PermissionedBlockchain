import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Base paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Fabric related configuration
    FABRIC_NETWORK_PROFILE = os.environ.get(
        'FABRIC_NETWORK_PROFILE',
        os.path.join(BASE_DIR, 'connection-profile.yaml')
    )
    CHANNEL_NAME = os.environ.get('FABRIC_CHANNEL_NAME', 'evidencechannel')
    CHAINCODE_NAME = os.environ.get('FABRIC_CHAINCODE_NAME', 'evidence')

    # Fabric Identity (for cloud deployment, set these env vars in Render)
    FABRIC_USER_CERT_PATH = os.environ.get('FABRIC_USER_CERT_PATH', '')
    FABRIC_USER_KEY_PATH = os.environ.get('FABRIC_USER_KEY_PATH', '')

    # IPFS
    IPFS_HOST = os.environ.get('IPFS_HOST', '/ip4/127.0.0.1/tcp/5001/http')

    # Wallet directory path (legacy - not used in cloud mode)
    WALLET_DIR = os.path.join(BASE_DIR, 'wallets')

    # CORS origins
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
