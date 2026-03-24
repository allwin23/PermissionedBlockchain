from flask import Blueprint, jsonify, request, session, send_file
from fabric_interface.client import fabric_client
from api.auth import login_required
from ipfs_interface.client import ipfs_client
import json
import os


def decode_response(response):
    if isinstance(response, bytes):
        return response.decode('utf-8')
    return response


evidence_bp = Blueprint('evidence', __name__)


@evidence_bp.route('', methods=['POST'])
@login_required
def submit_evidence():
    try:
        # Check if form data is sent (multipart)
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            file = request.files.get('file')

            payload_hash = data.get('payloadHash', '')
            if file and file.filename != '':
                # Save temporarily
                temp_path = os.path.join('/tmp', file.filename)
                file.save(temp_path)

                # Upload to IPFS
                try:
                    if ipfs_client.client:
                        payload_hash = ipfs_client.upload_file(temp_path)
                    else:
                        print("IPFS client not available, skipping upload")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
        else:
            data = request.json
            payload_hash = data.get('payloadHash', '')

        # Ensure all arguments are strings for the Fabric SDK
        mitre_tech = data.get('mitreTechnique', '')
        if isinstance(mitre_tech, list):
            mitre_tech = ",".join(mitre_tech)

        args = [
            str(data['evidenceId']),
            str(data['honeypotId']),
            str(data['honeypotType']),
            str(data['attackType']),
            str(data['sourceIpHash']),
            str(mitre_tech),
            str(payload_hash)
        ]

        requestor = fabric_client.get_default_requestor()
        tx_id = fabric_client.submit_transaction(
            requestor, 'SubmitEvidence', args)
        return jsonify({'status': 'success', 'tx_id': tx_id, 'ipfs_cid': payload_hash}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@evidence_bp.route('/<evidence_id>', methods=['GET'])
@login_required
def get_evidence(evidence_id):
    try:
        requestor = fabric_client.get_default_requestor()
        response = fabric_client.query_transaction(
            requestor, 'QueryEvidence', [evidence_id])
        return jsonify({'status': 'success', 'data': json.loads(decode_response(response))}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@evidence_bp.route('/all', methods=['GET'])
@login_required
def get_all_evidence():
    try:
        requestor = fabric_client.get_default_requestor()
        response = fabric_client.query_transaction(
            requestor, 'QueryAllEvidence', [])
        return jsonify({'status': 'success', 'data': json.loads(decode_response(response))}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@evidence_bp.route('/<evidence_id>/status', methods=['PUT'])
@login_required
def update_status(evidence_id):
    data = request.json
    try:
        requestor = fabric_client.get_default_requestor()
        tx_id = fabric_client.submit_transaction(requestor, 'UpdateEvidenceStatus', [
                                                 evidence_id, data['status']])
        return jsonify({'status': 'success', 'tx_id': tx_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@evidence_bp.route('/<evidence_id>/transfer', methods=['POST'])
@login_required
def transfer_custody(evidence_id):
    data = request.json
    try:
        requestor = fabric_client.get_default_requestor()
        # Chaincode expects [evidenceID, to, reason]
        reason = data.get('reason', 'Administrative transfer')
        tx_id = fabric_client.submit_transaction(requestor, 'TransferCustody', [
                                                 evidence_id, data['newOwningOrg'], reason])
        return jsonify({'status': 'success', 'tx_id': tx_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@evidence_bp.route('/<evidence_id>/payload', methods=['GET'])
@login_required
def download_payload(evidence_id):
    try:
        requestor = fabric_client.get_default_requestor()
        response = fabric_client.query_transaction(
            requestor, 'QueryEvidence', [evidence_id])
        evidence_data = json.loads(decode_response(response))

        cid = evidence_data.get('payloadHash')
        if not cid:
            return jsonify({'error': 'No payload CID associated with this evidence'}), 404

        temp_download_path = os.path.join('/tmp', cid)
        if ipfs_client.client:
            ipfs_client.download_file(cid, temp_download_path)
            return send_file(temp_download_path, as_attachment=True)
        else:
            return jsonify({'error': 'IPFS client not available to download payload'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 400
