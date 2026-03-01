package main

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// EvidenceRecord defines the structure for honeypot evidence
type EvidenceRecord struct {
	EvidenceID     string            `json:"evidenceId"`
	Timestamp      int64             `json:"timestamp"`
	HoneypotID     string            `json:"honeypotId"`
	HoneypotType   string            `json:"honeypotType"`
	AttackType     string            `json:"attackType"`
	SourceIPHash   string            `json:"sourceIpHash"`
	MitreTechnique []string          `json:"mitreTechnique"`
	PayloadHash    string            `json:"payloadHash" a`
	Submitter      string            `json:"submitter"`
	Status         string            `json:"status"` // new, verified, archived
	ChainOfCustody []CustodyTransfer `json:"chainOfCustody"`
}

type CustodyTransfer struct {
	From      string `json:"from"`
	To        string `json:"to"`
	Timestamp int64  `json:"timestamp"`
	Reason    string `json:"reason"`
}

// SmartContract is the main contract
type SmartContract struct {
	contractapi.Contract
}

// InitLedger adds a base set of evidence to the ledger (for testing)
func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	evidence := []EvidenceRecord{
		{
			EvidenceID:     "EVID-001",
			Timestamp:      time.Now().Unix(),
			HoneypotID:     "ssh-honeypot-01",
			HoneypotType:   "ssh",
			AttackType:     "bruteforce",
			SourceIPHash:   "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
			MitreTechnique: []string{"T1110.001"},
			PayloadHash:    "sha256-abc123...",
			Submitter:      "admin",
			Status:         "verified",
			ChainOfCustody: []CustodyTransfer{},
		},
		{
			EvidenceID:     "EVID-002",
			Timestamp:      time.Now().Unix() - 3600,
			HoneypotID:     "web-honeypot-01",
			HoneypotType:   "web",
			AttackType:     "sql_injection",
			SourceIPHash:   "a1b2c3d4e5f6...",
			MitreTechnique: []string{"T1190"},
			PayloadHash:    "sha256-def456...",
			Submitter:      "admin",
			Status:         "new",
			ChainOfCustody: []CustodyTransfer{},
		},
	}

	for _, ev := range evidence {
		evJSON, err := json.Marshal(ev)
		if err != nil {
			return err
		}
		err = ctx.GetStub().PutState(ev.EvidenceID, evJSON)
		if err != nil {
			return fmt.Errorf("failed to put evidence: %v", err)
		}
	}
	return nil
}

// SubmitEvidence adds new evidence to the ledger
func (s *SmartContract) SubmitEvidence(ctx contractapi.TransactionContextInterface,
	evidenceID string, honeypotID string, honeypotType string,
	attackType string, sourceIPHash string, mitreTechnique string,
	payloadHash string) error {

	// Check if evidence already exists
	exists, err := s.EvidenceExists(ctx, evidenceID)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("evidence %s already exists", evidenceID)
	}

	// Get submitter's MSP ID
	clientID, err := ctx.GetClientIdentity().GetID()
	if err != nil {
		return fmt.Errorf("failed to get client identity: %v", err)
	}

	// Create evidence record
	evidence := EvidenceRecord{
		EvidenceID:     evidenceID,
		Timestamp:      time.Now().Unix(),
		HoneypotID:     honeypotID,
		HoneypotType:   honeypotType,
		AttackType:     attackType,
		SourceIPHash:   sourceIPHash,
		MitreTechnique: []string{mitreTechnique},
		PayloadHash:    payloadHash,
		Submitter:      clientID,
		Status:         "new",
		ChainOfCustody: []CustodyTransfer{},
	}

	evJSON, err := json.Marshal(evidence)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(evidenceID, evJSON)
}

// QueryEvidence returns the evidence stored in the ledger with given id
func (s *SmartContract) QueryEvidence(ctx contractapi.TransactionContextInterface, evidenceID string) (*EvidenceRecord, error) {
	evJSON, err := ctx.GetStub().GetState(evidenceID)
	if err != nil {
		return nil, fmt.Errorf("failed to read evidence: %v", err)
	}
	if evJSON == nil {
		return nil, fmt.Errorf("evidence %s does not exist", evidenceID)
	}

	var evidence EvidenceRecord
	err = json.Unmarshal(evJSON, &evidence)
	if err != nil {
		return nil, err
	}
	return &evidence, nil
}

// QueryAllEvidence returns all evidence found in the ledger
func (s *SmartContract) QueryAllEvidence(ctx contractapi.TransactionContextInterface) ([]*EvidenceRecord, error) {
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var evidence []*EvidenceRecord
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}
		var ev EvidenceRecord
		err = json.Unmarshal(queryResponse.Value, &ev)
		if err != nil {
			return nil, err
		}
		evidence = append(evidence, &ev)
	}
	return evidence, nil
}

