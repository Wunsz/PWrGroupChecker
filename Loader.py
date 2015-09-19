import datetime
import GroupChecker
import time
import pprint
import configparser

__author__ = 'Bartosz Jabłoński <thewunsz@gmail.com>'

if __name__ == "__main__":
    parser = configparser.ConfigParser()
    parser.read("settings.ini")

    # Shall we?
    start = time.time()

    groupChecker = GroupChecker.GroupChecker(parser.get("General", "subscriptions"))

    groupChecker.login(parser.get("General", "login"), parser.get("General", "password"))
    courses = groupChecker.get_courses()
    groups = groupChecker.get_groups(courses.keys())

    groupChecker.logout()

    pprint.pprint(courses)
    pprint.pprint(groups)

    end = time.time()
    result = end - start

    print("Latest data from: ")
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("\n All done in %.2f seconds!" % result)
    # Good night :)
