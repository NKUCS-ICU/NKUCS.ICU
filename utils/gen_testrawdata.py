import os
from fnmatch import fnmatch

import pymysql
from settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from pymysql import connect
from pymysql.cursors import DictCursor

# Cross-platform path separators
path1 = os.path.join("..", "courses")
path2 = os.path.join("..", "courses_law")
path3 = os.path.join("..", "courses_maphd")


class Connector(object):
    def __init__(self):
        self.conn = connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4'
        )
        self.cursor = self.conn.cursor(DictCursor)

    def __del__(self):
        self.cursor.close()
        self.conn.close()


def show_files(base_path):
    ret_files = []
    print(base_path)
    for root, dirs, files in os.walk(top=base_path):
        for file in files:
            if fnmatch(file, "*.md"):
                ret_files.append(os.path.join(root, file))
    return ret_files


def insert_into_db_courses(files, base_course_id, course_type, course_department):
    counter = 100000
    for file in files:
        course_id = base_course_id + str(counter)
        course_nkcode = os.path.splitext(os.path.basename(file))[0]
        with open(file, 'rb') as fdes:
            fdes.readline()
            fline = fdes.readline().decode('utf-8')
        course_name = fline.split(' ')[-1].strip()
        if course_nkcode == 'README' or course_name == 'README':
            continue
        # Use parameterized query to prevent SQL injection
        sql = "INSERT INTO courses (course_id, course_isvalid, course_nkcode, course_name, course_type, course_department) VALUES (%s, %s, %s, %s, %s, %s)"
        connector.cursor.execute(sql, (course_id, 1, course_nkcode, course_name, course_type, course_department))
        connector.conn.commit()
        counter += 1


def insert_into_db_pages(files, base_page_id):
    counter = 100000
    for file in files:
        course_nkcode = os.path.splitext(os.path.basename(file))[0]
        page_id = base_page_id + str(counter)
        page_createtimestamp = "2023-01-08 00:01:02"
        page_updatetimestamp = "2023-01-08 00:01:02"
        with open(file, 'rb') as fdes:
            flines = fdes.readlines()
        page_content = ""
        for line in flines:
            page_content = page_content + line.decode('utf-8') + "\n"
        if course_nkcode == 'README':
            continue
        # Build GitHub Pages URL using os.path for cross-platform compatibility
        rel_path = os.path.relpath(file, "..")
        githubpage_url = "https://nkucs.icu/#/" + rel_path.replace(os.sep, '/').replace('.md', '')
        # Use parameterized query to prevent SQL injection
        sql = ("INSERT INTO pages (page_id, page_type, page_createtimestamp, page_updatetimestamp, "
               "page_content, page_githubpageurl) VALUES (%s, %s, %s, %s, %s, %s)")
        try:
            connector.cursor.execute(sql, (page_id, "Course", page_createtimestamp,
                                           page_updatetimestamp, page_content, githubpage_url))
        except pymysql.err.IntegrityError:
            continue
        connector.conn.commit()
        counter += 1


if __name__ == '__main__':
    connector = Connector()
    files1 = show_files(path1)
    files2 = show_files(path2)
    # insert_into_db_courses(files1, base_course_id="COURSE21", course_type="computer science", course_department="college of computer science/cyber security")
    # insert_into_db_courses(files2, base_course_id="COURSE22", course_type="law", course_department="college of cyber security/law")
    insert_into_db_pages(files1 + files2, base_page_id="PAGE")
