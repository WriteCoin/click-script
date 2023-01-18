from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
import requests
import conf
import traceback
import random
from typing import Union, List
import threading
from itertools import islice

def get_profiles(authToken):
    headers = {
        'Authorization': f'Bearer {authToken}'
    }
    response = requests.get(
        'https://anty-api.com/browser_profiles', headers=headers)
    response_json = response.json()
    data = response_json['data']
    profiles = {}
    if len(data) > 0:
        for profile in data:
            profiles[profile['name']] = profile['id']
        return profiles
    raise Exception("Profiles not found")


def get_browser(profileId):
    response = requests.get(
        f"http://localhost:3001/v1.0/browser_profiles/{profileId}/start?automation=1").json()
    if 'errorObject' in response:
        raise Exception(response['errorObject']['text'])
    port = response['automation']['port']
    return port


def close_browser(profileId):
    response = requests.get(
        f"http://localhost:3001/v1.0/browser_profiles/{profileId}/stop").json()
    if not response['success']:
        print(response)


def sleep(driver, time: Union[int, float]):
    try:
        WebDriverWait(driver, float(time), float(time)).until(
            lambda driver: False
        )
    except:
        pass


def close_tabs(driver, excluded_windows: Union[List[str], None] = None):
    if excluded_windows is None:
        excluded_windows = []
    if driver is None:
        raise Exception(
            "Closing tabs is not possible, the browser is not found")
    windows = [
        window
        for window in driver.window_handles
        if window not in excluded_windows
    ]
    current_window = driver.current_window_handle
    all_tabs_closed = True
    for window in windows:
        try:
            driver.switch_to.window(window)
            driver.close()
        except:
            all_tabs_closed = False
    if current_window in excluded_windows:
        driver.switch_to.window(current_window)


def hover_element(driver, element, duration):
    ActionChains(driver, duration).move_to_element(element).perform()


def find_element(driver, selector, element=None):
    if element is None:
        return driver.find_element(selector['by'], selector['value'])
    else:
        return element.find_element(selector['by'], selector['value'])


def is_element_exists(driver, selector, element=None) -> bool:
    try:
        find_element(driver, selector, element)
    except NoSuchElementException:
        return False
    else:
        return True


DEFAULT_TIMEOUT: float = 60.00
DEFAULT_POLL_FREQUENCY: float = 0.1


def wait_element(
        driver,
        selector,
        timeout=DEFAULT_TIMEOUT,
        poll_frequency=DEFAULT_POLL_FREQUENCY,
        element=None,
):
    def cond(driver):
        return is_element_exists(driver, selector, element)

    WebDriverWait(driver, timeout, poll_frequency).until(cond)

    return find_element(driver, selector, element)


def scroll_permanent(driver, current_pos, pos):
    driver.execute_script(
        """window.scrollTo(arguments[0], arguments[1]);""", current_pos, pos)


def scroll(driver, current_pos, pos, perScroll=None, per=None):
    if perScroll is None or per is None:
        scroll_permanent(driver, current_pos, pos)
    else:
        curScroll = current_pos
        maxScroll = pos
        more = curScroll > maxScroll
        less = curScroll < maxScroll
        if (callable(perScroll)):
            get_per_scroll = perScroll
        while not ((more and curScroll <= maxScroll) or (less and curScroll >= maxScroll)):
            if not get_per_scroll is None:
                perScroll = get_per_scroll()
            # print(f"curScroll: {curScroll}")
            # print(f"perScroll: {perScroll}")
            scroll_permanent(
                driver, curScroll, less and curScroll + perScroll or curScroll - perScroll)
            if more:
                curScroll -= perScroll
            elif less:
                curScroll += perScroll
            sleep(driver, per)
        return curScroll

def wait_page_load(driver, timeout: float = DEFAULT_TIMEOUT):
    def cond(driver):
        return driver.execute_script(
            """return document.readyState === 'complete'"""
        )

    WebDriverWait(driver, timeout).until(cond)

