import requests
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import json
import re
from bs4 import BeautifulSoup
import os
import csv
import datetime
from datetime import *


class PropertyFinder:
    adsObjects = []
    images = []
    domain = 'https://www.propertyfinder.ae/'
    path = os.path.realpath(os.curdir)

    def get_page(self, url):
        """
        Attempts to get the content at `url` by making an HTTP GET request.
        If the content-type of response is some kind of HTML/XML, return the
        text content, otherwise return None.
        """
        try:
            with closing(requests.get(url, stream=True)) as resp:
                if self.is_html_response(resp):

                    # return html
                    return str(resp.content)
                else:
                    return None

        except RequestException as e:
            self.log_error(
                'Error during requests to {0} : {1}'.format(url, str(e)))
            return None

    def is_html_response(self, resp):
        """
        Returns True if the response seems to be HTML, False otherwise.
        """
        content_type = resp.headers['Content-Type'].lower()
        return (resp.status_code == 200 and content_type is not None
                and content_type.find('html') > -1)

    def log_error(self, e):
        """
        It is always a good idea to log errors.
        This function just prints them
        """
        print(e)

    def download_images(self, imgSrc):
        picName = imgSrc.split('.')[-2].split('/')[-1]+'.jpg'
        with open(picName, 'wb') as handle:
            response = requests.get(imgSrc, stream=True)

            if not response.ok:
                self.log_error(response)

            for block in response.iter_content(1024):
                if not block:
                    break
                handle.write(block)

    def find_ads_in_html(self, rawHtml):

        html = BeautifulSoup(rawHtml, 'html.parser')
        html.prettify()
        elements = html.find('div', class_='column')
        ads_cards = elements.find_all('div')
        return ads_cards

    def get_each_ad_details(self, ads_cards):

        eachAdCard = str(ads_cards[2]).split(
            '<div class="card-list__item">')[1:]

        for adDetails in eachAdCard:
            try:
                adDetails = BeautifulSoup(adDetails, 'html.parser')
                adDetails.prettify()
                # print(adDetails)

                # create advertise objevt and append it into adsObjects list to be saved in csv after looping all the ads in frist three pages
                advertise = {}
                details = adDetails.find('a')

                advertise['title'] = details.find(
                    'h2', class_='card__title card__title-link').text
                advertise['location'] = details.find(
                    'p', class_='card__location').text
                advertise['price'] = details.find(
                    'span', class_='card__price-value').text
                advertise['bedrooms'] = details.find(
                    'p', class_='card__property-amenity--bedrooms').text
                advertise['bathrooms'] = details.find(
                    'p', class_='card__property-amenity--bathrooms').text
                advertise['area'] = details.find(
                    'p', class_='card__property-amenity--area').text

                # make new folder and change dir to it.
                advertise['images_directory'] = self.make_dir(
                    advertise['title'])
                # get images page url
                imagesPageUrl = (adDetails.find(
                    'a', class_='card card--clickable').get('href'))
                # download all the images in that page
                self.save_all_images(imagesPageUrl)
                self.adsObjects.append(advertise)
            except Exception as e:
                self.log_error(e)
                pass

    def make_dir(self, adTitle):
        '''will create new folder and change directory to this folder'''
        os.chdir(self.path)
        dirName = adTitle.replace(' ', '_').replace(
            '|', '_').replace('___', '_').replace('__', '_')
        images_directory = '{}\\propertyFinder\\{}'.format(self.path, dirName)
        os.makedirs(images_directory)
        os.chdir(images_directory)
        return images_directory

    def save_all_images(self, ImagesPageurl):
        """ will send get the HTML page loop in img tag download only the src with .jpg extension."""
        url = self.domain+ImagesPageurl
        rawHtml = self.get_page(url)
        html = BeautifulSoup(rawHtml, 'html.parser')
        html.prettify()

        images= html.find_all('img')
        for img in images:
            imag_src = img.get('src')
            print(imag_src)
            if imag_src.split('.')[-1] == 'jpg':
                self.download_images(str(imag_src))
        
    def save_csv(self):
        """ loop on adsObhects and save its details in CSV file."""
        os.chdir(self.path)
        t = datetime.now().strftime("%d%b%Y %H-%M%p")
        csvColumns = self.adsObjects[0].keys()
        csvFileName = f"Property_finder_data_{t}.csv"
        try:
            with open(csvFileName, 'w') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csvColumns)
                writer.writeheader()
                for data in self.adsObjects:
                    writer.writerow(data)
        except IOError as e:
            self.log_error(f"I/O error {e}")


def main():
    try:
        for page in range(1, 4):
            propertyFinder = PropertyFinder()
            rawHtml = propertyFinder.get_page(
                'https://www.propertyfinder.ae/en/buy/properties-for-sale.html?page={}'.format(page))

            ads = propertyFinder.find_ads_in_html(rawHtml)
            ads_details = propertyFinder.get_each_ad_details(ads)
        propertyFinder.save_csv()
    except Exception as e:
        propertyFinder.log_error(
            f"{e} \n script will be exit to kill the process")
        exit()


if __name__ == '__main__':
    main()
