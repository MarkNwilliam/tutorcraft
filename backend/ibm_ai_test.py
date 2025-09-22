import requests

# Step 1: Get the access token
print("Getting the access token...")
token_url = "https://iam.cloud.ibm.com/identity/token"
apikey = "0ryiZcx77E-96WINyp4_09q_lXReooFbT4-oS_lnHFua"
token_data = {
    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
    "apikey": apikey
}
token_headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

token_response = requests.post(token_url, headers=token_headers, data=token_data)

if token_response.status_code != 200:
    raise Exception("Failed to obtain access token: " + str(token_response.text))

token_info = token_response.json()
access_token = token_info["access_token"]
print("Access token obtained:", access_token)

# Step 2: Use the access token to make the request to the IBM Watson service
print("Making the request to the IBM Watson service...")
url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"

body = {
    "input": """System:
You are an intelligent AI programming assistant, utilizing a Granite code language model developed by IBM. Your primary function is to assist users in programming tasks, including code generation, code explanation, code fixing, generating unit tests, generating documentation, application modernization, vulnerability detection, function calling, code translation, and all sorts of other software engineering tasks.

Answer:
""",
    "parameters": {
        "decoding_method": "greedy",
        "max_new_tokens": 900,
        "min_new_tokens": 0,
        "repetition_penalty": 1
    },
    "model_id": "ibm/granite-20b-code-instruct",
    "project_id": "204189a7-217b-455b-8be2-7ee33ff73c5c"
}

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}"
}

response = requests.post(
    url,
    headers=headers,
    json=body
)

if response.status_code != 200:
    raise Exception("Non-200 response: " + str(response.text))

data = response.json()

print("Response from IBM Watson service:")
print(data)