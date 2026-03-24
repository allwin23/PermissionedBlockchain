import os
from config import Config
from hfc.fabric.user import create_user
from hfc.util.keyvaluestore import FileKeyValueStore


class Wallet:
    def __init__(self, wallet_dir=Config.WALLET_DIR):
        self.wallet_dir = wallet_dir

    def _read_file(self, file_path):
        with open(file_path, 'r') as f:
            return f.read()

    def load_identity(self, username, org_name="org1.example.com", msp_id="Org1MSP", client=None):
        """
        Loads the X.509 certificate and private key from the user's directory
        and returns a fabric-sdk-py User object.
        """
        user_path = os.path.join(self.wallet_dir, username)

        if not os.path.exists(user_path):
            return None

        # Look in msp/signcerts/ for the public cert
        signcerts_path = os.path.join(user_path, 'msp', 'signcerts')
        cert_file = None
        if os.path.exists(signcerts_path):
            certs = os.listdir(signcerts_path)
            if certs:
                cert_file = os.path.join(signcerts_path, certs[0])

        # Look in msp/keystore/ for the private key
        keystore_path = os.path.join(user_path, 'msp', 'keystore')
        key_file = None
        if os.path.exists(keystore_path):
            keys = [k for k in os.listdir(keystore_path) if k.endswith('_sk')]
            if keys:
                key_file = os.path.join(keystore_path, keys[0])

        if not cert_file or not key_file:
            return None

        # Create user object
        state_store = FileKeyValueStore('/tmp/fabric-client-kv-store/')
        user = create_user(
            name=username,
            org=org_name,
            state_store=state_store,
            msp_id=msp_id,
            cert_path=cert_file,
            key_path=key_file
        )
        if client:
            user.cryptoSuite = client.crypto_suite
        return user


wallet = Wallet()
