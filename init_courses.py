import json
import os

courses_json = "./courses.json"
grade_urls = [
    "/courses/grade-1/", "/courses/grade-2/",
    "/courses/grade-3/", "/courses/grade-4/"
]
grade_dirs = ["." + x for x in grade_urls]


course_page_template = """
# {course_id} {course_name}

本课程页面暂无内容，期待大家的共同建设\\~🔥

如果你愿意提供任何信息与观点，请在下方评论区留言，网站维护者会在第一时间看到，且会酌情将其添加为本课程页面的内容⚡️
"""

entry_template = "- [{course_id} {course_name}]({grade_url}{course_id})\n"


with open(courses_json, encoding="utf8") as f:
    courses = json.load(f)

# basic data validation
assert len(courses) == 4
assert all(isinstance(x, dict) for x in courses)

for i in range(4):
    grade_courses, grade_dir, grade_url = courses[i], grade_dirs[i], grade_urls[i]
    # readme = open(os.path.join(grade_dir, "README.md"),
    #               mode="a", encoding="utf8")
    sidebar = open(os.path.join(grade_dir, "_sidebar.md"),
                   mode="a", encoding="utf8")
    for course_id in sorted(grade_courses.keys()):  # sort by course ID
        course_name = grade_courses[course_id]
        course_path = os.path.join(
            grade_dir, course_id.replace("/", "-") + ".md")
        if not os.path.exists(course_path):
            with open(course_path, "w", encoding='utf8') as page:
                page.write(course_page_template.format(
                    course_id=course_id, course_name=course_name)
                )
        # readme.write(entry_template.format(
        #     course_id=course_id, course_name=course_name, grade_url=grade_url
        # ))
        sidebar.write(entry_template.format(
            course_id=course_id, course_name=course_name, grade_url=grade_url
        ))
