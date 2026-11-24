#!/usr/bin/env python3
"""Fetch Muse's Discord news/interest posts and rebuild feed.json.
Requires env DISCORD_TOKEN (bot token; with or without the "Bot " prefix).
Standard library only.
"""
import json, os, re, sys, urllib.request

API = "https://discord.com/api/v10"
BOT_ID = "1572395084991959203"
CHANNELS = [
    ("ニュース", "生成AI", "1572816371098722498"),
    ("ニュース", "AIコーディング", "1572817934848368660"),
    ("ニュース", "Python", "1572816374428991570"),
    ("ニュース", "OSS", "1572816380615467114"),
    ("ニュース", "データ圧縮", "1572816383111335946"),
    ("ニュース", "組込", "1572816388500885585"),
    ("ニュース", "研究・論文", "1572817937717403698"),
    ("ニュース", "Steam", "1572816391361405078"),
    ("興味", "新技術", "1572818611192733787"),
    ("興味", "新サービス", "1572818613881282583"),
    ("興味", "開発者ツール", "1572818617391915080"),
    ("興味", "AIエージェント", "1572818619887526049"),
]
LIMIT_PER_CHANNEL = 8
MAX_ITEMS = 60

def fetch_messages(channel_id, token):
    req = urllib.request.Request(
        f"{API}/channels/{channel_id}/messages?limit={LIMIT_PER_CHANNEL}",
        headers={"Authorization": token, "User-Agent": "muse-feed-bot"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)

def parse_message(content):
    urls = re.findall(r"https?://[^\s\)]+", content)
    url = urls[-1].rstrip("。、") if urls else ""
    body = re.sub(r"出典[:：]\s*https?://\S+", "", content)
    body = re.sub(r"https?://\S+", "", body).strip()
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if not lines:
        return None
    title = re.sub(r"^[📰✨🔥💡🧩\s]+", "", lines[0])
    bracket = re.match(r"^【([^】]+)】\s*(.*)$", title)
    if bracket and bracket.group(2).strip():
        title = bracket.group(2).strip()
    elif bracket:
        title = bracket.group(1).strip()
    summary = " ".join(lines[1:])[:300]
    return title, summary, url

def main():
    token = os.environ.get("DISCORD_TOKEN", "").strip()
    if not token:
        print("DISCORD_TOKEN is not set", file=sys.stderr)
        return 1
    if not token.startswith("Bot "):
        token = "Bot " + token
    items = []
    for section, theme, channel_id in CHANNELS:
        try:
            messages = fetch_messages(channel_id, token)
        except Exception as exc:
            print(f"warning: fetch failed for {theme}: {exc}", file=sys.stderr)
            continue
        for msg in messages:
            if msg.get("author", {}).get("id") != BOT_ID:
                continue
            content = (msg.get("content") or "").strip()
            if not content:
                continue
            parsed = parse_message(content)
            if not parsed:
                continue
            title, summary, url = parsed
            if not title:
                continue
            items.append({"section": section, "theme": theme, "title": title,
                          "summary": summary, "url": url, "date": msg.get("timestamp", "")})
    items.sort(key=lambda x: x["date"], reverse=True)
    items = items[:MAX_ITEMS]
    if not items:
        print("no items fetched; leaving feed.json unchanged", file=sys.stderr)
        return 1
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "feed.json")
    data = {"generated_at": items[0]["date"], "items": items}
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"wrote {len(items)} items to {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
