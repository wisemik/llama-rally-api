
## API Endpoints

### POST /send_message_galadriel

Sends a message to the Ethereum smart contract and retrieves the contract's response.

#### Request

- **URL**: `/send_message_galadriel`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body**:
  ```json
  {
    "message": "Your message to the contract"
  }
  ```

#### Response

- **Success**: `200 OK`
  ```json
  {
    "response": "Contract response"
  }
  ```
- **Error**: `400 Bad Request` if the message is missing
  ```json
  {
    "error": "Message is required"
  }
  ```

### POST /openai_response

Gets a response from OpenAI's completion model.

#### Request

- **URL**: `/openai_response`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body**:
  ```json
  {
    "message": "Your message to OpenAI"
  }
  ```

#### Response

- **Success**: `200 OK`
  ```json
  {
    "message": "Your message to OpenAI",
    "openai_response": "OpenAI response"
  }
  ```
- **Error**: `400 Bad Request` if the message is missing
  ```json
  {
    "error": "Message is required"
  }
  ```

### POST /claude_response

Gets a response from Anthropic's Claude model.

#### Request

- **URL**: `/claude_response`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body**:
  ```json
  {
    "message": "Your message to Claude"
  }
  ```

#### Response

- **Success**: `200 OK`
  ```json
  {
    "message": "Your message to Claude",
    "claude_response": "Claude response"
  }
  ```
- **Error**: `400 Bad Request` if the message is missing
  ```json
  {
    "error": "Message is required"
  }
  ```

### POST /criticize_user_request

Sends a message to the Ethereum smart contract to criticize and score a user prompt.

#### Request

- **URL**: `/criticize_user_request`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body**:
  ```json
  {
    "prompt": "User's prompt to be evaluated"
  }
  ```

#### Response

- **Success**: `200 OK`
  ```json
  {
    "score": 7,
    "description": "Explanation of the score"
  }
  ```
- **Error**: `400 Bad Request` if the prompt is missing
  ```json
  {
    "error": "Prompt is required"
  }
  ```
