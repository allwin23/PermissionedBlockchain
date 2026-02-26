#!/usr/bin/env bash

cd ~/repos/PermissionedBlockchain/go/src/github.com/alls23/fabric-samples/test-network

echo "Tearing down existing Test Network..."
./network.sh down
docker volume rm $(docker volume ls -qf dangling=true) || true
rm -rf channel-artifacts/

echo "Starting Test Network with CouchDB and CA..."
./network.sh up -ca -s couchdb

echo "Creating 'evidencechannel'..."
./network.sh createChannel -c evidencechannel

echo "Deploying Evidence Chaincode..."
./network.sh deployCC -ccn evidence -ccp ./chaincode/evidence/go -ccl go -c evidencechannel -cccg ./chaincode/evidence/go/collections_config.json

echo "Network ready."
