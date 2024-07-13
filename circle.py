import dotenv

dotenv.load_dotenv()

import requests
import os
import uuid

from entity_secret import generate_entity_secret


url = "https://api.circle.com/v1/w3s/developer/transactions/transfer"

def create_transfer(amount: str, destination_address: str) -> None:

    entitySecretCipherText = generate_entity_secret()

    wallet_id = "f89bfdb1-ccf3-517a-8046-12cffeb406de"
    #generate new uuid for idempotency key
    idempotencyKey = uuid.uuid4()

    print(idempotencyKey)

    payload = {
        "idempotencyKey": str(idempotencyKey),
        "entitySecretCipherText": entitySecretCipherText,
        "amounts": [amount],
        "destinationAddress": destination_address,
        "feeLevel": "HIGH",
        "tokenId": "5797fbd6-3795-519d-84ca-ec4c5f80c3b1",
        "walletId": wallet_id
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer "+os.getenv('CIRCLE_API_KEY')
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.text)

    return response.json().get('data').get('id')

create_transfer("0.1", "0xe5a0fE830657E5f473251a7d8Ff593aEb8C166a7")