# Script to test multiple maven java projects and store the outputs in a json file

This script was designed to help the grading of projects within the Gothenburg University Object Oriented Programming course DIT043. The idea is that groups create maven projects as part of the curriculum, and the teaching team wanted to automate a portion of the grading of these projects. this script allows for the teaching team to put all the student groups projects within a directory and run the teaching teams unit tests against all the student group projects. The maven test results or output to a json file a defined grades directory; if no grades directory is defined one will be made at the same location as the script. The methods of the script are commented to explain the purpose of the method. The script could be extended to work with other frameworks then just maven, however a defined project structure is necessary. 

## Configuration

to customize the behavior of the script you can create a grader_config.json file in the same directory as the grader.py script

**for the purposes of this config ./ is equivalent to location of grader.py**
```javascript
{
    "projects_dir": "",  // This is the directory of the student projects that you wish to be graded
    "project_structure": { // This defines where the tests directory and pom.xml files are found relative to the root of the individual projects.
        "tests_dir": "", // test Directory - default: src/test
        "pom_file": "" // pom.xml - default: pom.xml
    },
    "resources_path": { // Location of the Teaching teams resources to be used to test the student projects 
        "tests": "", // test directoy - default: ./resources/test
        "pom": "" // pom.xml file - default: ./resources/pom.xml
    },
    "test_command": "", // command to run on projects - default: mvn test
    "grade_output_dir": "", // the directory to output the grades as json and csv files - default: ./grades/{timestamp}grades.json and ./grades/{timestamp}grades.csv
    "output_timestamp_format": "" // the format for the prefix of the grades outputfiles - default: %Y-%m-%d-%H-%M-%S_
}
```
## Required Python Library

pandas - this is to convert from json to csv

## Extensions that could be made

- Threading to increase the speed
- the ability to work with other frameworks then just maven
- additional output formats to be specified in config
