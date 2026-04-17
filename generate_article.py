import anthropic
import os

with open("VKfE5BuqlSc.en.vtt", "r") as f:
    transcript = f.read()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=4000,
    messages=[{"role": "user", "content": f"Convert this YouTube transcript into a long-form article with H2 headers for each chapter, intro, and conclusion:\n\n{transcript}"}]
)

with open("article.md", "w") as f:
    f.write(message.content[0].text)

print("Done! Article saved to article.md")
