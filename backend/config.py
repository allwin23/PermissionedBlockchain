import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Base paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Fabric related configuration
    FABRIC_NETWORK_PROFILE = os.path.join(BASE_DIR, 'connection-profile.yaml')
    CHANNEL_NAME = 'evidencechannel'
    CHAINCODE_NAME = 'evidence'
    
    # Wallet directory path
    WALLET_DIR = os.path.join(BASE_DIR, 'wallets')
