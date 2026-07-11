#!/usr/bin/env python3
"""
Deep post-by-post analysis of @a.storyof.two's 36 posts.
Focuses on: caption anatomy, hook structure, music correlation, what worked/failed and why.
"""

import json
import os
import anthropic
from pathlib import Path

ROOT = Path(__file__).parent.parent
POSTS_FILE = ROOT / "corpus/posts/2026-05-09-posts.json"
OUTPUT_FILE = ROOT / "output/reports/2026-05-09-deep-post-analysis.md"

def load_posts():
    with open(POSTS_FILE) as f:
        posts = json.load(f)
    # Sort by likes descending
    return sorted(posts, key=lambda p: p.get("likesCount", 0), reverse=True)

def format_posts_for_analysis(posts):
    lines = []
    for i, p in enumerate(posts, 1):
        views = p.get("videoViewCount") or 0
        plays = p.get("videoPlayCount") or 0
        likes = p.get("likesCount", 0)
        comments = p.get("commentsCount", 0)
        ptype = p.get("type", "")
        caption = (p.get("caption") or "").strip()
        hashtags = p.get("hashtags") or []
        music = p.get("musicInfo") or {}
        artist = music.get("artist_name", "")
        song = music.get("song_name", "")
        is_original = music.get("uses_original_audio", False)
        is_muted = music.get("should_mute_audio", False)
        timestamp = p.get("timestamp", "")[:10]
        url = p.get("url", "")

        if is_muted:
            audio_desc = "MUTED/unavailable"
        elif is_original:
            audio_desc = f"ORIGINAL audio by creator — {song}"
        else:
            audio_desc = f'"{song}" by {artist}'

        lines.append(f"""
--- POST #{i} | {timestamp} ---
URL: {url}
Type: {ptype}
Performance: {likes:,} likes | {views:,} views | {plays:,} plays | {comments} comments
Caption: {caption[:500]}
Hashtags: {hashtags}
Audio: {audio_desc}
""")
    return "\n".join(lines)

def run_analysis(client, posts_text, section_title, prompt):
    print(f"\n⏳ Running: {section_title}")
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": f"""You are analysing @a.storyof.two — an Indian married couple's Instagram channel.
Creator: Anchal Raina Sharma. Subject: Himanshu + Anchal.
Channel voice: Hinglish wit + emotional warmth. Best posts: chaotic wife energy, husband POV, desi relatability.

Here are all 36 posts sorted by likes (highest first):

{posts_text}

---
{prompt}
"""
        }]
    )
    return message.content[0].text

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    client = anthropic.Anthropic(api_key=api_key)
    posts = load_posts()
    posts_text = format_posts_for_analysis(posts)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write("# @a.storyof.two — Deep Post Analysis: Hook, Caption & Music Autopsy\n")
        f.write("# Generated: 2026-05-09 | Model: Claude Opus | Posts analysed: 36\n\n---\n\n")

    def write_section(title, content):
        with open(OUTPUT_FILE, "a") as f:
            f.write(f"## {title}\n\n{content}\n\n---\n\n")

    # Section 1: Hook + Caption anatomy of every post
    s1 = run_analysis(client, posts_text, "Hook & Caption Anatomy",
        """TASK: For EVERY post (all 36), analyse the CAPTION ANATOMY with brutal precision.

Format each post as:

### [Rank]. [First 6 words of caption] — [likes] likes / [views] views

