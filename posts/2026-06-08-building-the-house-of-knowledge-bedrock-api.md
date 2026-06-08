---
title: "Building The House of Knowledge: The Bedrock Converse API"
date: 2026-06-08
tags: [ai, RAG, House of Knowledge]
description: "Part 2 of a series on building a real RAG system with real data - 
The Bedrock Converse API.  A bit technical."
image: /images/posts/bedrock.png
---

# Building the House of Knowledge: The Bedrock Converse API

*Part 2 of the House of Knowledge series. [Part 1 is here.](https://jamielab.uk/blog/building-the-house-of-knowledge-RAG-on-a-budget/)*

---

The last post was about building a RAG system on an underpowered NUC. It skipped over the AWS bits, mentioned Bedrock and the Converse API in passing and moved on. 

This post is the bit I glossed over. It's more focused on code than Part 1, and it's drier as a result. I'll try to keep it useful.

---

## Why Bedrock at all

It's not the obvious choice for a home project. The honest answer is that I already use AWS for work. IAM, boto3, region config: none of is was new pain. Starting from zero on a different platform would have been slower, and this was supposed to be a side project, not a rabbit hole.

Beyond familiarity, the other useful thing is model variety. Nova Lite, Claude Haiku, Llama, Mistral: all accessible from the same SDK, pay-per-token, no subscription. For a project where part of the point is comparing models, that's useful. I'm not locked into one provider's family of models, and I'm not paying a standing charge to find out whether the cheaper option is good enough.

Getting started is also fairly easy. A `boto3.client("bedrock-runtime")` call, an IAM user with `AmazonBedrockFullAccess`, and a region that has the models I want. That's it. No separate SDK, no API keys beyond what IAM already handles.

One thing to check: not all models are available in all regions. The project uses `eu-west-2` (London); Nova Lite and Haiku 4.5 are both available there. It's worth checking in the Bedrock console before assuming a model is accessible where you're running.

To be clear, none of this is a recommendation that everyone should use Bedrock. If you're already set up with OpenAI or Anthropic directly, then the ease of using AWS might not be a concern. This is just what made sense from where I started.

## The problem

The early versions of this project called `invoke_model` directly. This is the low-level Bedrock API: you serialise a JSON body, POST it, and parse the response. Simple enough, until you want to use two different model families.

Here's what calling Nova Lite looked like:

```python
body = {
    "messages": [
        {"role": "user", "content": [{"text": user_message}]},
    ],
    "system": [{"text": system_prompt}],
    "inferenceConfig": {"maxTokens": 2048, "temperature": 0.3},
}
response = client.invoke_model(modelId=model_id, body=json.dumps(body))
result = json.loads(response["body"].read())
text = result["output"]["message"]["content"][0]["text"]
input_tokens = result["usage"]["inputTokens"]  # camelCase
```

And here's what calling Haiku looked like:

```python
body = {
    "messages": [
        {"role": "user", "content": [{"type": "text", "text": user_message}]},
    ],
    "system": [{"type": "text", "text": system_prompt}],
    "max_tokens": 2048,
    "anthropic_version": "bedrock-2023-05-31",
}
response = client.invoke_model(modelId=model_id, body=json.dumps(body))
result = json.loads(response["body"].read())
text = result["content"][0]["text"]            # different path
input_tokens = result["usage"]["input_tokens"] # snake_case
```

Different content block shape, response path and token key casing. I ended up with two different implementations, one for each model family.

If the goal is to compare models, this is annoying. Adding a third model means writing a third client. The integration layer grows with every model you try, which is exactly the wrong way round when the whole point is to swap freely.

---

## The Converse API

The Converse API is `client.converse()` instead of `client.invoke_model()`. AWS introduced it to put a unified interface over all Bedrock-hosted generation models. The same request shape, the same response structure, regardless of what's running underneath.

```python
response = client.converse(
    modelId=model_id,  # the only thing that changes
    system=[{"text": system_prompt}],
    messages=[
        {"role": "user", "content": [{"text": user_message}]},
    ],
    inferenceConfig={"maxTokens": 2048},
)

message = response["output"]["message"]
text = message["content"][0]["text"]
input_tokens = response["usage"]["inputTokens"]
output_tokens = response["usage"]["outputTokens"]
```

To switch from Nova Lite to Haiku 4.5, you change `modelId`. Nothing else. The project wires this through an environment variable, `BEDROCK_MODEL_ID`, defaulting to `amazon.nova-lite-v1:0`. The Streamlit app passes it to `BedrockClient.__init__`. That's the entire model-switching mechanism.

The `BedrockClient` class in the project is deliberately thin:

```python
class BedrockClient:
    """Bedrock Runtime client using the unified Converse API."""

    def __init__(self, model_id: str, region: str):
        self.model_id = model_id
        self._client = boto3.client("bedrock-runtime", region_name=region)

    def invoke(self, system_prompt: str, user_message: str) -> InvokeResult:
        response = self._client.converse(
            modelId=self.model_id,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_message}]}],
            inferenceConfig={"maxTokens": 2048},
        )
        message = response["output"]["message"]
        input_tokens, output_tokens = _usage_tokens(response)
        return InvokeResult(
            text=_extract_text(message["content"]),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
```

Worth noting what Converse doesn't do: it unifies the interface, not the capabilities. You can't get extended thinking out of Nova Lite by pointing a different `modelId` at it. If you need model-specific parameters that fall outside the unified spec, they go in `additionalModelRequestFields`. That escape hatch exists, but I haven't needed it yet.

---

## Conversation history

The `messages` array supports proper multi-turn conversations: alternating `user` and `assistant` blocks, as many turns deep as you like (within the model's context window). The current implementation doesn't use this properly.

What it does instead is serialise recent history into the user message as plain text:

```python
window = history[-self.chat_history_window:]
for msg in window:
    role = msg["role"].capitalize()
    history_text += f"{role}: {msg['content']}\n"

user_message = f"Conversation so far:\n{history_text}\nQuestion: {message}"
```

It works. It's also a bit of a hack; the model sees history as embedded context within a single turn rather than as a real conversation.

The difference does actually matter. Models are trained on conversational data with explicit role structure. When you pass history as proper `messages` turns, the model understands natively which content is its own prior output and which is the user's input. Attention works the way it's supposed to. Follow-up questions like "what else do you know about him?" or "expand on the last point" get resolved correctly because the model can trace "last point" back to a specific assistant turn.

With the plain-text approach, the model has to parse your formatting to infer turn boundaries, and the signal it gets about who said what is weaker. For simple single-turn queries it makes no practical difference. For a lore assistant where half the questions are follow-ups ("what happened after that?", "you mentioned the Thornwood earlier, what's the connection?"), it does.

The right implementation passes history as proper `messages` turns:

```python
messages = []
for msg in history[-self.chat_history_window:]:
    messages.append({
        "role": msg["role"],
        "content": [{"text": msg["content"]}]
    })
messages.append({"role": "user", "content": [{"text": user_message}]})
```

The window is capped at 8 messages; unbounded history would balloon token costs when I'm trying to be cheap. That constraint isn't going anwyeher but I fixing the history serialisation is on my list.

---

## Tool use

Converse also has a unified interface for function calling (`toolConfig`, `toolUse`, `toolResult`) that works the same way regardless of model. The project uses it for the agentic retrieval mode, where the model decides what to search for rather than getting pre-retrieved context handed to it.

I'll leave the details for the agentic post, but the short version: having a single tool contract that works across models is what makes swapping between Nova Lite and Haiku in that mode straightforward. Without Converse, it'd be two more client implementations.

---

## What it doesn't cover

A few things worth knowing about:

**Embeddings.** BGE-M3 runs locally on the NUC and has nothing to do with Bedrock. The embedder never touches AWS. Converse is generation-only, but that's not a constraint here.

**Streaming.** `converse_stream()` exists if you want token-by-token output. The project doesn't use it; full responses are fast enough that it's not noticeable at the table. It would make the app feel more responsive though. That's on the list.

**Model-specific features.** Anything outside the unified spec lives in `additionalModelRequestFields`. Haven't needed it, but it's there.

---

## What's next

The API layer is sorted: one client, two models, a config flag to switch between them. What's still missing is accessibility. The app runs on a NUC in my home office. Fine when you're on my wifi, useless from a friend's place with a map spread across the table.

The next post is about fixing that: making a locally-running Streamlit app accessible from anywhere.  Without a static IP, without port forwarding, and without spending more money. The answer is Cloudflare Tunnel, and it's tidier than it sounds.

---
