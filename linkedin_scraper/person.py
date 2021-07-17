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
        driver=None,
        get=True,
        scrape=True,
        close_on_complete=True,
    ):
        self.linkedin_url = linkedin_url
        self.personProfile = {}
        self.token = None
        self.cookies = None
        self.session = requests.Session()

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

    def get_follow_page_data(self, publicIdentifier, start):
        url = 'https://www.linkedin.com/voyager/api/identity/profiles/{}/following?count=20&q=followedEntities&start={}'.format(
            publicIdentifier, start)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            'csrf-token': self.token,
        }
        res = self.session.get(url=url, headers=headers, cookies=self.cookies, verify=False)
        resp = res.json()
        page_elements = []
        total = resp['paging']['total']
        for element in resp['elements']:
            print(element)
            if 'com.linkedin.voyager.identity.shared.MiniProfile' in element['entity'].keys():
                page_elements.append({
                    'firstName': element['entity']['com.linkedin.voyager.identity.shared.MiniProfile']['firstName'],
                    'lastName': element['entity']['com.linkedin.voyager.identity.shared.MiniProfile']['lastName'],
                    'occupation': element['entity']['com.linkedin.voyager.identity.shared.MiniProfile']['occupation'],
                    'objectUrn': element['entity']['com.linkedin.voyager.identity.shared.MiniProfile']['objectUrn'],
                    'publicIdentifier': element['entity']['com.linkedin.voyager.identity.shared.MiniProfile']['publicIdentifier'],
                    'followerCount': element['followingInfo']['followerCount'],
                })

            elif 'com.linkedin.voyager.entities.shared.MiniCompany' in element['entity'].keys():
                page_elements.append({
                    'name': element['entity']['com.linkedin.voyager.entities.shared.MiniCompany']['name'],
                    'universalName': element['entity']['com.linkedin.voyager.entities.shared.MiniCompany']['universalName'],
                    'objectUrn': element['entity']['com.linkedin.voyager.entities.shared.MiniCompany']['objectUrn'],
                    'followerCount': element['followingInfo']['followerCount'],
                })
        return total, page_elements

    def get_follow_list(self, publicIdentifier):
        followList = []
        start = 0
        try:
            total, page_elements = self.get_follow_page_data(publicIdentifier, start)
            followList = page_elements
            if total > 20:
                bei = round(total/20)
                for i in range(0, bei):
                    try:
                        total, next_page_elements = self.get_follow_page_data(publicIdentifier, 20*i)
                        followList += next_page_elements
                    except Exception as e:
                        print(e)
                        pass
        except Exception as e:
            print(e)
            pass
        return followList

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
                    data = json.loads(data)
                    if 'request' in data.keys() and "com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities" in data['request']:
                        sourceId = data['body']
                    dataList.append({'dataId': dataId, 'content': data})
                except:
                    pass
        for data in dataList:
            if data['dataId'] == sourceId and 'data' in data['content'].keys():
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
                                info['profilePicture']['displayImageReference']['vectorImage']['rootUrl'],
                                info['profilePicture']['displayImageReference']['vectorImage']['artifacts'][1]['fileIdentifyingUrlPathSegment'].replace('&amp;', '&'),
                            ),
                        }
                    elif info['$type'] == 'com.linkedin.voyager.dash.identity.profile.Position':
                        persionProfile['PositionTitle'] = info['title']
                        persionProfile['PositionCompanyName'] = info['companyName']
                    elif info['$type'] == 'com.linkedin.voyager.dash.organization.Company':
                        persionProfile['companyUrl'] = info['url']
                        persionProfile['companyName'] = info['name']
                        persionProfile['companyUniversalName'] = info['universalName'] if 'universalName' in info.keys() else ''
        return persionProfile

    def get_peopleAlsoViewed(self, publicIdentifier):
        peopleAlsoViewed = []
        url = 'https://www.linkedin.com/voyager/api/identity/profiles/{}/browsemapWithDistance'.format(
            publicIdentifier)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            'csrf-token': self.token,
        }
        try:
            res = self.session.get(url=url, headers=headers, cookies=self.cookies, verify=False)
            resp = res.json()
            for relate in resp['elements']:
                user = relate['miniProfile']
                peopleAlsoViewed.append({
                    'firstName': user['firstName'],
                    'lastName': user['lastName'],
                    'occupation': user['occupation'],
                    'publicIdentifier': user['publicIdentifier'],
                    'objectUrn': user['objectUrn'],
                })
        except:
            pass
        return peopleAlsoViewed


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
            self.get_cookies()
            personProfile = self.get_profile_data(html)
            followList = self.get_follow_list(personProfile['publicIdentifier'])
            peopleAlsoViewed = self.get_peopleAlsoViewed(personProfile['publicIdentifier'])
            personProfile['followList'] = followList
            personProfile['peopleAlsoViewed'] = peopleAlsoViewed

            self.personProfile = personProfile

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