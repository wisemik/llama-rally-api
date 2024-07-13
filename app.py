import json
import time
import logging
import random
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
import os
import openai
import anthropic
from flask import Flask, request, jsonify, Response
from flask_cors import CORS  # Import the CORS module

load_dotenv()

# Clients for different LLM services
clientAnthropic = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
clientOpenai = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Web3 setup
RPC_URL = os.getenv('RPC_URL')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
CONTRACT_ADDRESS = os.getenv('SIMPLE_LLM_CONTRACT_ADDRESS')

if not RPC_URL or not PRIVATE_KEY or not CONTRACT_ADDRESS:
    raise ValueError("Missing required environment variables")

web3 = Web3(Web3.HTTPProvider(RPC_URL))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
if not web3.is_connected():
    raise ConnectionError("Unable to connect to Ethereum node")

with open('abis/OpenAiSimpleLLM.json', 'r') as file:
    contract_abi = json.load(file)
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)
account = web3.eth.account.from_key(PRIVATE_KEY)

# Flask app setup


app = Flask(__name__)
CORS(app)  # Enable CORS for the app

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model lists
CHATGPT_MODELS = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o']
CLAUDE_MODELS = []
ALL_MODELS = CHATGPT_MODELS + CLAUDE_MODELS

# Helper functions
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
    return web3.eth.wait_for_transaction_receipt(tx_hash)

def get_contract_response():
    while True:
        response = contract.functions.response().call()
        if response:
            return response
        time.sleep(2)

def get_openai_completion(message, model='gpt-3.5-turbo'):
    completion = clientOpenai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
            {"role": "user", "content": message}
        ]
    )
    return completion.choices[0].message.content

def get_claude_completion(message, model='claude-3-5-sonnet-20240620'):
    response = clientAnthropic.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": message}]
    )
    return response.content[0].text if response.content and len(response.content) > 0 else ""

def select_random_models():
    return random.sample(ALL_MODELS, 2)

def handle_llm_request(message, model):
    if model in CHATGPT_MODELS:
        return get_openai_completion(message, model)
    elif model in CLAUDE_MODELS:
        return get_claude_completion(message, model)
    else:
        return None


def handle_llm_stream_request(message, model):
    logger.info(f"Streaming request received for model: {model}")
    try:
        if model in CHATGPT_MODELS:
            logger.info(f"Using OpenAI model: {model}")
            stream = clientOpenai.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": message}],
                stream=True,
            )
            logger.info("Started streaming from OpenAI")
            try:
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        logger.info(f"Streaming chunk: {chunk.choices[0].delta.content}")
                        yield f"{chunk.choices[0].delta.content}\n\n"
            except Exception as e:
                logger.error(f"Error while streaming from OpenAI: {str(e)}")
            logger.info("Finished streaming from OpenAI")
        elif model in CLAUDE_MODELS:
            logger.info(f"Using Claude model: {model}")
            logger.info("Entered stream_claude_response")
            response = clientAnthropic.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": message}],
                stream=True,
            )
            logger.info("Started streaming from Claude")
            try:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        event_data = json.loads(decoded_line)
                        if event_data.get('type') == 'completion':
                            completion_data = {
                                "type": "completion",
                                "completion": event_data.get('completion', ''),
                                "stop_reason": event_data.get('stop_reason'),
                                "model": model
                            }
                            logger.info(f"Streaming chunk: {completion_data}")
                            yield f"event: completion\ndata: {json.dumps(completion_data)}\n\n"
            except Exception as e:
                logger.error(f"Error while streaming from Claude: {str(e)}")
            logger.info("Finished streaming from Claude")
        else:
            logger.error(f"Invalid model: {model}")
            yield f"data: {{\"error\": \"Invalid model: {model}. Available models are: {ALL_MODELS}\"}}\n\n"
    except Exception as e:
        logger.error(f"Error in handle_llm_stream_request: {str(e)}")
        yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"

# Routes
@app.route('/random_models', methods=['GET'])
def random_models():
    modelA, modelB = select_random_models()
    return jsonify({'modelA': modelA, 'modelB': modelB})

@app.route('/llm_request', methods=['POST'])
def llm_request():
    data = request.json
    message = data.get('message')
    model = data.get('model')
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    if model not in ALL_MODELS:
        return jsonify({'error': f'Invalid model: {model}. Available models are: {ALL_MODELS}'}), 400

    logger.info(f"Received message for LLM completion: {message}, model: {model}")
    response = handle_llm_request(message, model)
    if response is None:
        return jsonify({'error': 'Failed to get a response from the model'}), 500

    logger.info(f"LLM response: {response}")
    return jsonify({'message': message, 'response': response})

@app.route('/llm_request_streaming', methods=['POST'])
def llm_request_streaming():
    data = request.json
    message = data.get('message')
    model = data.get('model', 'gpt-3.5-turbo')  # Default to gpt-3.5-turbo if model not provided
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    if model not in ALL_MODELS:
        return jsonify({'error': f'Invalid model: {model}. Available models are: {ALL_MODELS}'}), 400

    logger.info(f"Received message for LLM streaming: {message}, model: {model}")
    return Response(handle_llm_stream_request(message, model), content_type='text/event-stream')

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