// UpdateEvidenceStatus changes the status of an evidence (new -> verified -> archived)
func (s *SmartContract) UpdateEvidenceStatus(ctx contractapi.TransactionContextInterface, evidenceID string, newStatus string) error {
	ev, err := s.QueryEvidence(ctx, evidenceID)
	if err != nil {
		return err
	}
	// Optionally, validate allowed transitions
	ev.Status = newStatus
	evJSON, _ := json.Marshal(ev)
	return ctx.GetStub().PutState(evidenceID, evJSON)
}

// TransferCustody records a transfer of evidence between parties
func (s *SmartContract) TransferCustody(ctx contractapi.TransactionContextInterface, evidenceID string, to string, reason string) error {
	ev, err := s.QueryEvidence(ctx, evidenceID)
	if err != nil {
		return err
	}
	from := ev.Submitter // current owner

	transfer := CustodyTransfer{
		From:      from,
		To:        to,
		Timestamp: time.Now().Unix(),
		Reason:    reason,
	}
	ev.ChainOfCustody = append(ev.ChainOfCustody, transfer)
	ev.Submitter = to // update current owner

	evJSON, _ := json.Marshal(ev)
	return ctx.GetStub().PutState(evidenceID, evJSON)
}

// VerifyIntegrity compares the stored payload hash with a submitted hash
func (s *SmartContract) VerifyIntegrity(ctx contractapi.TransactionContextInterface, evidenceID string, submittedHash string) (bool, error) {
	ev, err := s.QueryEvidence(ctx, evidenceID)
	if err != nil {
		return false, err
	}
	return ev.PayloadHash == submittedHash, nil
}

// GetEvidenceByType queries using a CouchDB selector (requires CouchDB)
func (s *SmartContract) GetEvidenceByType(ctx contractapi.TransactionContextInterface, honeypotType string) ([]*EvidenceRecord, error) {
	queryString := fmt.Sprintf(`{"selector":{"honeypotType":"%s"}}`, honeypotType)
	return s.getQueryResult(ctx, queryString)
}

// GetEvidenceByTimeRange queries evidence between start and end timestamps
func (s *SmartContract) GetEvidenceByTimeRange(ctx contractapi.TransactionContextInterface, startTime int64, endTime int64) ([]*EvidenceRecord, error) {
	queryString := fmt.Sprintf(`{"selector":{"timestamp":{"$gte":%d,"$lte":%d}}}`, startTime, endTime)
	return s.getQueryResult(ctx, queryString)
}

// Helper to execute rich queries
func (s *SmartContract) getQueryResult(ctx contractapi.TransactionContextInterface, queryString string) ([]*EvidenceRecord, error) {
	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var records []*EvidenceRecord
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}
		var ev EvidenceRecord
		err = json.Unmarshal(queryResponse.Value, &ev)
		if err != nil {
			return nil, err
		}
		records = append(records, &ev)
	}
	return records, nil
}

// EvidenceExists returns true when evidence with given ID exists in ledger.
func (s *SmartContract) EvidenceExists(ctx contractapi.TransactionContextInterface, evidenceID string) (bool, error) {
	evJSON, err := ctx.GetStub().GetState(evidenceID)
	if err != nil {
		return false, fmt.Errorf("failed to read evidence: %v", err)
	}
	return evJSON != nil, nil
}

// SubmitPrivateEvidence stores sensitive data in a private collection
func (s *SmartContract) SubmitPrivateEvidence(ctx contractapi.TransactionContextInterface, evidenceID string, rawIP string, sessionLog string) error {
	privateData := map[string]string{
		"rawIP":      rawIP,
		"sessionLog": sessionLog,
	}
	privateBytes, _ := json.Marshal(privateData)
	return ctx.GetStub().PutPrivateData("collectionEvidencePrivate", evidenceID, privateBytes)
}

// QueryPrivateEvidence retrieves private data (requires authorization)
func (s *SmartContract) QueryPrivateEvidence(ctx contractapi.TransactionContextInterface, evidenceID string) (string, error) {
	privateBytes, err := ctx.GetStub().GetPrivateData("collectionEvidencePrivate", evidenceID)
	if err != nil {
		return "", fmt.Errorf("failed to read private data: %v", err)
	}
	if privateBytes == nil {
		return "", fmt.Errorf("private evidence %s does not exist", evidenceID)
	}
	return string(privateBytes), nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		fmt.Printf("Error creating chaincode: %s", err.Error())
		return
	}
	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting chaincode: %s", err.Error())
	}
}
