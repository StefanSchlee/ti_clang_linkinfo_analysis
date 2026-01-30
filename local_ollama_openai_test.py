from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required but ignored by Ollama
)

response = client.chat.completions.create(
    model="gemma3:1b-it-qat",
    messages=[{"role": "user", "content": "Explain HTTP methods in one sentence."}],
)

print(response.choices[0].message.content)
