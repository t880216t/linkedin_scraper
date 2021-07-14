import requests, json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .objects import Experience, Education, Scraper, Interest, Accomplishment, Contact
import os
from linkedin_scraper import selectors


class Person(Scraper):

    __TOP_CARD = "pv-top-card"
    __WAIT_FOR_ELEMENT_TIMEOUT = 5

    def __init__(
        self,
        linkedin_url=None,
        name=None,
        about=None,
        experiences=None,
        educations=None,
        interests=None,
        accomplishments=None,
        company=None,
        job_title=None,
        contacts=None,
        driver=None,
        get=True,
        scrape=True,
        close_on_complete=True,
    ):
        self.linkedin_url = linkedin_url
        self.name = name
        self.about = about or []
        self.experiences = experiences or []
        self.educations = educations or []
        self.interests = interests or []
        self.accomplishments = accomplishments or []
        self.also_viewed_urls = []
        self.contacts = contacts or []

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") == None:
                    driver_path = os.path.join(
                        os.path.dirname(__file__), "drivers/chromedriver"
                    )
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        if get:
            driver.get(linkedin_url)

        self.driver = driver

        if scrape:
            self.scrape(close_on_complete)

    def scrape(self, close_on_complete=True):
        if self.is_signed_in():
            self.scrape_logged_in(close_on_complete=close_on_complete)
        else:
            print("you are not logged in!")
            x = input("please verify the capcha then press any key to continue...")
            self.scrape_not_logged_in(close_on_complete=close_on_complete)

    def get_profile_data(self,html):
        persionProfile = {}
        dataList = []
        soup = BeautifulSoup(html, 'html.parser')

        dataAll = soup.find_all('code')
        sourceId = None
        for codeChild in dataAll:
            data = codeChild.text
            dataId = codeChild.get('id')
            if data:
                try:
                    if 'request' in data.keys() and "com.linkedin.voyager.dash.deco.identity.profile" \
                                                    ".FullProfileWithEntities" in data['request']:
                        sourceId = data['body']
                    dataList.append({'dataId': dataId, 'content': data})
                except:
                    pass
        for data in dataList:
            if data['dataId'] == sourceId and 'data' in data['content'].keys():
                print(data['content'])
                for info in data['content']['included']:
                    if info['$type'] == 'com.linkedin.voyager.dash.identity.profile.Profile':
                        persionProfile = {
                            'firstName': info['firstName'],
                            'publicIdentifier': info['publicIdentifier'],
                            'lastName': info['lastName'],
                            'memorialized': info['memorialized'],
                            'summary': info['summary'],
                            'maidenName': info['maidenName'],
                            'profilePicture': "{}{}".format(
                                info['profilePicture']['displayImageReference']['vectorImage'],
                                info['profilePicture']['displayImageReference']['vectorImage']['artifacts'][1]['fileIdentifyingUrlPathSegment'].replace('&amp;', '&'),
                            ),
                        }
                    elif info['$type'] == 'com.linkedin.voyager.dash.identity.profile.Position':
                        persionProfile['PositionTitle'] = info['title']
                        persionProfile['PositionCompanyName'] = info['companyName']
                    elif info['$type'] == 'com.linkedin.voyager.dash.organization.Company':
                        persionProfile['companyUrl'] = info['url']
                        persionProfile['companyName'] = info['name']
                        persionProfile['companyUniversalName'] = info['universalName']
        return persionProfile

    def scrape_logged_in(self, close_on_complete=True):
        driver = self.driver
        duration = None

        root = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.CLASS_NAME,
                    self.__TOP_CARD,
                )
            )
        )
        if root:
            html = driver.page_source
            personProfile = self.get_profile_data(html)

            print(personProfile)

        if close_on_complete:
            driver.quit()

    def scrape_not_logged_in(self, close_on_complete=True, retry_limit=10):
        driver = self.driver
        retry_times = 0
        while self.is_signed_in() and retry_times <= retry_limit:
            page = driver.get(self.linkedin_url)
            retry_times = retry_times + 1
            print(page)
        if close_on_complete:
            driver.close()

    def __repr__(self):
        return "{name}\n\nAbout\n{about}\n\nExperience\n{exp}\n\nEducation\n{edu}\n\nInterest\n{int}\n\nAccomplishments\n{acc}\n\nContacts\n{conn}".format(
            name=self.name,
            about=self.about,
            exp=self.experiences,
            edu=self.educations,
            int=self.interests,
            acc=self.accomplishments,
            conn=self.contacts,
        )