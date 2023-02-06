import json
import string
import os

law_suffix = "law"
courses_json = "./courses.json"
grade_urls = [
    "/courses/grade-1/", "/courses/grade-2/",
    "/courses/grade-3/", "/courses/grade-4/"
]
# grade_urls = [
#     "/courses_maphd/1/"
# ]

grade_dirs = ["." + x for x in grade_urls]

def int_2_hashstring(param1):
    param1 = int(param1)
    ret = ""
    tmp = []
    for each in string.ascii_letters:
        tmp.append(each)
    for each in string.digits:
        tmp.append(each)
    while param1 > 0:
        ret = ret + tmp[param1 % len(tmp)]
        param1 = param1 // len(tmp)
    return ret

course_page_template = """
# {course_id} {course_name}

本课程页面暂无内容，期待大家的共同建设\\~🔥

如果你愿意提供任何信息与观点，请在下方评论区留言，网站维护者会在第一时间看到，且会酌情将其添加为本课程页面的内容⚡️
"""

entry_template = "- [{course_id} {course_name}]({grade_url}{hashed_course_id})\n"

IsSuitableForLaw = False
IsSuitableForLaw = int(input("please input a number for option: 0 for cs, 1 for law:\n"))

if IsSuitableForLaw == 1:
    courses_json = courses_json.replace("courses", "courses" + "_" + law_suffix)

with open(courses_json, encoding="utf8") as f:
    courses = json.load(f)

# basic data validation
assert len(courses) == len(grade_urls)
assert all(isinstance(x, dict) for x in courses)

for i in range(len(grade_urls)):
    # print(IsSuitableForLaw)
    if IsSuitableForLaw == 1:
        grade_dirs[i] = grade_dirs[i].replace("courses", "courses" + "_" + law_suffix)
        grade_urls[i] = grade_urls[i].replace("courses", "courses" + "_" + law_suffix)
    # print(grade_urls[i], grade_dirs[i], courses[i])

    grade_courses, grade_dir, grade_url = courses[i], grade_dirs[i], grade_urls[i]

    readme = open(os.path.join(grade_dir, "README.md"),
                  mode="a", encoding="utf8")
    sidebar = open(os.path.join(grade_dir, "_sidebar.md"),
                   mode="a", encoding="utf8")
    for course_id in sorted(grade_courses.keys()):  # sort by course ID
        course_name = grade_courses[course_id]
        # hashed_course_id = int_2_hashstring(course_id)
        hashed_course_id = course_id
        course_path = os.path.join(
            grade_dir, hashed_course_id.replace("/", "-") + ".md")
        if not os.path.exists(course_path):
            with open(course_path, "w", encoding='utf8') as page:
                page.write(course_page_template.format(
                    course_id=course_id, course_name=course_name)
                )
        readme.write(entry_template.format(
            course_id=course_id, course_name=course_name, grade_url=grade_url, hashed_course_id=hashed_course_id
        ))
        sidebar.write(entry_template.format(
            course_id=course_id, course_name=course_name, grade_url=grade_url, hashed_course_id=hashed_course_id
        ))
