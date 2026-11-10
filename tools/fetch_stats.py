"""Fetch public GitHub numbers for the profile card -> cache/stats.json.

Uses the GraphQL API. GITHUB_TOKEN is enough for everything public; a PAT with
read:user (secret STATS_TOKEN) also counts private contributions.
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cache" / "stats.json"
LOGIN = os.environ.get("GITHUB_REPOSITORY_OWNER", "Lainocs")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, privacy: PUBLIC,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { isFork stargazerCount pushedAt primaryLanguage { name } }
    }
  }
}
"""


def gql(after=None):
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": LOGIN, "after": after}},
        headers={"Authorization": f"bearer {TOKEN}"},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]


def main() -> None:
    user = gql()
    nodes = list(user["repositories"]["nodes"])
    page = user["repositories"]["pageInfo"]
    while page["hasNextPage"]:
        more = gql(page["endCursor"])
        nodes += more["repositories"]["nodes"]
        page = more["repositories"]["pageInfo"]

    cutoff = datetime.now(timezone.utc) - timedelta(days=3 * 365)
    langs = Counter(
        n["primaryLanguage"]["name"]
        for n in nodes
        if not n["isFork"]
        and n["primaryLanguage"]
        and datetime.fromisoformat(n["pushedAt"].replace("Z", "+00:00")) > cutoff
    )
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [
        [d["date"], LEVELS[d["contributionLevel"]], d["contributionCount"]]
        for w in cal["weeks"]
        for d in w["contributionDays"]
    ]
    stats = {
        "login": LOGIN,
        "repos": user["repositories"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in nodes if not n["isFork"]),
        "followers": user["followers"]["totalCount"],
        "since": user["createdAt"][:4],
        "contributions": cal["totalContributions"],
        "languages": [name for name, _ in langs.most_common(4)],
        "calendar": days,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(stats, indent=1) + "\n", encoding="utf-8")
    print(f"{LOGIN}: {stats['repos']} repos, {stats['contributions']} contributions, {stats['languages']}")


if __name__ == "__main__":
    main()
