
# API Endpoints

## Random Models

**GET /random_models**

Fetch two random model names.

**Response:**
```json
{
  "modelA": "model_name_1",
  "modelB": "model_name_2"
}
```

## Random Agents

**GET /random_agents**

Fetch two random agent names.

**Response:**
```json
{
  "agentA": "agent_name_1",
  "agentB": "agent_name_2"
}
```

## LLM Request

**POST /llm_request**

Fetch a completion from the specified LLM model.

**Request:**
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

## Agent Request

**POST /agent_request**

Interact with a specified agent on the Ethereum blockchain.

**Request:**
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

## LLM Request Streaming

**POST /llm_request_streaming**

Stream completions from the specified LLM model.

**Request:**
```json
{
  "message": "Your prompt here",
  "model": "gpt-3.5-turbo"
}
```

**Response:**
Streamed text/event-stream.

## Criticize User Request

**POST /criticize_user_request**

Send a user prompt to be evaluated by the smart contract critic.

**Request:**
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

## Vote on Models

**POST /vote**

Submit a vote on the performance of two models.

**Request:**
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

## Vote on Agents

**POST /vote_agents**

Submit a vote on the performance of two agents.

**Request:**
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

## Leaderboard

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

## Leaderboard Agents

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

## Verify Credential

**POST /verify**

Verify a user credential using the World ID service.

**Request:**
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
