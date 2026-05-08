from __future__ import annotations
from .base import LLMProvider, ChatMessage


class BedrockProvider(LLMProvider):
    """AWS Bedrock provider stub. Implement when migrating off Groq.

    Expected impl:
      import boto3
      client = boto3.client("bedrock-runtime", region_name=region)
      body = json.dumps({"anthropic_version": "bedrock-2023-05-31", ...})
      resp = client.invoke_model(modelId=model_id, body=body)
    """

    name = "bedrock"

    def __init__(self, region: str, model_id: str) -> None:
        self.region = region
        self.model = model_id

    async def chat(self, messages: list[ChatMessage], temperature: float = 0.2) -> str:
        raise NotImplementedError(
            "Bedrock provider not yet implemented. Switch LLM_PROVIDER=groq or implement boto3 invoke_model here."
        )
