"""Prepare and deliver notifications for newly ranked public models."""

import json
import os
import subprocess
import urllib.request
from pathlib import Path

SNAPSHOT = Path("fineprint/web/lib/market-data.json")
LEADERBOARD_URL = "https://fineprint.flexprice.io/#leaderboard"


def new_models(previous: dict, current: dict) -> list[dict]:
    old_ids = {row["id"] for row in previous.get("rows", [])}
    return [row for row in current.get("rows", []) if row["id"] not in old_ids]


def notification(previous: dict, current: dict, test: bool = False) -> tuple[int, str]:
    added = new_models(previous, current)
    if added:
        names = ", ".join(
            f"{str(row['label']).replace(chr(10), ' ')} (#{row['rank']}, Index {row['overall']:.1f})"
            for row in added[:8]
        )
        remainder = f" and {len(added) - 8} more" if len(added) > 8 else ""
        message = f"FinePrint found {len(added)} new ranked model(s): {names}{remainder}. View: {LEADERBOARD_URL}"
    else:
        leader = current["rows"][0]["label"] if current.get("rows") else "none"
        message = f"FinePrint ranking refresh test: {current['n_ranked']} models scored, current leader {leader}."
    if test:
        message = "Slack delivery test · " + message
    return len(added), message


def post_slack(webhook_url: str, message: str) -> None:
    if not webhook_url:
        raise ValueError("Set the repository secret SLACK_WEBHOOK_URL to enable ranking notifications.")
    request = urllib.request.Request(
        webhook_url,
        data=json.dumps({"text": message}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"Slack webhook returned HTTP {response.status}")


def main() -> None:
    current = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    previous_result = subprocess.run(
        ["git", "show", f"HEAD:{SNAPSHOT}"], capture_output=True, text=True, check=False
    )
    previous = json.loads(previous_result.stdout) if previous_result.returncode == 0 else current
    test = os.getenv("TEST_SLACK") == "true"
    count, message = notification(previous, current, test=test)
    output = os.getenv("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"message={message}\nnew_count={count}\n")
    if count or test:
        post_slack(os.getenv("SLACK_WEBHOOK_URL", ""), message)
        print("Slack ranking notification delivered.")
    else:
        print("No new ranked models; no Slack notification needed.")


if __name__ == "__main__":
    main()
