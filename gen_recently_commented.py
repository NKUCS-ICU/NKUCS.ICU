# -*- coding: UTF-8 -*-

from github import Github
import json
import sys

courses_json = "./courses.json"
grade_urls = [
    "/courses/grade-1/", "/courses/grade-2/",
    "/courses/grade-3/", "/courses/grade-4/"
]
grade_dirs = ["." + x for x in grade_urls]

with open(courses_json, encoding="utf8") as f:
    courses = json.load(f)

course2file = {}
for i in range(4):
    grade_courses, grade_dir, grade_url = courses[i], grade_dirs[i], grade_urls[i]
    for course_id in grade_courses:
        course2file[course_id] = grade_url + course_id

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("plz provide a Github access token")
        exit(1)
    access_token = sys.argv[1]
    g = Github(access_token)
    repo = g.get_repo("emanual20/emanual20.github.io")

    print("# 最新评论\n")

    issues = repo.get_issues(sort="updated")
    date_courses = {}
    for issue in issues:
        if issue.comments == 0:
            continue
        title = issue.title
        if title.split()[0] not in course2file:
            continue
        date = str(issue.updated_at).split()[0]
        course_id, course_name = title.split()[:2]
        date_courses.setdefault(date, []).append("[{} {}]({})".format(
            course_id, course_name, course2file[course_id]))

    for date in sorted(date_courses.keys(), reverse=True):
        print("- {}: ".format(date) + ", ".join(sorted(date_courses[date])))
        print()
