import anthropic
import os

with open("article.md", "r") as f:
    article = f.read()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1000,
    messages=[{"role": "user", "content": f"""Write 3 variations of a single social media post for X/Mastodon/Bluesky based on this article.
Rules:
- Max 280 characters each
- Punchy, technical audience
- End with [LINK] as placeholder for the article URL
- No hashtags
- Label each: VARIATION 1, VARIATION 2, VARIATION 3

Article:
{article}"""}]
)

with open("social_posts.md", "w") as f:
    f.write(message.content[0].text)

print("Done! Social posts saved to social_posts.md")
