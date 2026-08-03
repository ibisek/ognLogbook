"""
This is to parse airstrips from openaip.net.

Data exports:
    @see https://www.openaip.net/data/exports?page=1&limit=200&sortBy=format&sortDesc=false&contentType=airport&format=json
"""

import json
from time import sleep
from random import randint

from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


URL_ROOT = "https://www.openaip.net/data/airports?page=1&limit=200&sortBy=name&sortDesc=false&searchOptLwc=false&searchOptRegex=false"


def wait(min=5, max=20):
    sleep(randint(min, max))


class OpenAipAirfields(object):

    def __init__(self):
        service = FirefoxService(executable_path='/snap/bin/geckodriver')

        options = FirefoxOptions()
        options.enable_downloads = True

        self.driver = webdriver.Firefox(options=options, service=service)

        self.vars = {}

    def __del__(self):
        self.driver.quit()

    def browseDetail(self):
        name, icaoCode, iataCode, alt, lat, lon = None, None, None, None, None, None

        # extract general information & elevation:
        divs = self.driver.find_elements(By.CSS_SELECTOR, 'div.info-box')
        for div in divs:
            if div.text.startswith('General Information'):
                items = div.text.split('\n')
                name = items[2]
                icaoCode = items[6]
                iataCode = items[8]

                if icaoCode == 'NIL':
                    icaoCode = None
                if iataCode == 'NIL':
                    iataCode = None

            elif div.text.startswith('Elevation'):
                items = div.text.split('\n')
                alt = int(items[2].split(' ')[0])   # [m] AMSL

                break   # we've got all we need

        # extract location coordinates:
        divs = self.driver.find_elements(By.CSS_SELECTOR, 'div.drawer-box')
        for div in divs:
            if 'Coordinates' in div.text:
                items = div.text.split('\n')
                latLon = items[4]
                lat, lon = latLon.split(',')
                lat = float(lat)
                lon = float(lon)

                break   # we've got all we need

        # sum-up"
        code = icaoCode if icaoCode else iataCode   # both can be null!!

        if code and lat and lon:
            print(name, icaoCode, iataCode, alt, lat, lon)

            airfieldRecord = {'code': code, 'lat': lat, 'lon': lon, 'alt': alt}

            with open('../../data/airfields-openAip.json', 'a') as f:
                f.write(json.dumps(airfieldRecord))
                f.write('\n')

    def browseTable(self):
        tableRows = self.driver.find_elements(By.TAG_NAME, "tr")

        for i, tr in enumerate(tableRows):
            if i == 0:
                continue  # skip the header

            # read details only for records with ICAO or IATA code
            tds = tr.find_elements(By.TAG_NAME, 'td')
            items = [td.text for td in tds]
            if not items[3]:
                continue

            threeDotsButton = WebDriverWait(tr, 120).until(
                EC.presence_of_element_located((By.TAG_NAME, 'button'))
            )
            # threeDotsButton = tr.find_elements(By.TAG_NAME, "button")[0]
            threeDotsButton.click()

            try:
                openDetailButton = WebDriverWait(self.driver, 120).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.menu-list-item'))
                )
            except Exception as ex:
                print("[ERROR] pri cekani na tlacitko:", str(ex))
                continue

            a = tr.find_element(By.TAG_NAME, 'a')
            url = a.get_property('href')

            # openDetailButton.click()
            # WebDriverWait(self.driver, 20).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, 'div.badge-component'))
            # )

            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])
            while True:
                try:
                    self.driver.get(url)
                    break
                except Exception:   # urllib3.exceptions.ReadTimeoutError
                    wait(10, 20)
            wait(2, 2)  # wait for the page to load
            self.browseDetail()
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            # backButton = self.driver.find_element(By.CSS_SELECTOR, 'div.back-to-list-section')
            # backButton.find_element(By.TAG_NAME, 'span').click()

            wait(2, 6)

    def run(self):
        self.driver.get(URL_ROOT)

        while True:
            self.browseTable()

            navButtons = self.driver.find_elements(By.CSS_SELECTOR, 'button.sub-action')

            # there are two - Previous, Next
            nextBtn = navButtons[1]
            if not nextBtn.is_enabled():
                break   # we have reached the last page

            nextBtn.click()
            wait(3, 6)


if __name__ == '__main__':

    oaa = OpenAipAirfields()
    oaa.run()

# https://www.openaip.net/data/airports?page=2&limit=200&sortBy=name&sortDesc=false&searchOptLwc=false&searchOptRegex=false
# https://www.openaip.net/data/airports?page=4&limit=200&sortBy=name&sortDesc=false&searchOptLwc=false&searchOptRegex=false
# https://www.openaip.net/data/airports?page=6&limit=200&sortBy=name&sortDesc=false&searchOptLwc=false&searchOptRegex=false