import ipfshttpclient
import os
import shutil


class IPFSClient:
    def __init__(self, host='/ip4/127.0.0.1/tcp/5001/http'):
        try:
            self.client = ipfshttpclient.connect(host)
        except Exception:
            # When daemon is not running this will fail
            self.client = None

    def upload_file(self, file_path):
        """Adds file to IPFS, returns CID."""
        if not self.client:
            raise Exception("IPFS Client not connected")

        res = self.client.add(file_path)
        return res['Hash']

    def download_file(self, cid, output_path):
        """Retrieves file from IPFS by CID."""
        if not self.client:
            raise Exception("IPFS Client not connected")

        # ipfs get creates a file/folder in current directory with the name of the CID.
        # We need to change to the target dir, download, and optionally rename.
        current_dir = os.getcwd()
        target_dir = os.path.dirname(output_path) or '.'

        try:
            os.chdir(target_dir)
            self.client.get(cid)
            shutil.move(cid, output_path)
        finally:
            os.chdir(current_dir)


ipfs_client = IPFSClient()
