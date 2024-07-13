import json
import time
import logging
import random

import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
import os
import openai
import anthropic
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import httpx

from circle import create_transfer

load_dotenv()

# Clients for different LLM services
clientAnthropic = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
clientOpenai = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Web3 setup
RPC_URL = os.getenv('RPC_URL')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
CONTRACT_CRITIC_ADDRESS = os.getenv('CONTRACT_CRITIC_ADDRESS')
CONTRACT_CRITIC_WALLET = os.getenv('CONTRACT_CRITIC_WALLET')

if not RPC_URL or not PRIVATE_KEY or not CONTRACT_CRITIC_ADDRESS:
    raise ValueError("Missing required environment variables")

web3 = Web3(Web3.HTTPProvider(RPC_URL))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
if not web3.is_connected():
    raise ConnectionError("Unable to connect to Ethereum node")

with open('abis/OpenAiSimpleLLM.json', 'r') as file:
    contract_abi = json.load(file)
account = web3.eth.account.from_key(PRIVATE_KEY)

# Flask app setup
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///models.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class ModelScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    score = db.Column(db.Float, default=1200)
    price = db.Column(db.Float, nullable=False)

class AgentScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    score = db.Column(db.Float, default=1200)
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(50), nullable=False)
    wallet = db.Column(db.String(50), nullable=False)


# Initialize models and agents from JSON if not already initialized
def initialize_models():
    if not ModelScore.query.first():
        with open('models_data.json', 'r') as file:
            models_data = json.load(file)
            for model in models_data:
                new_model = ModelScore(name=model['name'], price=model['price'])
                db.session.add(new_model)
            db.session.commit()

def initialize_agents():
    if not AgentScore.query.first():
        with open('agents_data.json', 'r') as file:
            agents_data = json.load(file)
            for agent in agents_data:
                new_agent = AgentScore(name=agent['name'], price=agent['price'],
                                       address=agent['address'], wallet=agent['wallet'])
                db.session.add(new_agent)
            db.session.commit()

with app.app_context():
    db.create_all()
    initialize_models()
    initialize_agents()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function to get all model names from JSON
def get_all_models():
    with open('models_data.json', 'r') as file:
        models_data = json.load(file)
    return [model['name'] for model in models_data]

# Helper function to get all agent names from JSON
def get_all_agents():
    with open('agents_data.json', 'r') as file:
        agents_data = json.load(file)
    return [agent['name'] for agent in agents_data]

ALL_MODELS = get_all_models()
ALL_AGENTS = get_all_agents()

# Helper functions

def send_message_to_contract(message, contract_address):
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

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

def get_contract_response(contract_address):
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
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

def select_random_agents():
    return random.sample(ALL_AGENTS, 2)

def handle_llm_request(message, model):
    if 'gpt' in model:
        return get_openai_completion(message, model)
    elif 'claude' in model:
        return get_claude_completion(message, model)
    else:
        return None

def handle_agent_request(message, agent_name):
    agent = AgentScore.query.filter_by(name=agent_name).first()
    if not agent:
        logger.error(f"Agent {agent_name} not found")
        return None

    contract_address = agent.address
    tx_hash = send_message_to_contract(message, contract_address)
    logger.info(f"Transaction sent, tx hash: {tx_hash.hex()}")
    receipt = wait_for_transaction_receipt(tx_hash)
    logger.info(f"Transaction receipt: {receipt}")
    time.sleep(10)

    response = get_contract_response(contract_address)
    logger.info(f"Contract response: {response}")

    return response


def handle_llm_stream_request(message, model):
    logger.info(f"Streaming request received for model: {model}")
    try:
        if 'gpt' in model:
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
        elif 'claude' in model:
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

@app.route('/random_models', methods=['GET'])
def random_models():
    modelA, modelB = select_random_models()
    return jsonify({'modelA': modelA, 'modelB': modelB})

@app.route('/random_agents', methods=['GET'])
def random_agents():
    agentA, agentB = select_random_agents()
    return jsonify({'agentA': agentA, 'agentB': agentB})

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

