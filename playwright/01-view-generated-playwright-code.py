import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT") # ex. https://<resource-name>.services.ai.azure.com/openai/v1
OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
MODEL_DEPLOYMENT_NAME = "gpt-6-astra"

client = OpenAI(
    base_url=OPENAI_ENDPOINT,
    api_key=OPENAI_API_KEY
)

tools = [
    {
        "type": "function",
        "name": "exec_browser",
        "description": (
            "Execute Python Playwright code in a persistent Chromium browser."
            "The following objects are already available:"
            "- page: Playwright Page"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string"
                }
            },
            "required": ["code"],
            "additionalProperties": False
        },
        "strict": True
    }
]

response = client.responses.create(
    model="gpt-6-astra",
    tools=tools,
    input=(
        "Open Wikipedia, search for 織田信長,"
        "and tell me his year of death."
        "Use exec_browser tool to operate the browser."
    )
)

for item in response.output:
    print(item)