**Hook type**: [Conflict opener / Observation / Question / Statement / Lyric / Generic / Empty]
**Language**: [Hinglish / Hindi / English / Mixed]
**Voice**: [Voice 1: Vibe Girl (punchy, first-person, ironic) / Voice 2: Poet (soft, third-person, lyrical) / Voice 3: Generic (no identity)]
**Caption length**: [One line / 2-3 lines / Long form / Keyword dump]
**The actual hook** (first thing viewer reads): [quote it exactly]
**Punchline** (if any): [quote it]
**What's working**: [one sentence]
**What's killing it**: [one sentence — be specific, no fluff]
**Tags/hashtag strategy**: [Clean (none) / Brackets [] / Hashtags # / Both — and whether it helped or hurt]

Do this for all 36 posts. Be ruthless. This is a private strategy doc, not feedback for Anchal.""")
    write_section("Hook & Caption Anatomy — All 36 Posts", s1)

    # Section 2: Music correlation analysis
    s2 = run_analysis(client, posts_text, "Music Correlation Analysis",
        """TASK: Analyse the MUSIC/AUDIO choices across all posts and their correlation with performance.

Answer these questions with specific post evidence:

1. ORIGINAL AUDIO vs TRENDING AUDIO vs MUTED — What does the data show? Give exact numbers (avg likes per category).

2. Which SPECIFIC audio choices correlated with the highest views? Which correlated with failure?

3. The Lata Mangeshkar + Charlie Puth mix ("me threatening to leave") got 1.35M views with ORIGINAL audio.
   What does this tell us about Anchal's audio strategy? Is she underusing this lever?

4. Three posts used "Bairan" by Banjaare. What did each post get? What does that tell us about audio reuse?

5. What is the AUDIO PATTERN in the top 5 posts vs bottom 5 posts?

6. Give a clear AUDIO SELECTION FRAMEWORK: for a chaotic wife reel, what type of audio? For a soft love reel? For a Himanshu POV?

Be specific. Quote post numbers and exact metrics.""")
    write_section("Music & Audio Correlation Analysis", s2)

    # Section 3: Top 5 deep dives — what exactly worked
    top5_posts = format_posts_for_analysis(posts[:5])
    s3 = run_analysis(client, top5_posts, "Top 5 Deep Dives",
        """TASK: Deep dive into each of the top 5 posts. These are the channel's best performers.

For EACH post, answer:

**THE EXACT HOOK MECHANISM** — What is the first thing a viewer's brain processes? What emotion does it trigger in the first 2 seconds of reading the caption? Why does that emotion stop the scroll?

**THE SHARE/FORWARD TRIGGER** — Why would someone DM this to their partner? What is the specific sentence or idea they're forwarding? ("babe this is literally you" — quote what line)

**THE REPLICATION FORMULA** — If Anchal wanted to make 5 more posts with this EXACT formula, what are the 3 rules she must follow? Be specific enough to use as a brief.

**WHAT ALMOST WENT WRONG** — Is there anything about this post that got lucky? Audio choice, timing, thumbnail moment? What if she'd captioned it differently?

**THE MISSED CEILING** — Given the hook, could this have been even bigger? What one thing, if changed, would have pushed it from 140K likes to 300K?

Go post by post. No generalities.""")
    write_section("Top 5 Posts — Exact Anatomy of What Worked", s3)

    # Section 4: Bottom 5 + "Good idea, bad execution" posts
    bottom_posts = posts[-10:]  # last 10 (worst performers)
    bottom_text = format_posts_for_analysis(bottom_posts)

    # Also identify mid-performers with good concepts
    mid_posts = [p for p in posts if 100 < p.get("likesCount", 0) < 1000 and p.get("videoViewCount", 0) > 10000]
    mid_text = format_posts_for_analysis(mid_posts[:8])

    s4 = run_analysis(client, bottom_text + "\n\n--- ALSO EXAMINE THESE MID-PERFORMERS WITH GOOD CONCEPTS ---\n\n" + mid_text,
        "Failure Autopsy",
        """TASK: Diagnose the failures AND the "good idea, bad execution" posts.

For the BOTTOM 10 posts:
For each one, give:
- **Root cause of failure** (pick ONE: wrong audio / generic caption / wrong format / no hook / keyword dump / wrong language register)
- **The one change that would have saved it** — be specific ("Replace 'love found me softly' with..." / "Cut caption to one line: ...")
- **Salvageable?** Yes/No — if yes, could this concept be re-shot and posted again?

For the MID-PERFORMERS (good views, low likes ratio or good concept that underdelivered):
- **Why did the views not convert to likes?** (hook got clicks, content didn't deliver payoff?)
- **What specifically was the gap** between the concept and the execution?

Also answer: Is there a POST in the bottom 10 that had a genuinely GREAT idea but failed on execution? Which one, and what's the version that would have gone viral?

Name specific posts by their caption opening. No vague advice.""")
    write_section("Failure Autopsy — What Went Wrong and How to Fix It", s4)

    # Section 5: The replication playbook
    s5 = run_analysis(client, posts_text, "Replication Playbook",
        """TASK: Build the REPLICATION PLAYBOOK — a concrete brief that Anchal can use for her next 10 posts.

Based on everything in the 36 posts, give:

**THE VIRAL CAPTION FORMULA** (based on the top performers):
- Exact structure: [what goes in line 1 / line 2 / brackets vs no brackets]
- Language register: [which Hinglish phrases, which constructs hit]
- Length rule: [specific word count or line count]
- Punchline rule: [where does the funny/emotional payoff land?]

**THE 3 CAPTION ARCHETYPES THAT WORK** (with a template for each):
Template means: literally "______ to ______" with blanks to fill in.

**THE 3 CAPTION PATTERNS THAT FAIL** (with specific examples from the corpus):
Why each fails. What to do instead.

**THE 5 POSTS SHE SHOULD MAKE NEXT** — based on what the data is telling her:
For each: hook idea (one line), audio type to use, caption voice, estimated performance vs channel average.

**THE ONE THING** she is consistently getting wrong that is costing her the most reach.
Name it. One sentence.""")
    write_section("The Replication Playbook — Next 10 Posts Brief", s5)
    print(f"\n✅ Deep analysis written to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
