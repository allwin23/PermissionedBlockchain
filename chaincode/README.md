# Evidence Chaincode

This is the Smart Contract (Chaincode) representing the honeypot Evidence ledger for the Hyperledger Fabric test network.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Data Structures](#data-structures)
3. [Functions](#functions)
4. [Deployment](#deployment)
5. [Testing](#testing)

---

## Data Structures

### EvidenceRecord
The primary asset stored in the world state.

- `evidenceId` (string): Unique identifier.
- `timestamp` (int64): Epoch time of logging.
- `honeypotId` (string): The honeypot sensor origin ID.
- `honeypotType` (string): Type of sensor (e.g. `ssh`, `web`).
- `attackType` (string): Classification (e.g. `bruteforce`).
- `sourceIpHash` (string): Obfuscated IP address.
- `mitreTechnique` ([]string): Array of MITRE ATT&CK codes (e.g. `T1110.001`).
- `payloadHash` (string): Hash of the captured payload/file.
- `submitter` (string): The ID of the submitting agent.
- `status` (string): Current status (`new`, `verified`, `archived`).
- `chainOfCustody` ([]CustodyTransfer): Transfer history log.

### Private Data Collection
The chaincode supports a Private Data Collection named `collectionEvidencePrivate`, mapped in `collections_config.json`.
- Policy: `OR('Org1MSP.member', 'Org2MSP.member')`
- Attributes: `rawIP`, `sessionLog`

---

## Functions

### `InitLedger`
Initializes the ledger with base mock data.

**Args:** None

### `SubmitEvidence`
Adds a standard, public evidence asset to the ledger.

**Args:**
1. `evidenceID` (string)
2. `honeypotID` (string)
3. `honeypotType` (string)
4. `attackType` (string)
5. `sourceIPHash` (string)
6. `mitreTechnique` (string)
7. `payloadHash` (string)

**Example:**
```bash
peer chaincode invoke ... -c '{"function":"SubmitEvidence","Args":["EVID-003","ssh-hp-02","ssh","password_spraying","hash123","T1110","hash456"]}'
```

### `QueryEvidence`
Reads an evidence record by its string Identity from the ledger.

**Args:**
1. `evidenceID` (string)

### `QueryAllEvidence`
Retrieves all evidence entries physically stored on the ledger. Requires no arguments.

### `UpdateEvidenceStatus`
Updates the internal tracking mode status of an evidence asset.

**Args:**
1. `evidenceID` (string)
2. `newStatus` (string)

### `VerifyIntegrity`
A simple helper that reads an evidence record and compares its stored `payloadHash` against an explicit client-provided string hash to yield `true` or `false`.

**Args:**
1. `evidenceID` (string)
2. `submittedHash` (string)

### `GetEvidenceByType`
Executes a Rich CouchDB Query selector exclusively targeting the indexed `honeypotType` property.
*Requires: CouchDB enabled.*

**Args:**
1. `honeypotType` (string)

### `GetEvidenceByTimeRange`
Executes a Rich CouchDB Query over the integer `timestamp` limits.
*Requires: CouchDB enabled.*

**Args:**
1. `startTime` (int64)
2. `endTime` (int64)

### `SubmitPrivateEvidence`
Adds sensitive attributes (rawIP and sessionLog) to the `collectionEvidencePrivate` secure collection mapping directly to the `evidenceID`.

**Args:**
1. `evidenceID` (string)
2. `rawIP` (string)
3. `sessionLog` (string)

### `QueryPrivateEvidence`
Retrieves securely-stored private properties based on authorization constraints.

**Args:**
1. `evidenceID` (string)

---

## Deployment
From the `test-network` directory:
```bash
./network.sh deployCC -ccn evidence -ccp ./chaincode/evidence/go -ccl go -c evidencechannel -cccg ./chaincode/evidence/go/collections_config.json
```
