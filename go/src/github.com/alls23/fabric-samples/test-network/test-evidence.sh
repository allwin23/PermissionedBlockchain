#!/usr/bin/env bash

# Set environment for peer CLI
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=${PWD}/../config/
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

echo "==========================================="
echo "1. Initializing Ledger"
echo "==========================================="
peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com \
  --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  -C evidencechannel -n evidence \
  --peerAddresses localhost:7051 --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
  --peerAddresses localhost:9051 --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt \
  -c '{"function":"InitLedger","Args":[]}'

sleep 5

echo "==========================================="
echo "2. Submitting New Evidence"
echo "==========================================="
peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com \
  --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  -C evidencechannel -n evidence \
  --peerAddresses localhost:7051 --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
  --peerAddresses localhost:9051 --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt \
  -c '{"function":"SubmitEvidence","Args":["EVID-003","ssh-honeypot-02","ssh","password_spraying","ip_hash_123","T1110.003","sha256-xyz789"]}'

sleep 5

echo "==========================================="
echo "3. Querying Evidence EVID-001"
echo "==========================================="
peer chaincode query -C evidencechannel -n evidence -c '{"function":"QueryEvidence","Args":["EVID-001"]}'

echo "==========================================="
echo "4. Querying All Evidence"
echo "==========================================="
peer chaincode query -C evidencechannel -n evidence -c '{"function":"QueryAllEvidence","Args":[]}'

echo "==========================================="
echo "5. Updating Evidence Status for EVID-003"
echo "==========================================="
peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com \
  --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  -C evidencechannel -n evidence \
  --peerAddresses localhost:7051 --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
  --peerAddresses localhost:9051 --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt \
  -c '{"function":"UpdateEvidenceStatus","Args":["EVID-003","verified"]}'

sleep 5

echo "==========================================="
echo "6. Verifying Integrity for EVID-001"
echo "==========================================="
peer chaincode query -C evidencechannel -n evidence -c '{"function":"VerifyIntegrity","Args":["EVID-001","sha256-abc123..."]}'

echo "==========================================="
echo "7. Rich Querying by Evidence Type (ssh)"
echo "==========================================="
peer chaincode query -C evidencechannel -n evidence -c '{"function":"GetEvidenceByType","Args":["ssh"]}'
