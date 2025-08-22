import os
import json
import math
import shutil
import argparse
import requests
import pandas as pd
from tqdm import tqdm
from selenium import webdriver
from pandas import json_normalize
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

"""
{
  "@context": "https://schema.org",
  "@type": [
    "Product"
  ],
  "brand": {
    "@type": "Brand",
    "name": "Suzuki"
  },
  "description": "Suzuki Wagon R 2018 for sale in Faisalabad",
  "itemCondition": "used",
  "modelDate": 2018,
  "manufacturer": "Suzuki",
  "fuelType": "Petrol",
  "name": "Suzuki Wagon R 2018 for sale in Faisalabad",
  "image": "https://cache2.pakwheels.com/ad_pictures/1267/suzuki-wagon-r-vxl-2018-126786231.jpg",
  "vehicleTransmission": "Manual",
  "vehicleEngine": {
    "@type": "EngineSpecification",
    "engineDisplacement": "1000cc"
  },
  "mileageFromOdometer": "146,000 km",
  "offers": {
    "@context": "https://schema.org",
    "@type": "Offer",
    "price": 2270000,
    "availability": "http://schema.org/InStock",
    "priceCurrency": "PKR",
    "url": "https://www.pakwheels.com/used-cars/suzuki-wagon-r-2018-for-sale-in-faisalabad-10419952"
  }
}

"""

def main(args):
    """
        A function to run the core of the selenium script
    """

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    car_name_url = args.name.lower().replace(" ", "+")
    car_listing = []
    pages = args.pages
    averages = {
        'price': 0,
        'mileage': 0
    }
    columns_not_needed = [
        '@context',
        '@type',
        'itemCondition',
        'brand.@type',
        'offers.@type',
        'offers.@context',
        'offers.availability',
        'offers.priceCurrency',
        'vehicleEngine.@type',
    ]

    folder_path = f"{car_name_url}+{args.year}"
    os.makedirs(folder_path, exist_ok=True)

    chrome_driver_path="/home/momin/Downloads/chromedriver-linux64/chromedriver"

    service = Service(executable_path=chrome_driver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)
    # driver.get("https://www.pakwheels.com/used-cars/search/-/ct_lahore/ct_faisalabad/pr_1500000_2350000/?q=wagon+r")

    for index, val in enumerate(range(pages)):
        print(f"🔄 Page {index + 1} loading...")
        driver.get(f"https://www.pakwheels.com/used-cars/search/-/ct_lahore/ct_faisalabad/pr_1500000_5000000/yr_{args.year}_{args.year}/?q={car_name_url}&page={index + 1}")
        driver.implicitly_wait(5)
        length_classified_ads = len(driver.find_elements(By.CLASS_NAME, 'classified-listing'))

        for i in range(length_classified_ads):
            ad = driver.find_elements(By.CLASS_NAME, 'classified-listing')[i]
            script = ad.find_element(By.TAG_NAME, 'script')
            script_content = script.get_attribute('innerHTML')
            script_content = json.loads(script_content)

            if script_content['name'].find("Lahore") != -1 or script_content['name'].find("Faisalabad") != -1:
                car_listing.append(script_content)
                averages['price'] += script_content['offers']['price']
                averages['mileage'] += int(script_content.get('mileageFromOdometer', '0 km').replace(' km', '').replace(',', ''))

                headers = {
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
                    "Referer": "https://www.pakwheels.com/",
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                }

                driver.get(script_content['offers']['url'])
                driver.implicitly_wait(5)

                all_images = driver.find_element(By.CLASS_NAME, 'gallery')
                for index, li in enumerate(all_images.find_elements(By.TAG_NAME, 'li')):
                    img = li.find_element(By.TAG_NAME, 'img')
                    src = img.get_attribute('data-original')
                    ad_images_path = folder_path + "/" + script_content['offers']['url'].split('-')[-1]
                    os.makedirs(ad_images_path, exist_ok=True)

                    try:
                        image = requests.get(src, headers=headers)
                        image_path = f"{ad_images_path}/{index}.jpg"
                        if "image" in image.headers.get("Content-Type", ""):
                            with open(image_path, 'wb') as f:
                                for chunk in image.iter_content(1024):
                                    f.write(chunk)
                    except:
                        pass

                driver.back()
                driver.implicitly_wait(5)



    df = json_normalize(car_listing)
    # df = df.drop(columns=columns_not_needed, errors='ignore')

    df.to_csv(f"{folder_path}/{car_name_url}+{args.year}.csv", index=False)
    shutil.make_archive(folder_path, 'zip', folder_path)
    shutil.rmtree(folder_path)

    print(f"✅ Saved {len(df)} ads to car_listings.csv")
    print(f"🚗 Car Name: {args.name}")
    print(f"Average price: {math.ceil(averages['price'] / len(df)/5000) * 5000} PKR")
    print(f"Average mileage: {math.ceil(averages['mileage'] / len(df)/1000) * 1000} KMs")
    driver.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A script that scraps PakWheels.com car listings.")
    parser.add_argument("--name", "-n", type=str,
                        help="Car name with variant to search for (e.g., 'Wagon R VXL').")
    parser.add_argument("--year", "-y", type=int,
                        help="The car model year to filter by (default: 2018).", default=2018)
    parser.add_argument("--pages", "-p", type=int, default=1,
                        help="Total number of pages to scrape (default: 1).")
    args = parser.parse_args()


    main(args)