@app.route('/agent_request', methods=['POST'])
def agent_request():
    data = request.json
    message = data.get('message')
    agent = data.get('agent')
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    if agent not in ALL_AGENTS:
        return jsonify({'error': f'Invalid agent: {agent}. Available agents are: {ALL_AGENTS}'}), 400

    logger.info(f"Received message for agent completion: {message}, agent: {agent}")
    response = handle_agent_request(message, agent)
    if response is None:
        return jsonify({'error': 'Failed to get a response from the agent'}), 500

    logger.info(f"Agent response: {response}")
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

def payUser(wallet_address):
    # Placeholder function to pay the user
    logger.info(f"Paying user with wallet address: {wallet_address}")
    create_transfer("1", wallet_address)

def payAgent(wallet_address):
    # Placeholder function to pay the user
    logger.info(f"Paying agent with wallet address: {wallet_address}")
    create_transfer("1", wallet_address)

def payCritic(wallet_address):
    # Placeholder function to pay the user
    logger.info(f"Paying critic agent with wallet address: {wallet_address}")
    create_transfer("0.1", wallet_address)

@app.route('/criticize_user_request', methods=['POST'])
def criticize_user_request():
    data = request.json
    prompt = data.get('prompt')
    wallet_address = os.getenv("USER_WALLET_ADDRESS")

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    logger.info(f"Received message: {prompt}")

    # message = ("You are to receive a user message that is a prompt."
    #            "Your task is to evaluate this prompt,"
    #            "determine if it is good or bad, and assign it a score out of 10."
    #            "Additionally, provide a description explaining your score."
    #            "Your final output should be in JSON format with two fields: score and description."
    #            "\n\nPlease provide your evaluation in the following JSON format (and ONLY in this format,"
    #            "without ```json or ANY other info, only plain json):\n\n{\"score\": <score out of 10>,"
    #            "\"description\": \"<explanation of the score>\"}"
    #            f"\n\nHere is the user's prompt for you to evaluate:\n\n{prompt}")

    tx_hash = send_message_to_contract(prompt, CONTRACT_CRITIC_ADDRESS)
    logger.info(f"Transaction sent, tx hash: {tx_hash.hex()}")
    receipt = wait_for_transaction_receipt(tx_hash)
    logger.info(f"Transaction receipt: {receipt}")
    time.sleep(5)

    response = get_contract_response(CONTRACT_CRITIC_ADDRESS)
    logger.info(f"Contract response: {response}")

    try:
        response_data = json.loads(response)
        score = response_data.get('score')
        description = response_data.get('description')
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing response: {e}")
        return jsonify({'error': 'Failed to parse contract response'}), 500

    if wallet_address and score >= 7:
        payUser(wallet_address)

    payCritic(CONTRACT_CRITIC_WALLET)

    return jsonify({
        'score': score,
        'description': description
    })

@app.route('/vote', methods=['POST'])
def vote():
    data = request.json
    model_a = data.get('modelA')
    model_b = data.get('modelB')
    result = data.get('result')  # '<model_name>' or 'draw'

    if not model_a or not model_b or (result not in [model_a, model_b, 'draw']):
        return jsonify({'error': 'Invalid input'}), 400

    model_a_record = ModelScore.query.filter_by(name=model_a).first()
    model_b_record = ModelScore.query.filter_by(name=model_b).first()

    if not model_a_record or not model_b_record:
        return jsonify({'error': 'Model not found'}), 404

    update_elo_ratings(model_a_record, model_b_record, result)

    db.session.commit()

    return jsonify({'message': 'Vote recorded and ratings updated'})

@app.route('/vote_agents', methods=['POST'])
def vote_agents():
    data = request.json
    agent_a = data.get('agentA')
    agent_b = data.get('agentB')
    result = data.get('result')  # '<agent_name>' or 'draw'

    if not agent_a or not agent_b or (result not in [agent_a, agent_b, 'draw']):
        return jsonify({'error': 'Invalid input'}), 400

    agent_a_record = AgentScore.query.filter_by(name=agent_a).first()
    agent_b_record = AgentScore.query.filter_by(name=agent_b).first()

    if not agent_a_record or not agent_b_record:
        return jsonify({'error': 'Agent not found'}), 404

    update_elo_ratings_agents(agent_a_record, agent_b_record, result)

    # Pay the winning agent
    if result == agent_a_record.name:
        payAgent(agent_a_record.wallet)
    elif result == agent_b_record.name:
        payAgent(agent_b_record.wallet)

    db.session.commit()

    return jsonify({'message': 'Vote recorded and ratings updated'})


