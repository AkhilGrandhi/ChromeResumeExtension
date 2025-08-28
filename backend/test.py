import openai

# ⚠️ Paste your token here for testing only
api_key = "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"

# Create a client with the new API
client = openai.OpenAI(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # or "gpt-4"
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ]
    )

    print("✅ API call successful.")
    print("Response:", response.choices[0].message.content)

except openai.AuthenticationError:
    print("❌ Invalid API key.")
except Exception as e:
    print(f"⚠️ Error: {e}")
