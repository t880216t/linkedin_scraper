import requests, json
from bs4 import BeautifulSoup
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .objects import Scraper
import time
import os
import json


class Company(Scraper):
    linkedin_url = None
    name = None
    about_us = None
    website = None
    headquarters = None
    founded = None
    industry = None
    company_type = None
    company_size = None
    specialties = None
    showcase_pages = []
    affiliated_companies = []

    def __init__(self, linkedin_url=None, name=None, about_us=None, website=None, headquarters=None, founded=None,
                 industry=None, company_type=None, company_size=None, specialties=None, showcase_pages=[],
                 affiliated_companies=[], driver=None, scrape=True, get_employees=True, close_on_complete=True):
        self.linkedin_url = linkedin_url
        self.token = None
        self.companyInfo = {}
        self.cookies = None
        self.session = requests.Session()

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") == None:
                    driver_path = os.path.join(os.path.dirname(__file__), 'drivers/chromedriver')
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        driver.get(linkedin_url)
        self.driver = driver

        if scrape:
            self.scrape(get_employees=get_employees, close_on_complete=close_on_complete)

    # 获取cookies
    def get_cookies(self):
        # 获取浏览器所有Set-Cookie，返回对象是字典列表
        cookies = self.driver.get_cookies()
        # print(f"{cookies}")
        cookie_dict = {}
        for cookie in cookies:
            if cookie['name'] == 'JSESSIONID':
                self.token = cookie['value'].replace('"', '')
            cookie_dict[cookie['name']] = cookie['value'].replace('"', '')
        self.cookies = cookie_dict

    def scrape(self, get_employees=True, close_on_complete=True):
        if self.is_signed_in():
            self.scrape_logged_in(get_employees=get_employees, close_on_complete=close_on_complete)
        else:
            self.scrape_not_logged_in(get_employees=get_employees, close_on_complete=close_on_complete)

    def get_company_data(self, html):
        companyInfo = {}
        relateUser = []
        peopleAlsoView = []
        companyTopic = []
        dataList = []
        soup = BeautifulSoup(html, 'html.parser')

        dataAll = soup.find_all('code')
        for codeChild in dataAll:
            data = codeChild.text
            dataId = codeChild.get('id')
            try:
                data = json.loads(data)
                dataList.append({'dataId': dataId, 'content': data})
            except:
                pass
        for _data in dataList:
            # 获取公司基本信息
            if 'request' in _data['content'].keys() and "com.linkedin.voyager.deco.organization.web.WebFullCompanyMain" in \
                    _data['content']['request']:
                for data in dataList:
                    if data['dataId'] == _data['content']['body'] and 'data' in data['content'].keys():
                        for info in data['content']['included']:
                            try:
                                if info['$type'] == 'com.linkedin.voyager.organization.Company':
                                    companyInfo = {
                                        'name': info['name'],
                                        'url': info['url'],
                                        'relateUser': [],
                                        'peopleAlsoView': [],
                                        'companyTopic': [],
                                        'universalName': info['universalName'],
                                        'companyPageUrl': info['companyPageUrl'],
                                        'tagline': info['tagline'],
                                        'headquarter': info['headquarter'],
                                        'logo': "{}{}".format(
                                            info['logo']['image']['rootUrl'],
                                            info['logo']['image']['artifacts'][1]['fileIdentifyingUrlPathSegment'],
                                        ),
                                        'specialities': info['specialities'],
                                        'confirmedLocations': info['confirmedLocations'],
                                        'description': info['description'],
                                        'foundedOn': info['foundedOn']['year'],
                                        'companyType': info['companyType']['code'],
                                        'staffCountRange': {
                                            'start': info['staffCountRange']['start'],
                                            'end': info['staffCountRange']['end'],
                                        },
                                    }
                            except Exception as e:
                                print(e)
                                pass
            # 跟踪信息
            elif 'request' in _data['content'].keys() and 'com.linkedin.voyager.deco.organization.web.highlights.WebHighlightItem' in \
                    _data['content']['request']:
                for data in dataList:
                    if data['dataId'] == _data['content']['body'] and 'data' in data['content'].keys():
                        for info in data['content']['included']:
                            try:
                                # relate user
                                if info['$type'] == 'com.linkedin.voyager.identity.normalizedprofile.Profile':
                                    relateUser.append({
                                        'lastName': info['lastName'],
                                        'firstName': info['firstName'],
                                        'profilePicture': "{}{}".format(
                                            info['profilePicture']['rootUrl'],
                                            info['profilePicture']['artifacts'][1]['fileIdentifyingUrlPathSegment'].replace('&amp;', '&'),
                                        ),
                                        'mostRecentPosition': info['mostRecentPosition'],
                                        'companyName': info['mostRecentPosition']['companyName'],
                                        'title': info['mostRecentPosition']['title'],
                                        'startedOn': {
                                            'year': info['mostRecentPosition']['startedOn']['year'],
                                            'month': info['mostRecentPosition']['startedOn']['month'],
                                        },
                                    })
                                # company feed topic
                                elif info['$type'] == 'com.linkedin.voyager.feed.FeedTopic':
                                    companyTopic.append({
                                        'name': info['topic']['name'],
                                        'trending': info['topic']['trending'],
                                        'covid19': info['covid19'],
                                    })
                            except Exception as e:
                                print(e)
                                pass
            # 推荐信息
            elif 'request' in _data['content'].keys() and 'com.linkedin.voyager.deco.organization.web.WebSimilarCompanyCardWithRelevanceReason' in \
                    _data['content']['request']:
                for data in dataList:
                    if data['dataId'] == _data['content']['body'] and 'data' in data['content'].keys():
                        for info in data['content']['included']:
                            try:
                                # relate company
                                if info['$type'] == 'com.linkedin.voyager.organization.Company':
                                    peopleAlsoView.append({
                                        'name': info['name'],
                                        'url': info['url'],
                                        'logo': "{}{}".format(
                                            info['logo']['image']['rootUrl'],
                                            info['logo']['image']['artifacts'][1]['fileIdentifyingUrlPathSegment'],
                                        ),
                                        'universalName': info['universalName'],
                                        'staffCountRange': {
                                            'start': info['staffCountRange']['start'],
                                            'end': info['staffCountRange']['end'],
                                        },
                                    })
                            except Exception as e:
                                print(e)
                                pass

        companyInfo['relateUser'] = relateUser
        companyInfo['peopleAlsoView'] = peopleAlsoView
        companyInfo['companyTopic'] = companyTopic

        return companyInfo


    def scrape_logged_in(self, get_employees=True, close_on_complete=True):
        driver = self.driver

        driver.get(self.linkedin_url)

        _ = WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, '//span[@dir="ltr"]')))

        driver.get(self.linkedin_url)
        html = driver.page_source
        self.get_cookies()
        if html:
            self.companyInfo = self.get_company_data(html)

        if close_on_complete:
            driver.close()

    def scrape_not_logged_in(self, close_on_complete=True, retry_limit=10, get_employees=True):
        driver = self.driver
        retry_times = 0
        while self.is_signed_in() and retry_times <= retry_limit:
            page = driver.get(self.linkedin_url)
            retry_times = retry_times + 1

        driver.get(self.linkedin_url)

        if close_on_complete:
            driver.close()

    def __repr__(self):
        _output = {}
        _output['name'] = self.name
        _output['about_us'] = self.about_us
        _output['specialties'] = self.specialties
        _output['website'] = self.website
        _output['industry'] = self.industry
        _output['company_type'] = self.name
        _output['headquarters'] = self.headquarters
        _output['company_size'] = self.company_size
        _output['founded'] = self.founded
        _output['affiliated_companies'] = self.affiliated_companies
        _output['employees'] = self.employees

        return json.dumps(_output).replace('\n', '')
