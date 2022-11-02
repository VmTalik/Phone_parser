import asyncio
import random

import aiohttp
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

start_time = time.time()
all_data = []
phone_data = []


async def get_page_data(session, page_id: int):
    """ Функция асинхронного поиска частей ссылок страниц, на которых есть номера телефонов"""
    headers = [
        {'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:47.0) Gecko/20100101 Firefox/47.0',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'},
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 5.1) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'},
        {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:53.0) Gecko/20100101 Firefox/53.0',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    ]
    if page_id:
        url = f'https://krisha.kz/prodazha/doma/?page={page_id}'
    else:
        url = f'https://krisha.kz/prodazha/doma/'
    async with session.get(url, headers=headers[random.randint(0, len(headers) - 1)]) as resp:
        assert resp.status == 200
        print(f'url: {url}')
        resp_text = await resp.text()
        soup = BeautifulSoup(resp_text, 'lxml')
        house = str(soup.find_all('div', class_='a-card__header-left'))
        houses_page_link = re.findall(r'href="/a/show/\d{9}', house)
        all_data.extend(houses_page_link)


async def load_site_data():
    """Функиия, создающая задачи для асинхронного поиска частей ссылок страниц, на которых есть номера телефонов"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        # тут количество страниц
        for page_id in range(1, 2):
            task = asyncio.create_task(get_page_data(session, page_id))
            tasks.append(task)
        await asyncio.gather(*tasks)


def phone_number_search(data):
    """Функция скрапинга. Применяется Selenium для клика по кнопке для получения номеров телефонов"""
    options = webdriver.ChromeOptions()
    options.headless = True
    options.add_experimental_option(  # настройки отключения анимации на сайте, для возможного ускорения поиска
        'prefs',
        {
            'profile.managed_default_content_settings.javascript': 2,
            'profile.managed_default_content_settings.images': 2,
            'profile.managed_default_content_settings.mixed_script': 2,
            'profile.managed_default_content_settings.media_stream': 2,
            'profile.managed_default_content_settings.stylesheets': 2
        }
    )
    for i in data:
        page_house_number = i[14:]
        try:
            browser = webdriver.Chrome(options=options)
            browser.get(f'https://krisha.kz/a/show/{page_house_number}')
            button = browser.find_element(By.CSS_SELECTOR, '.show-phones')
            button.click()
            browser.implicitly_wait(0.2)
            phone_number = browser.find_element(By.CSS_SELECTOR, '.offer__contacts-phones').text
        finally:
            browser.quit()
        phone_data.append(phone_number)


asyncio.get_event_loop().run_until_complete(load_site_data())
phone_number_search(all_data)

end_time = time.time() - start_time
print(f"\nВремя парсинга: {end_time} секунд")
print('Номера телефонов:', *[i for i in phone_data], sep='\n')