def automation(profileId):
    port = get_browser(profileId)

    try:

        print(f"PORT: {port} - connecting to the browser")

        chrome_options = Options()
        chrome_options.add_experimental_option(
            "debuggerAddress", f"127.0.0.1:{port}")

        chrome_driver = conf.DRIVER_PATH

        driver = webdriver.Chrome(service=Service(
            executable_path=chrome_driver), options=chrome_options)

        driver.set_script_timeout(int(DEFAULT_TIMEOUT))

        driver._switch_to.new_window()

        close_tabs(driver, [driver.current_window_handle])

        driver.get(conf.URL)

        sleep(driver, random.randint(1, 3))

        print(f"PORT: {port} - page scrolling")

        # print(driver.execute_script("return window.scrollY;"))
        # curScroll = int(driver.execute_script("return window.scrollY;"))
        curScroll = 0
        def perScroll(): return random.randint(15, 100)
        maxScroll = random.randint(200, int(driver.find_element(
            By.CSS_SELECTOR, 'body').get_attribute('scrollHeight')))
        per = 0.03
        curScroll = scroll(driver, curScroll, maxScroll, perScroll, per)

        # try:
        #     driver.execute_async_script(
        #         """function getRandomIntInclusive(min, max) { min = Math.ceil(min); max = Math.floor(max); return Math.floor(Math.random() * (max - min + 1)) + min; }; var maxScroll = getRandomIntInclusive(200, document.body.scrollHeight); var curScroll = 0; var perScroll = 5; var interval = setInterval(function() { if (curScroll >= maxScroll) { clearInterval(interval); } else { window.scrollTo(curScroll, curScroll + perScroll); curScroll += perScroll; }; }, 3);""")
        # except TimeoutException:
        #     pass

        sleep(driver, random.randint(5, 10))

        print(f"PORT: {port} - search element")

        ground = driver
        for selector in conf.SELECTORS[:-1]:
            # print(selector)

            ground = wait_element(driver, selector, element=ground)

            driver.switch_to.frame(ground)

        last_selector = conf.SELECTORS[-1]

        # print(ground)

        # print(f"last selector: {last_selector}")

        element = wait_element(driver, last_selector)

        print(f"PORT: {port} - hover element")

        # driver.execute_async_script(
        #     """var maxScroll = arguments[0]; var curScroll = 0; var perScroll = 5; var interval = setInterval(function() { if (curScroll >= maxScroll) { clearInterval(interval); } else { window.scrollTo(curScroll, curScroll + perScroll); curScroll += perScroll; }; }, 3);""", scrollHeight)

        # print(driver.execute_script("return window.scrollY;"))
        # curScroll = int(driver.execute_script("return window.scrollY;"))
        def perScroll(): return random.randint(50, 100)
        maxScroll = int(element.get_attribute('scrollHeight'))
        per = 0.03
        # print(f"curScroll: {curScroll}")
        # print(f"maxScroll: {maxScroll}")

        driver.switch_to.default_content()
        scroll(driver, curScroll, maxScroll, perScroll, per)

        sleep(driver, random.randint(5, 10))

        ground = driver
        for selector in conf.SELECTORS[:-1]:
            # print(selector)

            ground = wait_element(driver, selector, element=ground)

            driver.switch_to.frame(ground)

        hover_element(driver, element, random.randint(1, 3))

        # print(element)

        print(f"PORT: {port} - click")

        element.click()

        driver.switch_to.default_content()
        
        wait_page_load(driver)

        selector_navigation = { 'by': By.XPATH, 'value': '//button[@aria-label="Navigation"]'}

        def navigate(text):
            selector = { 'by': By.PARTIAL_LINK_TEXT, 'value': text }
            if (is_element_exists(driver, selector)):
                if (is_element_exists(driver, selector_navigation)):
                    wait_element(driver, selector).click()
                nav_el = wait_element(driver, selector)
                def perScroll(): return random.randint(15, 30)
                maxScroll = 0
                per = 0.03
                scroll(driver, curScroll, maxScroll, perScroll, per)
                maxScroll = int(nav_el.get_attribute('scrollHeight'))
                scroll(driver, curScroll, maxScroll, perScroll, per)
                nav_el.click()
                wait_page_load(driver)
                sleep(driver, random.randint(5, 10))

        navigate('About')
        navigate('Home')
        navigate('Support')
        navigate('Join')
        navigate('Sign')
        navigate('Sign up')
        navigate('Privacy')

        print(f"PORT: {port} - close the browser")

        close_browser(profileId)

        print(f"PORT: {port} - success")
    except Exception as ex:
        print(traceback.format_exc())
        print(ex)
        close_browser(profileId)


def main():
    try:
        print('get profiles')
        profiles = get_profiles(conf.AUTH_TOKEN)
        profiles_str = ", ".join(list(profiles.keys()))
        print(f"Profiles: {profiles_str}")

        profiles_count = 0
        limit_profiles = conf.LIMIT_PROFILES
        max_profiles_count = len(profiles.keys())
        while profiles_count < max_profiles_count:
            profiles = dict(islice(profiles.items(), profiles_count, profiles_count + limit_profiles))
            threads = []
            for profile in profiles:
                print(f"Start automation for profile: {profile}")
                profileId = profiles[profile]
                # task = asyncio.create_task(automation(profileId))
                # task
                t = threading.Thread(target=automation,args=(profileId,))
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
            profiles_count += limit_profiles
        
    except Exception as ex:
        print(traceback.format_exc())
        print(ex)
        if not profileId is None:
            close_browser(profileId)


if __name__ == '__main__':
    main()
