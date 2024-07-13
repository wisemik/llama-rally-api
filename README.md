# LlamaRally API Server

This project is a Flask-based API server that interfaces with various Language Learning Models (LLMs) including OpenAI's GPT models and Anthropic's Claude models. It also includes integration with an Ethereum smart contract for message processing and a SQLite database for model scoring and leaderboard functionality.

## Features

- Interaction with multiple LLM models
- Streaming responses from LLMs
- Random model selection
- User prompt evaluation via Ethereum smart contract
- Model voting system with ELO rating
- Leaderboard for model performance

## API Endpoints

### 1. Get Random Models

- **URL:** `/random_models`
- **Method:** `GET`
- **Description:** Returns two randomly selected LLM models.
- **Response:** JSON object with `modelA` and `modelB` fields.

### 2. LLM Request

- **URL:** `/llm_request`
- **Method:** `POST`
- **Description:** Sends a message to a specified LLM model and returns the response.
- **Request Body:**
  - `message`: The input message (required)
  - `model`: The LLM model to use (must be one of the supported models)
- **Response:** JSON object with `message` and `response` fields.

### 3. LLM Streaming Request

- **URL:** `/llm_request_streaming`
- **Method:** `POST`
- **Description:** Streams the response from a specified LLM model for a given input message.
- **Request Body:**
  - `message`: The input message (required)
  - `model`: The LLM model to use (optional, defaults to 'gpt-3.5-turbo')
- **Response:** Server-Sent Events (SSE) stream of the model's response.

### 4. Criticize User Request

- **URL:** `/criticize_user_request`
- **Method:** `POST`
- **Description:** Evaluates a user's prompt using an Ethereum smart contract, returning a score and description.
- **Request Body:**
  - `prompt`: The user's prompt to evaluate (required)
- **Response:** JSON object with `score` and `description` fields.

### 5. Vote

- **URL:** `/vote`
- **Method:** `POST`
- **Description:** Records a vote for a model comparison and updates ELO ratings.
- **Request Body:**
  - `modelA`: Name of the first model
  - `modelB`: Name of the second model
  - `result`: The winning model's name or 'draw'
- **Response:** Confirmation message

### 6. Leaderboard

- **URL:** `/leaderboard`
- **Method:** `GET`
- **Description:** Retrieves the current leaderboard of models based on their ELO scores.
- **Response:** JSON array of model rankings, including score and price information.
