import os
from linkedin_scraper import Person, actions
from selenium import webdriver


email = '123123123'
password = '12314213123'
linkedin_url = 'https://www.linkedin.com/in/winnie-lai-17578412b/'


option = webdriver.ChromeOptions()
option.add_argument('--disable-infobars')  # 禁用浏览器正在被自动化程序控制的提示
option.add_argument('--ignore-certificate-errors')
option.add_argument('lang=en_US')  # 设置语言

driver = webdriver.Chrome("./chromedriver.exe",chrome_options=option,)

actions.login(driver=driver, email=email, password=password) # if email and password isnt given, it'll prompt in terminal
person = Person(linkedin_url, driver=driver)
# user = {
#         'linkedin_url': linkedin_url,
#         'name': person.name,
#         'about': person.about,
#         'experiences': person.experiences,
#         'educations': person.educations,
#         'interests': person.interests,
#         'accomplishments': person.accomplishments,
#         'company': person.company,
#         'job_title': person.job_title,
#         'contacts': person.contacts,
#     }
print(person)