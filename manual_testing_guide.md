# Permissioned Blockchain: Manual Testing Guide

This guide provides a comprehensive overview of the system logic and all the CLI commands required to set up, manage, and test the Permissioned Blockchain network and its backend integration.

---

## 🧠 System Logic Overview

### 1. Chaincode Logic (Smart Contract)
The `evidence` chaincode (located in `chaincode/evidence.go`) manages cyber-threat evidence records.
- **Evidence Lifecycle**: It supports submitting new evidence, querying existing records (singular or all), updating status (e.g., from `new` to `verified`), and recording custody transfers.
- **Integrity Management**: Stores a SHA-256 hash of the evidence payload. This hash is cross-referenced with files stored off-chain on IPFS to ensure data integrity.
- **Data Model**: Uses `EvidenceRecord` struct which includes fields for ID, timestamp, honeypot metadata, Mitre techniques, and a `ChainOfCustody` array.
- **Private Data**: Sensitive data (like raw IP addresses) is stored in a Private Data Collection (`collectionEvidencePrivate`), ensuring it is only shared between authorized peers.

### 2. Block & Ledger Logic
- **Distributed Ledger**: Consists of a blockchain (log of all transactions) and a World State (current values).
- **World State (CouchDB)**: Uses CouchDB to enable "Rich Queries." This allows complex filtering (e.g., searching by `honeypotType` or `timestamp` range) directly on the ledger.
- **Block Formation**: Transactions are validated by endorsing peers, ordered into blocks by the Orderer, and then committed to the ledgers of all peers in the channel.

### 3. Backend Logic (Flask & SDK)
The backend service (in `backend/`) acts as the gateway for the system.
- **Identity & Wallets**: Manages X.509 certificates in a `wallets/` directory. Each request is signed by a valid user identity (e.g., `alice`).
- **IPFS Integration**: When a file is uploaded via the API, the backend:
    1. Uploads the raw file to IPFS.
    2. Receives a unique CID (Content Identifier).
    3. Stores that CID on the blockchain as part of the evidence record.
- **REST Interface**: Maps HTTP endpoints to Fabric chaincode functions using the `hfc` Python SDK.

## 🐳 Docker Management & Cleanup

### 1. Starting & Checking Docker Service
Ensure the Docker daemon is running before starting the blockchain network.

```bash
# Start Docker Service (if not running)
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Check Docker status
sudo systemctl status docker

# Verify Docker version and connectivity
docker info
```

### 2. Image Generation & Management
In a Fabric environment, images are often generated automatically during chaincode deployment. However, you can manage images manually:

```bash
# List all Docker images
docker images

# Building a custom image (e.g., if you add a Dockerfile to the backend)
# cd backend && docker build -t permissioned-blockchain-backend .

# Remove specific images
docker rmi <image_id>

# Remove all dangling images (untagged)
docker image prune
```

### 3. Intensive Pruning & Cleanup
Use these commands if the network fails to start due to "Channel already exists" or "Conflict" errors.

```bash
# Stop the network first
cd ~/repos/PermissionedBlockchain/go/src/github.com/alls23/fabric-samples/test-network
./network.sh down

# Remove ALL containers, networks, and images (Use with caution)
docker system prune -a

# Specifically prune all volumes (This removes all data from CouchDB/Ledger)
docker volume prune

# List volumes to double check
docker volume ls
```

---

## 🚀 Deployment & Environment Commands

### 1. Prerequisites (Docker & Python)
Ensure Docker and Python environments are ready.

```bash
# Verify Docker is running
docker ps

# Install Backend Dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Hyperledger Fabric Network Setup
Starting the chain from scratch.

```bash
# Navigate to the test network
cd ~/repos/PermissionedBlockchain/go/src/github.com/alls23/fabric-samples/test-network

# Start the network with Certificate Authority (CA) and CouchDB
./network.sh up -ca -s couchdb

# Create the evidence channel
./network.sh createChannel -c evidencechannel

# Deploy the Evidence Chaincode with Private Data configuration
./network.sh deployCC -ccn evidence -ccp ./chaincode/evidence/go -ccl go -c evidencechannel -cccg ./chaincode/evidence/go/collections_config.json
```

---

## 🛠️ Management & Testing Commands

### 1. Network Pruning & Cleanup
If the channel already exists or you need to reset the environment.

```bash
# Stop the network and remove all containers/artifacts
./network.sh down

# Prune dangling Docker volumes (Clean prune)
docker volume rm $(docker volume ls -qf dangling=true)

# Remove old channel artifacts
rm -rf channel-artifacts/
```

### 2. Manual Chaincode Testing (Peer CLI)
Test the chaincode logic directly without the backend.

```bash
# Set up Peer CLI environment variables
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=${PWD}/../config/
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

# Invoke InitLedger (Seed sample data)
peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem -C evidencechannel -n evidence -c '{"function":"InitLedger","Args":[]}'

# Query All Evidence
peer chaincode query -C evidencechannel -n evidence -c '{"function":"QueryAllEvidence","Args":[]}'

# Submit New Evidence
peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem -C evidencechannel -n evidence -c '{"function":"SubmitEvidence","Args":["EVID-101","honeypot-v01","ssh","bruteforce","hashed_ip","T1110","ipfs_cid_placeholder"]}'
```

### 3. Backend Server Operations
Starting the backend and connecting it to the chain.

```bash
# Start the Flask Server (From backend directory)
cd ~/repos/PermissionedBlockchain/backend
source venv/bin/activate
python app.py
```

---

## 🌐 API & Integration Testing

### 1. API Calls (cURL)
Test the backend endpoints manually.

```bash
# 1. Login (To get session cookie)
curl -X POST http://localhost:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "alice", "password": "password"}' \
     -c cookies.txt

# 2. Get All Evidence
curl -X GET http://localhost:5000/api/evidence/all -b cookies.txt

# 3. Submit Evidence (JSON only)
curl -X POST http://localhost:5000/api/evidence \
     -b cookies.txt \
     -H "Content-Type: application/json" \
     -d '{
       "evidenceId": "EVID-WEB-001",
       "honeypotId": "web-pot-01",
       "honeypotType": "http",
       "attackType": "xss",
       "sourceIpHash": "ip_hash_abc",
       "mitreTechnique": ["T1190"],
       "payloadHash": "sha256-hash-example"
     }'

# 4. Submit Evidence with File Upload (IPFS Integration)
curl -X POST http://localhost:5000/api/evidence \
     -b cookies.txt \
     -F "file=@/path/to/evidence_payload.log" \
     -F "evidenceId=EVID-FILE-001" \
     -F "honeypotId=ssh-pot" \
     -F "honeypotType=ssh" \
     -F "attackType=exploit" \
     -F "sourceIpHash=hash123"
```

### 2. Automated Integration Tests
Run the pre-written integration scripts.

```bash
# Run the Fabric Client test script
cd ~/repos/PermissionedBlockchain/backend
source venv/bin/activate
python test_fabric.py

# Run Evidence Logic shell test
cd ~/repos/PermissionedBlockchain/go/src/github.com/alls23/fabric-samples/test-network
./test-evidence.sh
```
