import json
import time
import logging
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
from eth_utils import to_dict, to_hex

load_dotenv()

RPC_URL = os.getenv('RPC_URL')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
CONTRACT_ADDRESS = os.getenv('SIMPLE_LLM_CONTRACT_ADDRESS')

if not RPC_URL:
    raise ValueError("Missing RPC_URL in .env")
if not PRIVATE_KEY:
    raise ValueError("Missing PRIVATE_KEY in .env")
if not CONTRACT_ADDRESS:
    raise ValueError("Missing SIMPLE_LLM_CONTRACT_ADDRESS in .env")

web3 = Web3(Web3.HTTPProvider(RPC_URL))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

if not web3.is_connected():
    raise ConnectionError("Unable to connect to Ethereum node")

with open('abis/OpenAiSimpleLLM.json', 'r') as file:
    contract_abi = json.load(file)
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)
account = web3.eth.account.from_key(PRIVATE_KEY)

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_message_to_contract(message):
    nonce = web3.eth.get_transaction_count(account.address)
    txn = contract.functions.sendMessage(message).build_transaction({
        'chainId': 696969,
        'gas': 2000000,
        'gasPrice': web3.to_wei('5', 'gwei'),
        'nonce': nonce
    })

    signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)

    return tx_hash


def wait_for_transaction_receipt(tx_hash):
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt


def get_contract_response():
    while True:
        response = contract.functions.response().call()
        if response:
            return response
        time.sleep(2)


# def convert_to_serializable(obj):
#     """Recursively converts AttributeDict and HexBytes objects to serializable types."""
#     if isinstance(obj, bytes):
#         return obj.hex()
#     elif isinstance(obj, list):
#         return [convert_to_serializable(item) for item in obj]
#     elif isinstance(obj, dict):
#         return {key: convert_to_serializable(value) for key, value in obj.items()}
#     elif isinstance(obj, AttributeDict):
#         return {key: convert_to_serializable(value) for key, value in obj.items()}
#     return obj


@app.route('/send_message_galadriel', methods=['POST'])
def send_message_galadriel():
    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({'error': 'Message is required'}), 400

    logger.info(f"Received message: {message}")
    tx_hash = send_message_to_contract(message)
    logger.info(f"Transaction sent, tx hash: {tx_hash.hex()}")
    receipt = wait_for_transaction_receipt(tx_hash)
    logger.info(f"Transaction receipt: {receipt}")
    time.sleep(10)

    response = get_contract_response()
    logger.info(f"Contract response: {response}")

    # Convert the receipt to a serializable format
    # receipt_dict = convert_to_serializable(dict(receipt))

    return jsonify({
        'response': response
    })


@app.route('/criticize_user_request', methods=['POST'])
def criticize_user_request():
    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({'error': 'Message is required'}), 400

    logger.info(f"Received message: {message}")
    tx_hash = send_message_to_contract(message)
    logger.info(f"Transaction sent, tx hash: {tx_hash.hex()}")
    receipt = wait_for_transaction_receipt(tx_hash)
    logger.info(f"Transaction receipt: {receipt}")
    time.sleep(10)

    response = get_contract_response()
    logger.info(f"Contract response: {response}")

    # Convert the receipt to a serializable format
    # receipt_dict = convert_to_serializable(dict(receipt))

    return jsonify({
        'response': response
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
