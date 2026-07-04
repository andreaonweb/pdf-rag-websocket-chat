import ollama

MODEL_NAME = "llama3.2"


def call_ollama(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]
