import yaml
import json
import os
import asyncio
import threading
import concurrent.futures
from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.orderer import Orderer
from hfc.util.crypto.crypto import ecies
from config import Config

def _start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

_fabric_client_loop = asyncio.new_event_loop()
_fabric_client_thread = threading.Thread(
    target=_start_background_loop, args=(_fabric_client_loop,), daemon=True
)
_fabric_client_thread.start()

class FabricClientWrapper:
    def __init__(self, profile_path=Config.FABRIC_NETWORK_PROFILE):
        if profile_path.endswith('.yaml'):
            with open(profile_path, 'r') as f:
                self.profile = yaml.safe_load(f)
                
            # fabric-sdk-py has bugs where it expects 'path' instead of 'pem' for tlsCACerts.
            # Convert raw PEM texts into temporary files before converting profile to JSON.
            def _convert_pem_to_path(nodes, prefix):
                for name, info in nodes.items():
                    if 'tlsCACerts' in info and 'pem' in info['tlsCACerts']:
                        pem_data = info['tlsCACerts']['pem']
                        tmp_cert = f"/tmp/{prefix}_{name}_tls.pem"
                        with open(tmp_cert, 'w') as tf:
                            tf.write(pem_data)
                        info['tlsCACerts'] = {'path': tmp_cert}
                        
            if 'peers' in self.profile:
                _convert_pem_to_path(self.profile['peers'], 'peer')
            if 'orderers' in self.profile:
                _convert_pem_to_path(self.profile['orderers'], 'orderer')
            if 'certificateAuthorities' in self.profile:
                for name, info in self.profile['certificateAuthorities'].items():
                    if 'tlsCACerts' in info and 'pem' in info['tlsCACerts']:
                        # The CA might have a list of PEMs
                        pem_data = info['tlsCACerts']['pem']
                        if isinstance(pem_data, list) and len(pem_data) > 0:
                            pem_data = pem_data[0]
                        tmp_cert = f"/tmp/ca_{name}_tls.pem"
                        with open(tmp_cert, 'w') as tf:
                            tf.write(pem_data)
                        info['tlsCACerts'] = {'path': tmp_cert, 'pem': pem_data} # keeping pem for CA

            temp_json = '/tmp/connection-profile.json'
            with open(temp_json, 'w') as f:
                json.dump(self.profile, f)
            self.client = Client(net_profile=temp_json)
        else:
            self.client = Client(net_profile=profile_path)
            
        # Re-create peers & orderers to explicitly pass mTLS client certs since Python SDK ignores it in profile
        client_key_path = None
        client_cert_path = None
        user_path = os.path.join(Config.WALLET_DIR, 'alice')
        import glob
        if os.path.exists(user_path):
            keystore = os.path.join(user_path, 'msp', 'keystore')
            signcerts = os.path.join(user_path, 'msp', 'signcerts')
            keys = glob.glob(os.path.join(keystore, '*_sk'))
            certs = glob.glob(os.path.join(signcerts, '*'))
            if keys and certs:
                client_key_path = keys[0]
                client_cert_path = certs[0]
                
        if client_key_path and client_cert_path:
            for name, peer in list(self.client._peers.items()):
                opts = tuple((k, v) for k, v in peer._grpc_options.items()) if getattr(peer, '_grpc_options', None) else None
                ep = peer._endpoint.replace('grpcs://', '').replace('grpc://', '')
                new_peer = Peer(
                    name=name,
                    endpoint=ep,
                    tls_ca_cert_file=peer._tls_ca_certs_path,
                    client_key_file=client_key_path,
                    client_cert_file=client_cert_path,
                    opts=opts
                )
                self.client._peers[name] = new_peer
                
            for name, orderer in list(self.client._orderers.items()):
                opts = tuple((k, v) for k, v in orderer._grpc_options.items()) if getattr(orderer, '_grpc_options', None) else None
                ep = orderer._endpoint.replace('grpcs://', '').replace('grpc://', '')
                new_orderer = Orderer(
                    name=name,
                    endpoint=ep,
                    tls_ca_cert_file=orderer._tls_ca_certs_path,
                    client_key_file=client_key_path,
                    client_cert_file=client_cert_path,
                    opts=opts
                )
                self.client._orderers[name] = new_orderer

        if not getattr(self.client, 'crypto_suite', None) or not self.client.crypto_suite:
            self.client._crypto_suite = ecies()
            
        self.channel_name = Config.CHANNEL_NAME
        if not self.client.get_channel(self.channel_name):
            self.client.new_channel(self.channel_name)
            
        self.chaincode_name = Config.CHAINCODE_NAME
        self.default_peers = ['peer0.org1.example.com'] 

class FabricClient:
    def __init__(self):
        # Initialize the wrapper ON the background loop
        future = asyncio.run_coroutine_threadsafe(self._init_wrapper(), _fabric_client_loop)
        self.wrapper = future.result()

    async def _init_wrapper(self):
        return FabricClientWrapper()

    @property
    def client(self):
        return self.wrapper.client

    def get_user_identity(self, org_name, user_name):
        return self.wrapper.client.get_user(org_name, user_name)

    def submit_transaction(self, requestor, fcn, args):
        if not isinstance(args, list):
            args = [args]
        
        coro = self.wrapper.client.chaincode_invoke(
            requestor=requestor,
            channel_name=self.wrapper.channel_name,
            peers=self.wrapper.default_peers,
            args=args,
            cc_name=self.wrapper.chaincode_name,
            fcn=fcn,
            wait_for_event=True
        )
        future = asyncio.run_coroutine_threadsafe(coro, _fabric_client_loop)
        return future.result()
    
    def query_transaction(self, requestor, fcn, args):
        if not isinstance(args, list):
            args = [args]
            
        kwargs = {
            "requestor": requestor,
            "channel_name": self.wrapper.channel_name,
            "peers": self.wrapper.default_peers,
            "args": args,
            "cc_name": self.wrapper.chaincode_name,
            "fcn": fcn
        }
        coro = self.wrapper.client.chaincode_query(**kwargs)
        future = asyncio.run_coroutine_threadsafe(coro, _fabric_client_loop)
        return future.result()

fabric_client = FabricClient()
