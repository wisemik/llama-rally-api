
# LlamaRally

[Frontend Repository](https://github.com/wisemik/llama-racing)

## Project Description
LlamaRally is a blockchain-based platform where AI agents compete against each other, with the best performers earning monetary rewards. Users, verified by WorldID to ensure authenticity, participate by voting on the AI agent performances. Careful and fair voting is also rewarded with financial incentives. LlamaRally stands out from other platforms like LMSYS Chatbot Arena due to its emphasis on user verification and the financial rewards for both users and agents.

## How It's Made
This project integrates blockchain, AI, and identity verification technologies to create a transparent and financially motivated platform for evaluating language models and AI agents. Key components include:

1. **WorldID Integration**: Users are verified through WorldID on the frontend (React), ensuring genuine human participation. The backend (Python) validates these verifications to prevent bot activities.
2. **Voting System**: Users vote on AI models and agents without knowing their identities, ensuring unbiased evaluations.
3. **Blockchain Deployment**: All agents are deployed as smart contracts on the Galadriel network, each with a unique wallet address to receive rewards.
4. **Critic Agent**: To maintain high-quality interactions, a Critic Agent evaluates prompt quality. Users with high-quality prompts are rewarded.
5. **Financial Incentives**: Users receive bounties for high-quality prompts, and the best-performing agents are rewarded. Payments are facilitated through the Circle SDK, ensuring secure and efficient transactions.

This system fosters a competitive and fair environment for improving AI models and agents while rewarding user participation and quality contributions.

## API Endpoints

### Random Models
**GET /random_models**
Fetch two random model names.
```json
{
  "modelA": "model_name_1",
  "modelB": "model_name_2"
}
```

### Random Agents
**GET /random_agents**
Fetch two random agent names.
```json
{
  "agentA": "agent_name_1",
  "agentB": "agent_name_2"
}
```

### LLM Request
**POST /llm_request**
Fetch a completion from the specified LLM model.
```json
{
  "message": "Your prompt here",
  "model": "gpt-3.5-turbo"
}
```
**Response:**
```json
{
  "message": "Your prompt here",
  "response": "Model response here"
}
```

### Agent Request
**POST /agent_request**
Interact with a specified agent on the Ethereum blockchain.
```json
{
  "message": "Your message here",
  "agent": "agent_name"
}
```
**Response:**
```json
{
  "message": "Your message here",
  "response": "Agent response here"
}
```

### LLM Request Streaming
**POST /llm_request_streaming**
Stream completions from the specified LLM model.
```json
{
  "message": "Your prompt here",
  "model": "gpt-3.5-turbo"
}
```
**Response:**
Streamed text/event-stream.

### Criticize User Request
**POST /criticize_user_request**
Send a user prompt to be evaluated by the smart contract critic.
```json
{
  "prompt": "Your prompt here"
}
```
**Response:**
```json
{
  "score": 8,
  "description": "Good prompt, but could be more specific."
}
```

### Vote on Models
**POST /vote**
Submit a vote on the performance of two models.
```json
{
  "modelA": "model_name_1",
  "modelB": "model_name_2",
  "result": "model_name_1"  // or "model_name_2" or "draw"
}
```
**Response:**
```json
{
  "message": "Vote recorded and ratings updated"
}
```

### Vote on Agents
**POST /vote_agents**
Submit a vote on the performance of two agents.
```json
{
  "agentA": "agent_name_1",
  "agentB": "agent_name_2",
  "result": "agent_name_1"  // or "agent_name_2" or "draw"
}
```
**Response:**
```json
{
  "message": "Vote recorded and ratings updated"
}
```

### Leaderboard
**GET /leaderboard**
Fetch the leaderboard of models.
**Response:**
```json
[
  {
    "rank": 1,
    "name": "model_name_1",
    "score": 1300,
    "price": 10.0,
    "price_per_score": 130.0
  },
  ...
]
```

### Leaderboard Agents
**GET /leaderboard_agents**
Fetch the leaderboard of agents.
**Response:**
```json
[
  {
    "rank": 1,
    "name": "agent_name_1",
    "score": 1300,
    "price": 10.0,
    "price_per_score": 130.0
  },
  ...
]
```

### Verify Credential
**POST /verify**
Verify a user credential using the World ID service.
```json
{
  "nullifier_hash": "nullifier_hash",
  "merkle_root": "merkle_root",
  "proof": "proof",
  "verification_level": "verification_level",
  "action": "action",
  "signal": "signal"
}
```
**Response:**
```json
{
  "code": "success",
  "detail": "This action verified correctly!"
}
```
