#!/usr/bin/env python3

import json
import os
import sys
from urllib.request import Request, urlopen

from scripts.site_tools import parse_course_groups

course2file = {}
for group_route, entries in parse_course_groups().items():
    if not group_route.startswith("/courses/grade-"):
        continue
    for entry in entries:
        course2file[entry.course_id] = entry.route


def fetch_issues(access_token):
    page = 1
    while True:
        url = (
            "https://api.github.com/repos/NKUCS-ICU/NKUCS.ICU/issues"
            f"?state=all&sort=updated&per_page=100&page={page}"
        )
        request = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "NKUCS.ICU-maintenance-script",
            },
        )
        with urlopen(request, timeout=30) as response:
            issues = json.load(response)
        yield from issues
        if len(issues) < 100:
            return
        page += 1


if __name__ == "__main__":
    access_token = os.environ.get("GITHUB_TOKEN")
    if not access_token:
        print("please set GITHUB_TOKEN in the environment", file=sys.stderr)
        exit(1)
    print("# 最新评论\n")

    date_courses = {}
    for issue in fetch_issues(access_token):
        if "pull_request" in issue or issue["comments"] == 0:
            continue
        title = issue["title"]
        if title.split()[0] not in course2file:
            continue
        date = issue["updated_at"].split("T", maxsplit=1)[0]
        course_id, course_name = title.split()[:2]
        date_courses.setdefault(date, []).append("[{} {}]({})".format(
            course_id, course_name, course2file[course_id]))

    for date in sorted(date_courses.keys(), reverse=True):
        print("- {}: ".format(date) + ", ".join(sorted(date_courses[date])))
        print()
