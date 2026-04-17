import anthropic
import os
import sys
import subprocess

# Get YouTube URL from command line
if len(sys.argv) < 2:
    print("Usage: python3.11 pipeline.py YOUTUBE_URL")
    sys.exit(1)

url = sys.argv[1]
video_id = url.split("v=")[-1].split("/")[-1].split("?")[0]

print(f"Processing {video_id}...")

# Step 1 - Download transcript, thumbnail, metadata
subprocess.run([
    "python3.11", "-m", "yt_dlp",
    "--write-auto-sub", "--sub-format", "vtt",
    "--write-thumbnail", "--write-info-json",
    "--convert-thumbnails", "jpg",
    "--skip-download",
    "-o", f"{video_id}.%(ext)s",
    url
])

print("Downloaded assets.")

# Step 2 - Extract screenshots at chapters
import json
with open(f"{video_id}.info.json", "r") as f:
    info = json.load(f)

chapters = info.get("chapters", [])
if chapters:
    import os
    os.makedirs("screenshots", exist_ok=True)
    for chapter in chapters:
        t = int(chapter["start_time"])
        subprocess.run([
            "ffmpeg", "-ss", str(t), "-i", f"{video_id}.webm",
            "-frames:v", "1", "-q:v", "2",
            f"screenshots/screenshot_{t}s.jpg", "-y"
        ], stderr=subprocess.DEVNULL)
    print(f"Extracted {len(chapters)} screenshots.")

# Step 3 - Read transcript
vtt_file = f"{video_id}.en.vtt"
if not os.path.exists(vtt_file):
    vtt_file = f"{video_id}.vtt"
with open(vtt_file, "r") as f:
    transcript = f.read()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Step 4 - Generate article
print("Generating article...")
msg = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=4000,
    messages=[{"role": "user", "content": f"Convert this YouTube transcript into a long-form article with H2 headers for each chapter, intro, and conclusion:\n\n{transcript}"}]
)
article = msg.content[0].text
with open("article.md", "w") as f:
    f.write(article)
print("Article saved.")

# Step 5 - Generate social posts
print("Generating social posts...")
msg2 = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1000,
    messages=[{"role": "user", "content": f"""Write 3 variations of a single social post for X/Mastodon/Bluesky and 2 LinkedIn posts.

X/MASTODON/BLUESKY rules:
- Max 280 characters
- Punchy, technical audience
- End with [LINK]
- No hashtags
- Label: X VARIATION 1, X VARIATION 2, X VARIATION 3

LINKEDIN rules:
- 3-5 sentences
- Business/professional/outcome oriented
- Focus on what the reader gains or can achieve
- End with [LINK]
- Label: LINKEDIN 1, LINKEDIN 2

Article:
{article}"""}]
)
with open("social_posts.md", "w") as f:
    f.write(msg2.content[0].text)
print("Social posts saved.")

print("\nAll done! Files: article.md, social_posts.md, screenshots/")
