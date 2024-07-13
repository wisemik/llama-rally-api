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
import openai
import anthropic

load_dotenv()

clientAnthropic = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

clientOpenai = openai.OpenAI(
  api_key=os.getenv('OPENAI_API_KEY')
)
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

    return jsonify({
        'response': response
    })



def get_openai_completion(message):
    completion = clientOpenai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
            {"role": "user", "content": message}
        ]
    )

    return completion.choices[0].message.content


def get_claude_completion(message):
    response = clientAnthropic.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Hello, Claude"}
        ]
    )

    # Extract the text from the first content block
    if response.content and len(response.content) > 0:
        response_text = response.content[0].text
    else:
        response_text = ""

    print(response_text)
    return response_text

@app.route('/openai_response', methods=['POST'])
def openai_response():
    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({'error': 'Message is required'}), 400

    logger.info(f"Received message for OpenAI completion: {message}")
    openai_response = get_openai_completion(message)
    logger.info(f"OpenAI response: {openai_response}")

    return jsonify({
        'message': message,
        'openai_response': openai_response
    })


@app.route('/claude_response', methods=['POST'])
def claude_response():
    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({'error': 'Message is required'}), 400

    logger.info(f"Received message for Claude completion: {message}")
    claude_response = get_claude_completion(message)
    logger.info(f"Claude response: {claude_response}")

    return jsonify({
        'message': message,
        'claude_response': claude_response
    })

@app.route('/criticize_user_request', methods=['POST'])
def criticize_user_request():
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    logger.info(f"Received message: {prompt}")

    message = ("You are to receive a user message that is a prompt."
               "Your task is to evaluate this prompt,"
               "determine if it is good or bad, and assign it a score out of 10."
               "Additionally, provide a description explaining your score."
               "Your final output should be in JSON format with two fields: score and description."
               "\n\nPlease provide your evaluation in the following JSON format (and ONLY in this format):\n\n{\"score\": <score out of 10>,"
               "\"description\": \"<explanation of the score>\"}"
               f"\n\nHere is the user's prompt for you to evaluate:\n\n{prompt}")

    tx_hash = send_message_to_contract(message)
    logger.info(f"Transaction sent, tx hash: {tx_hash.hex()}")
    receipt = wait_for_transaction_receipt(tx_hash)
    logger.info(f"Transaction receipt: {receipt}")
    time.sleep(10)

    response = get_contract_response()
    logger.info(f"Contract response: {response}")

    try:
        response_data = json.loads(response)
        score = response_data.get('score')
        description = response_data.get('description')
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing response: {e}")
        return jsonify({'error': 'Failed to parse contract response'}), 500

    return jsonify({
        'score': score,
        'description': description
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
