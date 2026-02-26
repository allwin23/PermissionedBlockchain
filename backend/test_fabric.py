import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import asyncio
from fabric_interface.client import fabric_client
from fabric_interface.wallet import wallet
import sys

def main():
    print("Testing Query EVI-999...")
    admin = wallet.load_identity('alice', client=fabric_client.client)
    try:
        response = fabric_client.query_transaction(
            requestor=admin,
            fcn='QueryEvidence',
            args=['EVI-999']
        )
        print("Query Response:", response)
    except Exception as e:
        print("Query Error:", str(e))

if __name__ == "__main__":
    main()
