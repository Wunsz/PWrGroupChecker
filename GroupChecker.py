# -*- coding: utf-8 -*-
import requests
import re
from sqlalchemy import func
from orm.Connection import Connection
from orm.Course import Course
from orm.Group import Group
from orm.GroupLog import GroupLog

from bs4 import BeautifulSoup

__author__ = 'Bartosz Jabłoński <thewunsz@gmail.com>'

class GroupChecker:
    """
    This project would not succeed without Piotr Giedziun <piotrgiedziun@gmail.com>
    and his script for generating the schedule basing on Edukacja CL.

    You can find it here: https://github.com/piotrgiedziun/plan_pwr

    Usage:
    subscriptions_id = 1234
    checker = GroupChecker(subscriptions_id)

    checker.login("somelogin", "somepass")

    courses = checker.get_courses()
    groups = checker.get_groups(courses.keys())

    checker.logout()

    """

    GET_COOKIES_URL = 'https://edukacja.pwr.wroc.pl/EdukacjaWeb/logOutUser.do'
    LOGIN_URL = 'https://edukacja.pwr.wroc.pl/EdukacjaWeb/logInUser.do'
    ZAPISY_COOKIES_URL = 'https://edukacja.pwr.wroc.pl/EdukacjaWeb/zapisy.do?event=WyborSluchacza'
    ZAPISY_URL = 'https://edukacja.pwr.wroc.pl/EdukacjaWeb/zapisy.do?href=#hrefZapisySzczSlu'
    ZAPISY_URL_X = 'https://edukacja.pwr.wroc.pl/EdukacjaWeb/zapisy.do?event=ZapiszFiltr&event=wyborKryterium&href=#hrefKryteriumFiltrowania'
    ZAPISY_GUIDE_LINE_COOKIES_URL = 'https://edukacja.pwr.wroc.pl/EdukacjaWeb/zapisy.do?event=WyborSluchacza'
    LOGOUT_URL = 'https://edukacja.pwr.wroc.pl/EdukacjaWeb/logOutUser.do'

    ERROR_NO_ACCESS = 'Brak uprawnień dostępu do żądanego zasobu.'
    ERROR_WRONG_LOGIN_PASS = 'Niepowodzenie logowania. Niepoprawna nazwa użytkownika'
    ERROR_SERVER_OVERLOADED = 'Jesteś w tej chwili jednym z kilku tysięcy chętnych do odwiedzenia naszego portalu'
    ERROR_BAD_TIME = 'Nie można wykonać tej akcji poza dozwolonymi terminami. Wykonujesz akcję w bloku z ograniczeniami, dla którego są one zabronione.'

    INFO_WRONG_LOGIN_PASS = 'Nie jebłeś się w loginie lub haśle? Bo to co dałeś nie działa... (Wrong login or password)'
    INFO_SERVER_OVERLOADED = 'Hue hue. Za dużo owieczek lgnie na rzeź! (Server overloaded)'
    INFO_GROUP_QUOTA_NOT_FOUND = 'Group quota not found!'
    INFO_TOKEN_NOT_FOUND = 'Token not found!'
    INFO_BAD_TIME = 'Hue hue. Za późno >:D Nie możesz już tego zrobić >:D (Nie można wykonać tej akcji poza dozwolonymi terminami)'

    ELEMENTS_PER_PAGE = 10

    def __init__(self, subscriptions_id, use_db):
        self.session = None
        self.last_cookie = None
        self.token = None
        self.subscriptions_id = subscriptions_id
        self.use_db = bool(use_db)
        self.logs = []

        if self.use_db:
            self.connection = Connection.session()

        pass

    def login(self, login, password):
        """
        Logs user in optaining cl.edu.web.TOKEN
        :param login: User login
        :param password: User password
        :return:
        """

        # Prepare request
        token = self._get_token()
        login_data = {
            'login': login,
            'password': password,
            'cl.edu.web.TOKEN': token
        }

        login_response = requests.post(self.LOGIN_URL,
                                       data=login_data,
                                       cookies=self.last_cookie,
                                       allow_redirects=True,
                                       verify=True)

        login_response_html = login_response.text

        # Check if there was no login error
        if self.ERROR_NO_ACCESS in login_response_html or self.ERROR_WRONG_LOGIN_PASS in login_response_html:
            raise Exception(self.INFO_WRONG_LOGIN_PASS)

        # Check if there was no server overloaded error
        if self.ERROR_SERVER_OVERLOADED in login_response_html:
            raise Exception(self.INFO_SERVER_OVERLOADED)

        # Set session cookie
        self.session = self._parse_session(login_response_html)
        self.last_cookie = login_response.cookies
        self.token = token

    def logout(self):
        """
        Log user out
        :return:
        """
        post_data = {
            'clEduWebSESSIONTOKEN': self.session,
            'cl.edu.web.TOKEN': self.token,
            'wyloguj': ''
        }

        requests.post(self.LOGOUT_URL, data=post_data, cookies=self.last_cookie, allow_redirects=True, verify=True)

    def get_courses(self):
        self._navigate_to_courses()

        courses_request_data = self._get_courses_groups_request()

        total_return = requests.post(self.ZAPISY_URL_X, cookies=self.last_cookie, data=courses_request_data,
                                     allow_redirects=False, verify=True)

        self.last_cookie = total_return.cookies

        return self._parse_course_vector_data(total_return.text.encode('utf-8'))

    def get_groups(self, courses_codes):
        """
        Gets all grupus data of all courses
        :param courses_codes: List of course codes
        :return: Full data
        """

        self._navigate_to_courses()

        full_data = {}
        for course_code in courses_codes:
            print('.', end="", flush=True)
            full_data[course_code] = self.get_course_groups(course_code)

        print("")
        return full_data

    def get_course_groups(self, course_code):
        """
        Gets all groups data of specified course
        :param course_code: Code of the course INZ001234L
        :return: Full data
        """

        current_page = 1
        page_iterator_condition = True
        max_page = None

        groups = {}

        # For each page of the pagination
        while page_iterator_condition:
            # Prepare request
            page_data = self._prepare_group_paginator_value(current_page)
            course_details_request = self._get_courses_groups_request(course_code=course_code,
                                                                      additional_parameters=page_data)

            # Send the request and extract html data and set the cookie
            response = requests.post(self.ZAPISY_URL_X, cookies=self.last_cookie, data=course_details_request,
                                     allow_redirects=False, verify=True)
            html = response.text.replace('</br>', '')
            self.last_cookie = response.cookies

            # Check if proper data was received
            if self.ERROR_BAD_TIME in html:
                raise Exception(self.INFO_BAD_TIME)

            # Parse current page groups
            current_page_groups = self._parse_course_groups(html, course_code)
            groups.update(current_page_groups)

            # Exit loop if that was the last page
            if max_page is None:
                max_page = self._get_max_page(html)

            current_page += 1
            page_iterator_condition = current_page <= max_page

        return groups

    def _parse_session(self, html):
        """
        Parses session information to obtain session token
        :param html:
        :return:
        """
        p = re.compile(r'<input type="hidden" name="clEduWebSESSIONTOKEN" value="(?P<session>[a-zA-Z0-9=]+)">')
        m = p.search(html)

        if m is None:
            raise Exception("Can't complie session")

        return m.group('session')

    def _get_token(self):
        """
        Gets the session and token (also sets a cookie)
        :return:
        """
        get_cookies_r = requests.get(self.GET_COOKIES_URL, verify=True)

        token = self._parse_token(get_cookies_r.text.encode('utf-8'))

        # set cookie
        self.last_cookie = get_cookies_r.cookies

        return token

    def _parse_token(self, html):
        """
        Finds and returns Edukacja.CL navigation token
        :param html:
        :return:
        """
        p = re.compile(r'<input type="hidden" name="cl.edu.web.TOKEN" value="(?P<token>[a-zA-Z0-9=]+)">')
        m = p.search(html.decode("utf-8"))

        if m is None:
            raise Exception(self.INFO_TOKEN_NOT_FOUND)

        return m.group('token')

    def _navigate_to_courses(self):
        # Get the schedule
        zapisy_cookies_r = requests.get(self.ZAPISY_GUIDE_LINE_COOKIES_URL,
                                        params={'clEduWebSESSIONTOKEN': self.session}, cookies=self.last_cookie,
                                        verify=True)
        zapisy_cookies_html = zapisy_cookies_r.text.encode('utf-8')
        token = self._parse_token(zapisy_cookies_html)

        zapisy_data = {'clEduWebSESSIONTOKEN': self.session,
                       'cl.edu.web.TOKEN': token,
                       'positionIterator': 'ZapisyROViewIterator',
                       'rowId': self.subscriptions_id,
                       'event_ZapisyPrzegladanieGrup': 'Przeglądanie grup'
                       }

        zapisy_r = requests.post(self.ZAPISY_URL, cookies=self.last_cookie, data=zapisy_data, allow_redirects=True,
                                 verify=True)

        if self.ERROR_BAD_TIME in zapisy_r.text:
            raise Exception(self.INFO_BAD_TIME)

        # Set a cookie. OM NOM NOM NOM!
        self.last_cookie = zapisy_r.cookies
        self.token = self._parse_token(zapisy_r.text.encode('utf-8'))

    def _parse_course_vector_data(self, page_html):
        """
        Parses course data to extract course codes and names in this vector
        :param page_html: HTML page to be parsed
        :return: Array
        """

        soup = BeautifulSoup(page_html, 'html.parser')
        courses = soup.find_all(name="a", attrs={"title": "Wybierz wiersz"})

        pretty_courses = {}
        for course in courses:
            course_code = str.strip(course.text)

            pretty_courses[course_code] = {
                "code": course_code,
                "name": str.strip(course.parent.next_sibling.next_sibling.text),  # 2 next sibling because of spaces
                "type": course_code[-1:]
            }

            self._save_or_update_course(pretty_courses[course_code])

        return pretty_courses

    def _get_courses_groups_request(self, group_code="", course_code="", additional_parameters={}):
        """
        Prepares search request for courses data
        :param group_code: Group code search filter (i.e. Z00-12e)
        :param course_code: Course code search filter (i.e. INZ001234L)
        :return: Request dictionary
        """

        base_data = {
            "KryteriumFiltrowania": "Z_WEKTORA_ZAP",
            "UczPpsId": "178883",
            "UczSppId": "1111609",
            "cl.edu.web.TOKEN": self.token,
            "clEduWebSESSIONTOKEN": self.session,
            "filtrCzyPowt": "",
            "filtrCzyRez": "",
            "filtrCzyZabl": "",
            "filtrGodzDo": "",
            "filtrGodzOd": "",
            "filtrGrupyWDniu": "",
            "filtrInePrNazwisko": "",
            "filtrKodGrupy": group_code,
            "filtrKodKursu": course_code,
            "filtrNazwaKursu": "",
            "ineJorId": "",
            "ineJorSymbol": "",
            "ineJorSymbol": "",
            "ineJorSymbol_cl_edu_web_lov_callback": "/zapisy.do?event=forwardZapisy",
            "ineJorSymbol_cl_edu_web_lov_callback_href": "hrefKryteriumFiltrowania",
            "ineJorSymbol_cl_edu_web_lov_handlerClass": "cl.edu.web.common.lov.handlers.JednostkiOrganizacyjneLovHandler",
            "uczWppId": "93647",
            "uczWppNazwa": "PO-W08-INF- - -ST-Ii-WRO- - - - - -PWR1-DWU, W_PO-W08-INF- - -ST-Ii-WRO (2012/2013)/V9",
            "uczWppNazwa": "93647",
            "uczWppNazwa_cl_edu_web_lov_callback": "/zapisy.do?event=forwardZapisy",
            "uczWppNazwa_cl_edu_web_lov_callback_href": "hrefKryteriumFiltrowania",
            "uczWppNazwa_cl_edu_web_lov_handlerClass": "cl.edu.web.controller.logic.studiowanie.zapisy.WiazkiPnPsLovHandler",
            "event_NoEvent": "Szukaj",
        }

        for key in additional_parameters.keys():
            base_data[key] = additional_parameters[key]

        return base_data

    def _prepare_group_paginator_value(self, page):
        return {
            "pagingIterName": "GrupyZajecioweKursuWEKROViewIterator",
            "pagingRangeStart": (page - 1) * self.ELEMENTS_PER_PAGE,
            "event": "positionIterRangeStartGZK"
        }

    def _get_max_page(self, html_page):
        soup = BeautifulSoup(html_page, 'html.parser')
        tag = soup.find_all("input", {"value": ">>>"})[1]

        if tag.has_attr("onclick"):
            number_regex = re.compile(r"pagingRangeStartGrupyZajecioweKursuWEKROViewIteratorId', '(?P<number>[0-9]+)'")
            result = number_regex.search(tag["onclick"])

            max_item_count_start = result.group("number").strip()
            page = (int(max_item_count_start) / self.ELEMENTS_PER_PAGE) + 1
        else:
            page = 1

        return page

    def _parse_course_groups(self, html, course_code):
        """
        Parses all groups for given page
        :param html:
        :return: Parsed groups
        """

        soup = BeautifulSoup(html, 'html.parser')
        groups_table = soup.find(name="a", attrs={"name": "hrefGrupyZajecioweKursuTabela"}) \
            .find_next_sibling(name="table", attrs={"class": "KOLOROWA"})

        first_row = self._get_nth_sibling(groups_table.tr, 4)

        groups = {}

        condition_regex = re.compile(r'Z[0-9]{2}-.{2,5}')
        condition = True
        first_row = first_row.next_sibling.next_sibling

        while condition:
            group_data = self._parse_course_group(first_row, course_code)
            groups[group_data[0]['code']] = group_data[0]

            first_row = group_data[1]
            condition = first_row.next_sibling != None and \
                        first_row.next_sibling.next_sibling != None

            alternative_one = self._get_nth_sibling(first_row, 2).td.has_attr("rowspan") and \
                              condition_regex.match(self._get_nth_sibling(first_row, 2).td.text.strip()) is not None

            alternative_two = self._get_nth_sibling(first_row, 2).has_attr("class") and \
                              self._get_nth_sibling(first_row, 2)['class'][0] == "uwagi_hide" and \
                              self._get_nth_sibling(first_row, 4) is not None and \
                              self._get_nth_sibling(first_row, 4).td.has_attr("rowspan") and \
                              condition_regex.match(self._get_nth_sibling(first_row, 4).td.text.strip()) is not None

            if condition and alternative_one:
                first_row = self._get_nth_sibling(first_row, 2)
            elif condition and alternative_two:
                first_row = self._get_nth_sibling(first_row, 4)

            condition = condition and (alternative_one or alternative_two)

        self._commit_to_db()

        return groups

    def _parse_course_group(self, first_row, course_code):
        """
        Parses 3-row data of the group
        :param first_row: First row from 3 row data in Edukacja (BeautifulSoup)
        :return: Parsed data, and reference to last row
        """

        second_row = self._get_nth_sibling(first_row, 2)
        third_row = self._get_nth_sibling(second_row, 2)

        quota = self._get_nth_sibling(first_row.td, 6).text

        group_data = {
            'code': first_row.td.text.strip(),
            'taken': self._parse_quota(quota, 0),
            'capacity': self._parse_quota(quota, 1),
            'lecturer': re.sub(r'\s+', ' ', second_row.td.text.strip())}

        group_data.update(self._parse_place_and_time(third_row.td.text.strip()))

        # Save to DB
        self._save_or_update_group(group_data, course_code, True)

        return [group_data, third_row]

    @staticmethod
    def _parse_quota(quota_text, part):
        """
        Parses quota string returning either capacity or already subscribed student count
        :param quota_text: Text of the quota 12/30
        :param part: 1 - subscribed, 2 - capacity
        :return: Number of subscribed or capacity
        """

        split_quota = quota_text.strip().split('/')
        return split_quota[part]

    @staticmethod
    def _parse_place_and_time(place_time):
        """
        Parses time and place string extracting vital information like building
        or room as well as time
        :param place_time: String to be parsed
        :return: Parsed array
        """

        regex = re.compile(
            r'(?P<day>(pn|wt|śr|cz|pt)(/TN |/TP |[ ]))(?P<start>[0-9]+:[0-9]+)-(?P<end>[0-9]+:[0-9]+), bud. (?P<building>[\w\-]+), sala (?P<room>[\w]+)')
        regex_result = regex.search(place_time)
        data = {}

        if regex_result is not None:
            data['day'] = regex_result.group('day').strip()
            data['start'] = regex_result.group('start')
            data['end'] = regex_result.group('end')
            data['building'] = regex_result.group('building')
            data['room'] = regex_result.group('room')
        else:
            data['day'] = "?"
            data['start'] = "00:00"
            data['end'] = "00:00"
            data['building'] = "?"
            data['room'] = "?"

        return data

    @staticmethod
    def _get_nth_sibling(soup_tag, sibling_count):
        """
        Returns nth sibling of given BeautifulSoup tag
        :param soup_tag:
        :param sibling_count:
        :return:
        """
        while sibling_count > 0:
            soup_tag = soup_tag.next_sibling
            sibling_count -= 1

        return soup_tag

    def _save_or_update_course(self, course_data):
        """
        Saves or updates course data
        :param course_data:
        :return:
        """
        if not self.use_db:
            return

        course = self.connection.query(Course).filter(Course.id_course == course_data["code"]).first()
        if course is None:
            course = Course(id_course=course_data["code"], name=course_data["name"], type=course_data["type"])
            self.connection.add(course)
            self.connection.commit()
        elif course.name is not course_data["name"] or course.type is not course_data["type"]:
            course.name = course_data["name"]
            course.type = course_data["type"]
            self.connection.commit()

    def _save_or_update_group(self, group_data, course, log_change=True):
        """
        Updates or saves group and if specified, creates a log entry
        :param group_data:
        :param course:
        :param log_change:
        :return:
        """

        log_change = False    # Logging feature is not working!

        if not self.use_db:
            return

        group = self.connection.query(Group).filter(Group.id_group == group_data["code"]).first()
        if group is None:
            group = Group(id_group=group_data["code"], id_course=course, assigned=group_data["taken"], capacity=group_data["capacity"])
            group.last_change = None
            self.connection.add(group)

        if int(group.assigned) != int(group_data["taken"]):
            group.last_change = func.now()
            self.connection.add(group)

        group.assigned = group_data["taken"]
        group.capacity = group_data["capacity"]
        group.day = None if group_data["day"] is "?" else self._parse_day(group_data["day"])
        group.week = None if group_data["day"] is "?" else self._parse_week(group_data["day"])
        group.start = None if group_data["start"] is "00:00" else group_data["start"]
        group.end = None if group_data["start"] is "00:00" else group_data["end"]
        group.building = None if group_data["building"] is "?" else group_data["building"]
        group.room = None if group_data["room"] is "?" else group_data["room"]
        group.lecturer = None if group_data["lecturer"] is "?" else group_data["lecturer"]
        group.updated = func.now()

        if log_change:
            group_log = GroupLog(id_group=group_data["code"], assigned=group_data["taken"])
            group_log.check_time = func.now()

            self.logs.append(group_log)

    def _parse_week(self, string):
        """
        Parses week number
        :param string:
        :return:
        """
        return "Odd" if "/TN" in string else "Even" if "/TP" in string else None

    def _parse_day(self, string):
        """
        Parses day
        :param string:
        :return:
        """
        if "pn" in string:
            return 1
        elif "wt" in string:
            return 2
        elif "śr" in string:
            return 3
        elif "cz" in string:
            return 4
        elif "pt" in string:
            return 5
        else:
            return None

    def _commit_to_db(self):
        """
        Commits sql changes
        :return:
        """
        if self.use_db:
            self.connection.commit()

            for group_log in self.logs:
                self.connection.add(group_log)

            self.connection.commit()
            self.logs = []