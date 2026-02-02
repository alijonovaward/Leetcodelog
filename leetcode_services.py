import requests
import json
from datetime import datetime, timezone

def is_solve_today(username):
    url = "https://leetcode.com/graphql"
    query = """
    query recentSubmissions($username: String!) {
      recentSubmissionList(username: $username) {
        timestamp
        statusDisplay
      }
    }
    """
    variables = {"username": username}
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    subs = res.json()["data"]["recentSubmissionList"]

    today = datetime.now(timezone.utc).date()
    for sub in subs:
        ts = datetime.fromtimestamp(int(sub["timestamp"]), timezone.utc).date()
        if ts == today and sub["statusDisplay"] == "Accepted":
            return True
    return False


def get_count_solved_problems(username):
    url = "https://leetcode.com/graphql"
    query = """
    query getUserProfile($username: String!) {
      matchedUser(username: $username) {
        submitStats {
          acSubmissionNum {
            difficulty
            count
          }
        }
      }
    }
    """
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.post(url, json={"query": query, "variables": {"username": username}}, headers=headers)
    return res.json()
