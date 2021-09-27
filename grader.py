"""
Copyright 2021 Drake Axelrod

Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
and associated documentation files (the "Software"), to deal in the Software without 
restriction, including without limitation the rights to use, copy, modify, merge, publish, 
distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom 
the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or 
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import os
import json
from pathlib import Path
import shutil
import sys
import re
import pandas as pd
import datetime

# config defaults
CWD = str(Path.cwd())
CONFIG_NAME = "grader_config.json"
CONFIG_PROJECTS_DIR = "/projects"
CONFIG_PROJECT_STRUCTURE = { "tests_dir": "src/test", "pom_file": "pom.xml" }
CONFIG_RESOURCE_PATH= { "tests": CWD + "/resources/test", "pom": CWD + "/resources/pom.xml" }
CONFIG_TEST_COMMAND = "mvn test"
CONFIG_GRADES_DIR = CWD + "/grades"
CONFIG_OUTPUT_TIMESTAMP_FORMAT = "%Y-%m-%d-%H-%M-%S_"
config: dict =  json.load(open(CONFIG_NAME )) if os.path.isfile(CONFIG_NAME) else { }
config.setdefault("projects_dir", CWD + "/projects" ),
config.setdefault("project_structure", CONFIG_PROJECT_STRUCTURE) 
config.setdefault("resources_path", CONFIG_RESOURCE_PATH)
config.setdefault("test_command", CONFIG_TEST_COMMAND)
config.setdefault("grades_output_dir",  CONFIG_GRADES_DIR)
config.setdefault("output_timestamp_format",  CONFIG_OUTPUT_TIMESTAMP_FORMAT) 

# assign config settings
PROJECTS_DIR = Path(config["projects_dir"])
TEST_COMMAND = config["test_command"]
GRADES_OUTPUT_DIR = Path(config["grades_output_dir"])
TEST_DIR = Path(config["resources_path"]["tests"])
POM_FILE = Path(config["resources_path"]["pom"])
PROJECT_TESTS_PATH = Path(config["project_structure"]["tests_dir"])
PROJECT_POM_FILE_PATH = Path(config["project_structure"]["pom_file"])
TIMESTAMP_FORMAT = config["output_timestamp_format"]

# individual project symantics
MODIFIED_PROJECT_TESTS_PATH = PROJECT_TESTS_PATH.with_name("original_test")
MODIFIED_PROJECT_POM_FILE_PATH = PROJECT_POM_FILE_PATH.with_name("original_pom.xml")

#make sure everything is where its supposed to be or inform the user that something is wrong
if not PROJECTS_DIR.is_dir():
    print(f"projects directory does not exist or has been configured incorrectly")
    exit(1)
if not GRADES_OUTPUT_DIR.is_dir():
    Path.mkdir(GRADES_OUTPUT_DIR)
if not TEST_DIR.is_dir():
        print(f"test suite directory does not exist or has been configured incorrectly")
        exit(1)
if not POM_FILE.is_file():
        print(f"pom file does not exist or has been configured incorrectly")
        exit(1)

all_projects = list(PROJECTS_DIR.iterdir())
all_projects.sort()

# progressbar - code was taken from https://stackoverflow.com/a/34482761
def progressbar(it, prefix="", size=60, file=sys.stdout):
    count = len(it)
    def show(j):
        x = int(size*j/count)
        file.write("%s[%s%s] %i/%i\r" % (prefix, "#"*x, "."*(size-x), j, count))
        file.flush()        
    show(0)
    for i, item in enumerate(it):
        yield item
        show(i+1)
    file.write("\n")
    file.flush()

# timestamp - code was taken from https://stackoverflow.com/a/5215012
def timeStamped(fname):
    fmt = '%Y-%m-%d-%H-%M-%S_{fname}'
    fmt = f"{TIMESTAMP_FORMAT}{fname}"
    return datetime.datetime.now().strftime(fmt).format(fname=fname)

# parse the output of mvn test specifically
def sanitize_results(result: str) -> str:
    start_str = "T E S T S\n[INFO] -------------------------------------------------------\n"
    start = result.find(start_str) + len(start_str)
    end = result.find("BUILD SUCCESS")
    substring = result[start:end]
    line_arr = substring.splitlines()
    arr = []
    for line in line_arr:
        s = re.sub("Running |\[INFO\] |\n|-*", "", line)
        if s != "":
            arr.append(s)
    project_dict: dict = {}
    while len(arr) > 0:
        val: str = arr.pop()
        key = arr.pop()
        project_dict[key] = str_to_dict(val)
        # add field for results for csv
    project_dict["Results:"]["Time elapsed"] = "empty"
    # remove time elapsed 
    for project in project_dict:
        del project_dict[project]["Time elapsed"]
    return project_dict


# parses a str such as "{'Tests run': 45, 'Failures': 0, 'Errors': 0, 'Skipped': 0}" to a dict
def str_to_dict(string):
    my_dict = {}
    str_arr = string.split(",")
    for s in str_arr:
        i = s.split(': ')
        # if its an int cast otherwise dont
        my_dict[i[0].strip()] = int(i[1]) if (i[1]).isdigit() else i[1]
    return my_dict

# renames a dir or file in a project
def rename_resource(project: Path, original: Path, modifed:  Path):
    try:
        Path(project / original).rename(Path(project / modifed))
    except:
        print(f"could not rename the {original} in {project.stem}")

# changes the projects test dir and pom.xml names so that they are not used in mvn test
def invalidate_project_resources(project: Path):
    rename_resource(project, PROJECT_TESTS_PATH, MODIFIED_PROJECT_TESTS_PATH)
    rename_resource(project, PROJECT_POM_FILE_PATH, MODIFIED_PROJECT_POM_FILE_PATH)

# repairs the changes from _invalidate_project_resources
def fix_project_resources(project: Path):
    rename_resource(project, MODIFIED_PROJECT_TESTS_PATH, PROJECT_TESTS_PATH)
    rename_resource(project, MODIFIED_PROJECT_POM_FILE_PATH, PROJECT_POM_FILE_PATH)

# copies the designated test dir and pom.xml into the project
def cp_resources_to_project(project: Path):
    path = project/PROJECT_TESTS_PATH
    try:
        shutil.copytree(TEST_DIR, path)
    except:
        print(f"could not find {TEST_DIR} or {path}")
    try:
        shutil.copy(POM_FILE, project/PROJECT_POM_FILE_PATH)
    except:
        print(f"could not find {POM_FILE} or {path}")

# removes the copied test dir and pom.xml from the project
def rm_resources_from_project(project: Path):
    shutil.rmtree(str(project/PROJECT_TESTS_PATH))
    os.remove(str(project/PROJECT_POM_FILE_PATH))

# grades a project via mvn test
def grade_project(project: Path):
    invalidate_project_resources(project)
    cp_resources_to_project(project)
    result = _run_mvn_test(project)
    rm_resources_from_project(project)
    fix_project_resources(project)
    return result

# runs mvn test from the current project root directory
def _run_mvn_test(project: Path):
    os.chdir(project)
    return sanitize_results(os.popen(TEST_COMMAND).read())

# loops through the projects and grades them building a dict of results
def grade_all_projects():
    grades = {}
    for project in progressbar(list(all_projects), "Grading Projects: ", 60):
        try:
            grades[project.stem] = grade_project(project)
        except:
            print(f"could not grade {project} due to an error in the project structure")
    return grades

# parses the grades dict into a json and csv
def output_grades(grades: dict):
    json_path: str = str(GRADES_OUTPUT_DIR/timeStamped("grades.json"))
    csv_path: str = str(GRADES_OUTPUT_DIR/timeStamped("grades.csv"))
    # save as json (needed for csv)
    with open(json_path, 'w') as f:
        json.dump(grades, indent=4 ,fp=f)
    f.close()
    # save as csv
    df: pd.DataFrame = pd.read_json(json_path)
    df = df.to_csv()
    with open(csv_path, 'w') as f:
        f.write(df)
    f.close

# makes the script go zoom!
output_grades(grade_all_projects())