def update_elo_ratings(model_a, model_b, result):
    K = 32  # ELO constant

    def calculate_new_rating(rating, opponent_rating, actual_score):
        expected_score = 1 / (1 + 10 ** ((opponent_rating - rating) / 400))
        return rating + K * (actual_score - expected_score)

    if result == model_a.name:
        score_a, score_b = 1, 0
    elif result == model_b.name:
        score_a, score_b = 0, 1
    elif result == 'draw':
        score_a, score_b = 0.5, 0.5

    model_a.score = calculate_new_rating(model_a.score, model_b.score, score_a)
    model_b.score = calculate_new_rating(model_b.score, model_a.score, score_b)

def update_elo_ratings_agents(agent_a, agent_b, result):
    K = 32  # ELO constant

    def calculate_new_rating(rating, opponent_rating, actual_score):
        expected_score = 1 / (1 + 10 ** ((opponent_rating - rating) / 400))
        return rating + K * (actual_score - expected_score)

    if result == agent_a.name:
        score_a, score_b = 1, 0
    elif result == agent_b.name:
        score_a, score_b = 0, 1
    elif result == 'draw':
        score_a, score_b = 0.5, 0.5

    agent_a.score = calculate_new_rating(agent_a.score, agent_b.score, score_a)
    agent_b.score = calculate_new_rating(agent_b.score, agent_a.score, score_b)

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    models = ModelScore.query.order_by(ModelScore.score.desc()).all()
    leaderboard = [
        {
            'rank': idx + 1,
            'name': model.name,
            'score': model.score,
            'price': model.price,
            'price_per_score':  model.score / model.price if model.price != 0 else 0
        }
        for idx, model in enumerate(models)
    ]
    return jsonify(leaderboard)

@app.route('/leaderboard_agents', methods=['GET'])
def leaderboard_agents():
    agents = AgentScore.query.order_by(AgentScore.score.desc()).all()
    leaderboard = [
        {
            'rank': idx + 1,
            'name': agent.name,
            'score': agent.score,
            'price': agent.price,
            'price_per_score': agent.score / agent.price if agent.price != 0 else 0
        }
        for idx, agent in enumerate(agents)
    ]
    return jsonify(leaderboard)

@app.route('/verify', methods=['POST'])
def verify():
    req_body = request.json
    print("Received request to verify credential:\n", req_body)

    payload = {
        "nullifier_hash": req_body["nullifier_hash"],
        "merkle_root": req_body["merkle_root"],
        "proof": req_body["proof"],
        "verification_level": req_body["verification_level"],
        "action": req_body["action"],
        "signal": req_body["signal"],
    }

    print("Sending request to World ID /verify endpoint:\n", payload)

    verify_endpoint = f"{os.getenv('NEXT_PUBLIC_WLD_API_BASE_URL')}/api/v1/verify/{os.getenv('NEXT_PUBLIC_WLD_APP_ID')}"

    verify_res = requests.post(verify_endpoint, json=payload)
    wld_response = verify_res.json()

    print(f"Received {verify_res.status_code} response from World ID /verify endpoint:\n", wld_response)

    if verify_res.status_code == 200:
        # This is where you should perform backend actions based on the verified credential, such as setting a user as "verified" in a database
        # For this example, we'll just return a 200 response and console.log the verified credential
        print("Credential verified! This user's nullifier hash is: ", wld_response["nullifier_hash"])
        return jsonify({"code": "success", "detail": "This action verified correctly!"})
    else:
        # This is where you should handle errors from the World ID /verify endpoint. Usually these errors are due to an invalid credential or a credential that has already been used.
        # For this example, we'll just return the error code and detail from the World ID /verify endpoint.
        return jsonify({"code": wld_response["code"], "detail": wld_response["detail"]}), verify_res.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
