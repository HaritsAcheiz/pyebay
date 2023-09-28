import json
import os.path
import time
import httpx
from selectolax.parser import HTMLParser
from dataclasses import dataclass, field
import pandas as pd
import re
from dotenv import load_dotenv
from typing import List
from random import choice

load_dotenv()
proxy = os.getenv('PROXY')

@dataclass
class EbayScraper:
    proxies: List = field(default_factory=lambda: ['154.12.112.163:8800','192.126.196.137:8800','154.12.112.208:8800',
                                                   '192.126.194.95:8800','154.12.113.169:8800','192.126.196.93:8800',
                                                   '154.12.113.202:8800','192.126.194.135:8800','154.12.113.32:8800',
                                                   '154.12.113.91:8800']
                          )

    proxy_index: int = 0
    product_cat: str = ''

    def fetch(self, url):

        retries = 0
        while retries < 10:
            if self.proxy_index >= 10:
                self.proxy_index = 0
            proxy = self.proxies[self.proxy_index]
            useragents = ['Mozilla / 5.0(Windows NT 10.0; WOW64; rv: 52.0) Gecko / 20100101 Firefox / 52.0',
                          'Mozilla 5.0 (Windows NT 10.0; Win32; x86; rv:88.0) Gecko/20100101 Firefox/88.0.1',
                          'Mozilla 5.0 (Windows NT 10.0; Win32; x86; rv;88.0) Gecko/20100101 Firefox/88.0',
                          'Mozilla 5.0 (Windows NT 10.0; Win32; x86; rv;88.0.1) Gecko/20100101 Firefox/88.0.1',
                          'Mozilla/10.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0']
            useragent = choice(useragents)
            print(proxy)

            headers = {
                'user-agent': useragent
            }

            proxies = {
                'http://': f'http://{proxy}',
                'https://': f'http://{proxy}'
            }
            self.proxy_index += 1
            timeout = httpx.Timeout(10.0, read=20.0)
            try:
                with httpx.Client(headers=headers, proxies=proxies, timeout=timeout) as client:
                # with httpx.Client(headers=headers) as client:
                    response = client.get(url)
                retries = 0
                if response.status_code == 200:
                    print('Fetch completed')
                    break
                else:
                    print(f'Fetch retry with status code {response.status_code}')
                    time.sleep(3)
                    retries += 1
                    continue
            except Exception as e:
                print(f'Fetch retry due to {e}')
                time.sleep(3)
                retries += 1
                continue

        return response

    def standardize(self, input: str):
        clean_value = input.lower().replace('   (out of stock)', '').strip().capitalize()
        if clean_value == "Colour":
            result = "Color"
        else:
            result = clean_value

        return result

    def get_UPC(self):
        UPCS = pd.read_csv('GasScooters30KUPC.csv')
        Available_UPC = UPCS[UPCS['status'] == 'available'].iloc[0]
        UPCS.iloc[Available_UPC.name, 1] = 'used'
        UPCS.to_csv('GasScooters30KUPC.csv', index=False)

        return Available_UPC['UPC']

    def first_format(self, tree):
        print('first_format')
        print(tree.css_first('title').text())
        try:
            feedbacks = int(re.search(r'\((\d+)\)', tree.css_first('h2.fdbk-detail-list__title > span.SECONDARY').text().replace(',', '')).group(1))
        except Exception as e:
            feedbacks = 0

        picture_panel = tree.css_first('div#PicturePanel')
        right_panel = tree.css_first('div#RightSummaryPanel')
        left_panel = tree.css_first('div#LeftSummaryPanel')
        # more_desc = tree.css_first('div#readMoreDesc')
        more_desc = tree.css_first('div.tabs__content')
        item_specs = tree.css(
            'div.ux-layout-section-evo__item.ux-layout-section-evo__item--table-view > div.ux-layout-section-evo__row')
        if left_panel:
            select_box = left_panel.css('span.x-msku__select-box-wrapper > select.x-msku__select-box')
        else:
            print("Product doesn't have variant")

        empty_product = {
            'Handle': '', 'Title': '', 'Body (HTML)': '', 'Vendor': '', 'Product Category': '', 'Type': '', 'Tags': '',
            'Published': '', 'Option1 Name': '', 'Option1 Value': '', 'Option2 Name': '', 'Option2 Value': '',
            'Option3 Name': '', 'Option3 Value': '', 'Variant SKU': '', 'Variant Grams': '',
            'Variant Inventory Tracker': '', 'Variant Inventory Qty': '', 'Variant Inventory Policy': '',
            'Variant Fulfillment Service': '', 'Variant Price': '', 'Variant Compare At Price': '',
            'Variant Requires Shipping': '', 'Variant Taxable': '', 'Variant Barcode': '', 'Image Src': '',
            'Image Position': '', 'Image Alt Text': '', 'Gift Card': '', 'SEO Title': '', 'SEO Description': '',
            'Google Shopping / Google Product Category': '', 'Google Shopping / Gender': '',
            'Google Shopping / Age Group': '', 'Google Shopping / MPN': '', 'Google Shopping / AdWords Grouping': '',
            'Google Shopping / AdWords Labels': '', 'Google Shopping / Condition': '',
            'Google Shopping / Custom Product': '', 'Google Shopping / Custom Label 0': '',
            'Google Shopping / Custom Label 1': '', 'Google Shopping / Custom Label 2': '',
            'Google Shopping / Custom Label 3': '', 'Google Shopping / Custom Label 4': '', 'Variant Image': '',
            'Variant Weight Unit': '', 'Variant Tax Code': '', 'Cost per item': '', 'Price / International': '',
            'Compare At Price / International': '', 'Status': '', 'Item_Desc': {}, 'Shipping': '', 'Seller': '', 'Location':''
        }

        second_options = ['None - $0', '1 year - $89']
        third_options = ['None - $0', 'Custom license plate - $39']

        # check product availability and seller feedbacks
        if left_panel and feedbacks >= 20:
            product = empty_product.copy()
            # check for variant
            # Multi variant
            try:
                SKU = more_desc.css_first(
                    'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                    strip=True)
            except:
                SKU = more_desc.css_first(
                    'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
                    strip=True)
            if select_box:
                # Select the options for first option
                first_options = select_box[-1].css('option')
                # Generate combinations of options
                for i, first_option in enumerate(first_options[1::]):
                    for j, second_option in enumerate(second_options):
                        for k, third_option in enumerate(third_options):
                            UPC = self.get_UPC()
                            option_value = first_option.attributes.get('value')
                            product = empty_product.copy()
                            if i == 0 and j == 0 and k == 0:
                                for data in product:
                                    if data == 'Handle':
                                        product[data] = left_panel.css_first('h1.x-item-title__mainTitle').text(
                                            strip=True).lower().replace(' -', '').replace(' ', '-').replace(',', '')
                                        # try:
                                        #     product[data] = more_desc.css_first(
                                        #         'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                        #         strip=True)
                                        # except:
                                        #     product[data] = more_desc.css_first(
                                        #         'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
                                        #         strip=True)
                                    elif data == 'Title':
                                        product[data] = left_panel.css_first('h1.x-item-title__mainTitle').text(strip=True)
                                    elif data == 'Body (HTML)':
                                        product[data] = self.get_desc(SKU)
                                    elif data == 'Vendor':
                                        product[data] = 'Magic Cars'
                                        # product[data] = f"{product['Handle']}"
                                    # elif data == 'Variant Price':
                                    #     # product[data] = float(
                                    #     #     re.findall(
                                    #     #         r"\d+\.\d+", left_panel.css('div.x-price-primary')[-1].text(strip=True))[0])
                                    #     variant_price = float(re.search(r'\$\s*([\d,]+(?:\.\d+)?)', left_panel.css(
                                    #         'div.x-price-primary')[-1].text(strip=True).replace(',', '')).group(
                                    #         1))
                                    elif data == 'Variant Price':
                                        variant_price = float(self.get_price(tree, option_value)['price'])
                                        if variant_price > 100.00:
                                            variant_price_add = variant_price + 200.00
                                            self.product_cat = 'B92'
                                        else:
                                            variant_price_add = round(variant_price * 1.75, 2)
                                            self.product_cat = 'bprts'
                                        if j == 0 and k == 0:
                                            product[data] = variant_price_add
                                        elif j != 0 and k == 0:
                                            product[data] = variant_price_add + 89.00
                                        elif j == 0 and k != 0:
                                            product[data] = variant_price_add + 39.00
                                        elif j != 0 and k != 0:
                                            product[data] = variant_price_add + 39.00 + 89.00
                                    elif data == 'Google Shopping / MPN':
                                        product[data] = UPC
                                    elif data == 'Variant Barcode':
                                        product[data] = UPC
                                    elif data == 'Google Shopping / Condition':
                                        product[data] = left_panel.css_first('span.ux-icon-text__text > span.clipped').text(
                                            strip=True)
                                    elif data == 'Google Shopping / Custom Label 1':
                                        product[data] = self.product_cat
                                    elif data == 'Image Src':
                                        product[data] = self.get_variant_image(tree, option_value=option_value)
                                        if product[data] == '':
                                            product[data] = tree.css_first(
                                                f'div.ux-image-carousel.img-transition-medium > div[data-idx="0"]').css_first(
                                                'img').attributes.get('src')
                                            if product[data]:
                                                pass
                                            else:
                                                product[data] = tree.css_first(
                                                    f'div.ux-image-carousel.img-transition-medium > div[data-idx="0"]').css_first(
                                                    'img').attributes.get('data-src')
                                    elif data == 'Tags':
                                        product[data] = 'B92'
                                    elif data == 'Published':
                                        product[data] = True
                                    # elif data == 'Option1 Name':
                                    #     product[data] = select_box[-1].attributes.get('selectboxlabel')
                                    elif data == 'Option1 Name':
                                        product[data] = self.standardize(select_box[-1].attributes.get('selectboxlabel'))
                                    # elif data == 'Option1 Value':
                                    #     product[data] = first_option.text()
                                    elif data == 'Option1 Value':
                                        product[data] = self.standardize(first_option.text())
                                    elif data == 'Option2 Name':
                                        product[data] = 'Warranty'
                                    elif data == 'Option2 Value':
                                        product[data] = second_option
                                    elif data == 'Option3 Name':
                                        product[data] = 'Custom license plate'
                                    elif data == 'Option3 Value':
                                        product[data] = third_option
                                    elif data == 'Variant SKU':
                                        try:
                                            SKU = more_desc.css_first(
                                                'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                                strip=True)
                                        except:
                                            SKU = more_desc.css_first(
                                                'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
                                                strip=True)
                                        product[data] = (str(SKU) +'-'+ product['Option1 Value'] +'-'+ product[
                                            'Option2 Value'] +'-'+ product['Option3 Value']).lower().replace(' ', '')
                                    elif data == 'Variant Grams':
                                        item_weight_pattern = r'(\d+(?:\.\d+)?)\s*(\S+)'
                                        try:
                                            item_weight = re.search(item_weight_pattern, json.loads(
                                                self.get_item_desc(item_specs).replace("\'", "\""))['Item Weight'])
                                            if item_weight.group(2) in ['lbs', 'pounds', 'lb']:
                                                product[data] = float(item_weight.group(1)) * 453.6
                                            elif 'kg' in item_weight.group(2):
                                                product[data] = float(item_weight.group(1)) * 1000
                                            else:
                                                product[data] = float(item_weight.group(1))
                                        except:
                                            if float(re.search(r'\$\s*([\d,]+(?:\.\d+)?)', left_panel.css(
                                            'div.x-price-primary')[-1].text(strip=True).replace(',', '')).group(
                                            1)) > 150:
                                                product[data] = 85 * 453.6
                                            else:
                                                product[data] = 15 * 453.6
                                    # elif data == 'Variant Inventory Tracker':
                                    #     product[data] = 'shopify'
                                    # elif data == 'Variant Inventory Qty':
                                    #     product[data] = 10
                                    elif data == 'Variant Inventory Policy':
                                        product[data] = 'deny'
                                    elif data == 'Variant Fulfillment Service':
                                        product[data] = 'manual'
                                    elif data == 'Variant Compare At Price':
                                        product[data] = round(product['Variant Price'] * 1.3, 2)
                                    elif data == 'Variant Requires Shipping':
                                        product[data] = True
                                    elif data == 'Taxable':
                                        product[data] = True
                                    elif data == 'Variant Image':
                                        try:
                                            product[data] = self.get_variant_image(tree, option_value=option_value)
                                        except Exception as e:
                                            print(e)
                                            product[data] = ''
                                    elif data == 'Image Position':
                                        product[data] = 1
                                    elif data == 'Image Alt Text':
                                        product[data] = product['Variant Image']
                                    elif data == 'Gift Card':
                                        product[data] = False
                                    elif data == 'Variant Weight Unit':
                                        product[data] = 'lb'
                                    elif data == 'Cost per item':
                                        product[data] = variant_price
                                    elif data == 'Status':
                                        product[data] = 'active'
                                    elif data == 'Item_Desc':
                                        product[data] = self.get_item_desc(item_specs=item_specs)
                                    elif data == 'Shipping':
                                        try:
                                            shipping_panel = left_panel.css_first('div.ux-labels-values.col-12.ux-labels-values--shipping')
                                            product[data] = shipping_panel.css_first('span.ux-textspans.ux-textspans--BOLD').text(strip=True)
                                        except:
                                            product[data] = ''
                                    elif data == 'Seller':
                                        product[data] = tree.css_first(
                                            'h2.d-stores-info-categories__container__info__section__title').attributes.get(
                                            'title')
                                    elif data == 'Location':
                                        try:
                                            location_parent_element = tree.css_first(
                                                'div.ux-labels-values.col-12.ux-labels-values--shipping')
                                            if location_parent_element:
                                                product[data] = location_parent_element.css_first(
                                                    'span.ux-textspans.ux-textspans--SECONDARY').text(strip=True)
                                            else:
                                                location_parent_element = tree.css_first(
                                                    'ux-labels-values.col-12.ux-labels-values__column-last-row.ux-labels-values--localPickup')
                                                product[data] = location_parent_element.css_first(
                                                    'div.ux-labels-values__values.col-9 > div > div > span').text(
                                                    strip=True)
                                        except Exception as e:
                                            print('No location')
                                            product[data] = ''


                                        # location_parent_element = tree.css_first(
                                        #     'div.ux-labels-values.col-12.ux-labels-values--shipping')
                                        # product[data] = location_parent_element.css_first(
                                        #     'span.ux-textspans.ux-textspans--SECONDARY').text(strip=True)
                                product_df = pd.DataFrame(product, index=[0])
                                collected_df = product_df.copy()
                                main_images = self.get_main_product_images(tree)
                                product = empty_product.copy()
                                for image in main_images:
                                    for data in product:
                                        if data == 'Handle':
                                            product[data] = left_panel.css_first('h1.x-item-title__mainTitle').text(
                                                strip=True).lower().replace(' -', '').replace(' ', '-').replace(',', '')
                                            # try:
                                            #     product[data] = more_desc.css_first(
                                            #         'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                            #         strip=True)
                                            # except:
                                            #     product[data] = more_desc.css_first(
                                            #         'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans.ux-textspans--BOLD').text(
                                            #         strip=True)
                                        elif data == 'Image Src':
                                            product[data] = image
                                        elif data == 'Image Alt Text':
                                            product[data] = image
                                    product_df = pd.DataFrame(product, index=[0])
                                    collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)

                            else:
                                for data in product:
                                    if data == 'Handle':
                                        product[data] = left_panel.css_first('h1.x-item-title__mainTitle').text(
                                            strip=True).lower().replace(' -', '').replace(' ', '-').replace(',', '')
                                        # try:
                                        #     product[data] = more_desc.css_first(
                                        #         'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                        #         strip=True)
                                        # except:
                                        #     product[data] = more_desc.css_first(
                                        #         'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans.ux-textspans--BOLD').text(
                                        #         strip=True)
                                    elif data == 'Variant Price':
                                        variant_price = float(self.get_price(tree, option_value)['price'])
                                        if variant_price > 100.00:
                                            variant_price_add = variant_price + 200.00
                                            self.product_cat = 'B92'
                                        else:
                                            variant_price_add = round(variant_price * 1.75, 2)
                                            self.product_cat = 'bprts'
                                        if j == 0 and k == 0:
                                            product[data] = variant_price_add
                                        elif j != 0 and k == 0:
                                            product[data] = variant_price_add + 89.00
                                        elif j == 0 and k != 0:
                                            product[data] = variant_price_add + 39.00
                                        elif j != 0 and k != 0:
                                            product[data] = variant_price_add + 39.00 + 89.00
                                    elif data == 'Option1 Value':
                                        product[data] = self.standardize(first_option.text())
                                    elif data == 'Option2 Value':
                                        product[data] = second_option
                                    elif data == 'Option3 Value':
                                        product[data] = third_option
                                    elif data == 'Variant SKU':
                                        try:
                                            SKU = more_desc.css_first(
                                                'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                                strip=True)
                                        except:
                                            SKU = more_desc.css_first(
                                                'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
                                                strip=True)
                                        product[data] = (str(SKU) +'-'+ product['Option1 Value'] +'-'+ product[
                                            'Option2 Value'] +'-'+ product['Option3 Value']).lower().replace(' ', '')
                                    elif data == 'Variant Grams':
                                        item_weight_pattern = r'(\d+(?:\.\d+)?)\s*(\S+)'
                                        try:
                                            item_weight = re.search(item_weight_pattern, json.loads(
                                                self.get_item_desc(item_specs).replace("\'", "\""))['Item Weight'])
                                            if item_weight.group(2) in ['lbs', 'pounds', 'lb']:
                                                product[data] = float(item_weight.group(1)) * 453.6
                                            elif 'kg' in item_weight.group(2):
                                                product[data] = float(item_weight.group(1)) * 1000
                                            else:
                                                product[data] = float(item_weight.group(1))
                                        except:
                                            if float(re.search(r'\$\s*([\d,]+(?:\.\d+)?)', left_panel.css(
                                            'div.x-price-primary')[-1].text(strip=True).replace(',', '')).group(
                                            1)) > 150:
                                                product[data] = 85 * 453.6
                                            else:
                                                product[data] = 15 * 453.6
                                    # elif data == 'Variant Inventory Tracker':
                                    #     product[data] = 'shopify'
                                    # elif data == 'Variant Inventory Qty':
                                    #     product[data] = 10
                                    elif data == 'Variant Inventory Policy':
                                        product[data] = 'deny'
                                    elif data == 'Variant Fulfillment Service':
                                        product[data] = 'manual'
                                    elif data == 'Variant Compare At Price':
                                        product[data] = round(product['Variant Price'] * 1.3, 2)
                                    elif data == 'Variant Requires Shipping':
                                        product[data] = True
                                    elif data == 'Taxable':
                                        product[data] = True
                                    elif data == 'Variant Image':
                                        try:
                                            product[data] = self.get_variant_image(tree, option_value=option_value)
                                        except Exception as e:
                                            print(e)
                                            product[data] = ''
                                    elif data == 'Variant Weight Unit':
                                        product[data] = 'lb'
                                    elif data == 'Cost per item':
                                        product[data] = variant_price
                                    elif data == 'Status':
                                        product[data] = 'active'
                                    elif data == 'Google Shopping / MPN':
                                        product[data] = UPC
                                    elif data == 'Variant Barcode':
                                        product[data] = UPC
                                product_df = pd.DataFrame(product, index=[0])
                                collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)

            # No Variant
            else:
                for j, second_option in enumerate(second_options):
                    for k, third_option in enumerate(third_options):
                        if j == 0 and k == 0:
                            UPC = self.get_UPC()
                            product = empty_product.copy()
                            for data in product:
                                if data == 'Handle':
                                    product[data] = left_panel.css_first('h1.x-item-title__mainTitle').text(
                                        strip=True).lower().replace(' -', '').replace(' ', '-').replace(',', '')
                                    # try:
                                    #     product[data] = more_desc.css_first(
                                    #         'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                    #         strip=True)
                                    # except:
                                    #     product[data] = more_desc.css_first(
                                    #         'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans.ux-textspans--BOLD').text(
                                    #         strip=True)
                                elif data == 'Title':
                                    product[data] = left_panel.css_first('h1.x-item-title__mainTitle').text(strip=True)
                                elif data == 'Body (HTML)':
                                    product[data] = self.get_desc(SKU)
                                elif data == 'Vendor':
                                    product[data] = 'Magic Cars'
                                    # product[data] = f"{product['Handle']}"
                                elif data == 'Variant Price':
                                    # product[data] = float(
                                        # re.findall(
                                        #     r"\d+\.\d+", left_panel.css('div.x-price-primary')[-1].text(strip=True))[0])
                                    variant_price = float(re.search(r'\$\s*([\d,]+(?:\.\d+)?)', left_panel.css(
                                        'div.x-price-primary')[-1].text(strip=True).replace(',', '')).group(
                                        1))
                                    if variant_price > 100.00:
                                        product[data] = variant_price + 200.00
                                        self.product_cat = 'B92'
                                    else:
                                        product[data] = round(variant_price * 1.75, 2)
                                        self.product_cat = 'bprts'
                                    # x = self.get_variant_image(tree, 0)
                                elif data == 'Google Shopping / MPN':
                                    product[data] = UPC
                                elif data == 'Variant Barcode':
                                    product[data] = UPC
                                elif data == 'Google Shopping / Condition':
                                    product[data] = left_panel.css_first('span.ux-icon-text__text > span.clipped').text(
                                        strip=True)
                                elif data == 'Google Shopping / Custom Label 1':
                                    product[data] = self.product_cat
                                elif data == 'Image Src':
                                    try:
                                        product[data] = picture_panel.css_first(
                                            'div.ux-image-carousel-item.active.image').css_first('img').attributes.get('src')
                                    except:
                                        product[data] = picture_panel.css_first(
                                            'div.ux-image-carousel-item.active.image').css_first('img').attributes.get('src')
                                elif data == 'Tags':
                                    product[data] = 'B92'
                                elif data == 'Published':
                                    product[data] = True
                                elif data == 'Option1 Name':
                                    product[data] = 'Warranty'
                                elif data == 'Option1 Value':
                                    product[data] = second_option
                                elif data == 'Option2 Name':
                                    product[data] = 'Custom license plate'
                                elif data == 'Option2 Value':
                                    product[data] = third_option
                                elif data == 'Variant SKU':
                                    try:
                                        SKU = more_desc.css_first(
                                            'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                            strip=True)
                                    except:
                                        SKU = more_desc.css_first(
                                            'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
                                            strip=True)
                                    product[data] = (str(SKU) +'-'+ product['Option1 Value'] +'-'+ product[
                                        'Option2 Value'] +'-'+ product['Option3 Value']).lower().replace(' ', '')
                                elif data == 'Variant Grams':
                                    item_weight_pattern = r'(\d+(?:\.\d+)?)\s*(\S+)'
                                    try:
                                        item_weight = re.search(item_weight_pattern, json.loads(
                                            self.get_item_desc(item_specs).replace("\'", "\""))['Item Weight'])
                                        if item_weight.group(2) in ['lbs', 'pounds', 'lb']:
                                            product[data] = float(item_weight.group(1)) * 453.6
                                        elif 'kg' in item_weight.group(2):
                                            product[data] = float(item_weight.group(1)) * 1000
                                        else:
                                            product[data] = float(item_weight.group(1))
                                    except:
                                        if float(re.search(r'\$\s*([\d,]+(?:\.\d+)?)', left_panel.css(
                                            'div.x-price-primary')[-1].text(strip=True).replace(',', '')).group(
                                            1)) > 150:
                                            product[data] = 85 * 453.6
                                        else:
                                            product[data] = 15 * 453.6
                                # elif data == 'Variant Inventory Tracker':
                                #     product[data] = 'shopify'
                                # elif data == 'Variant Inventory Qty':
                                #     product[data] = 10
                                elif data == 'Variant Inventory Policy':
                                    product[data] = 'deny'
                                elif data == 'Variant Fulfillment Service':
                                    product[data] = 'manual'
                                elif data == 'Variant Compare At Price':
                                    product[data] = round(product['Variant Price'] * 1.3, 2)
                                elif data == 'Variant Requires Shipping':
                                    product[data] = True
                                elif data == 'Taxable':
                                    product[data] = True
                                elif data == 'Image Position':
                                    product[data] = 1
                                elif data == 'Image Alt Text':
                                    product[data] = product['Image Src']
                                elif data == 'Gift Card':
                                    product[data] = False
                                elif data == 'Variant Weight Unit':
                                    product[data] = 'lb'
                                elif data == 'Cost per item':
                                    product[data] = variant_price
                                elif data == 'Status':
                                    product[data] = 'active'
                                elif data == 'Item_Desc':
                                    product[data] = self.get_item_desc(item_specs=item_specs)
                                elif data == 'Shipping':
                                    try:
                                        shipping_panel = left_panel.css_first(
                                            'div.ux-labels-values.col-12.ux-labels-values--shipping')
                                        product[data] = shipping_panel.css_first(
                                            'span.ux-textspans.ux-textspans--BOLD').text(strip=True)
                                    except:
                                        product[data] = ''
                                elif data == 'Seller':
                                    product[data] = tree.css_first('h2.d-stores-info-categories__container__info__section__title').attributes.get('title')
                                elif data == 'Location':
                                    try:
                                        location_parent_element = tree.css_first('div.ux-labels-values.col-12.ux-labels-values--shipping')
                                        if location_parent_element:
                                            product[data] = location_parent_element.css_first('span.ux-textspans.ux-textspans--SECONDARY').text(strip=True)
                                        else:
                                            location_parent_element = tree.css_first('ux-labels-values.col-12.ux-labels-values__column-last-row.ux-labels-values--localPickup')
                                            product[data] = location_parent_element.css_first('div.ux-labels-values__values.col-9 > div > div > span').text(strip=True)
                                    except Exception as e:
                                        print('no location')
                                        product[data] = ''

                                product_df = pd.DataFrame(product, index=[0])
                                collected_df = product_df.copy()

                            # insert all product images
                            main_images = self.get_main_product_images(tree)
                            product = empty_product.copy()
                            for image in main_images:
                                for data in product:
                                    if data == 'Handle':
                                        product[data] = left_panel.css_first('h1.x-item-title__mainTitle').text(
                                            strip=True).lower().replace(' -', '').replace(' ', '-').replace(',', '')
                                        # try:
                                        #     product[data] = more_desc.css_first(
                                        #         'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                        #         strip=True)
                                        # except:
                                        #     product[data] = more_desc.css_first(
                                        #         'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans.ux-textspans--BOLD').text(
                                        #         strip=True)
                                    elif data == 'Image Src':
                                        product[data] = image
                                    elif data == 'Image Alt Text':
                                        product[data] = image
                                product_df = pd.DataFrame(product, index=[0])
                                collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)
                        else:
                            product = empty_product.copy()
                            for data in product:
                                if data == 'Handle':
                                    product[data] = left_panel.css_first('h1.x-item-title__mainTitle').text(
                                        strip=True).lower().replace(' -', '').replace(' ', '-').replace(',', '')
                                    # try:
                                    #     product[data] = more_desc.css_first(
                                    #         'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                    #         strip=True)
                                    # except:
                                    #     product[data] = more_desc.css_first(
                                    #         'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans.ux-textspans--BOLD').text(
                                    #         strip=True)
                                # elif data == 'Variant Price':
                                    # product[data] = float(
                                        # re.findall(
                                        #     r"\d+\.\d+", left_panel.css('div.x-price-primary')[-1].text(strip=True))[0]) + 89.00
                                    # product[data] = float(re.search(r'\$\s*([\d,]+(?:\.\d+)?)', left_panel.css(
                                    #     'div.x-price-primary')[-1].text(strip=True).replace(',', '')).group(
                                    #     1)) + 89.00
                                elif data == 'Variant Price':
                                    variant_price = float(re.search(r'\$\s*([\d,]+(?:\.\d+)?)', left_panel.css(
                                        'div.x-price-primary')[-1].text(strip=True).replace(',', '')).group(
                                        1))
                                    if variant_price > 100.00:
                                        variant_price_add = variant_price + 200.00
                                        self.product_cat = 'B92'
                                    else:
                                        variant_price_add = round(variant_price * 1.75, 2)
                                        self.product_cat = 'bprts'
                                    if j == 0 and k == 0:
                                        product[data] = variant_price_add
                                    elif j != 0 and k == 0:
                                        product[data] = variant_price_add + 89.00
                                    elif j == 0 and k != 0:
                                        product[data] = variant_price_add + 39.00
                                    elif j != 0 and k != 0:
                                        product[data] = variant_price_add + 39.00 + 89.00
                                elif data == 'Option1 Value':
                                    product[data] = second_option
                                elif data == 'Option2 Value':
                                    product[data] = third_option
                                elif data == 'Variant SKU':
                                    try:
                                        SKU = more_desc.css_first(
                                            'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                            strip=True)
                                    except:
                                        SKU = more_desc.css_first(
                                            'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
                                            strip=True)
                                    product[data] = (str(SKU) +'-'+ product['Option1 Value'] +'-'+ product[
                                        'Option2 Value'] +'-'+ product['Option3 Value']).lower().replace(' ', '')
                                elif data == 'Variant Grams':
                                    item_weight_pattern = r'(\d+(?:\.\d+)?)\s*(\S+)'
                                    variant_price = float(re.search(r'\$\s*([\d,]+(?:\.\d+)?)', left_panel.css(
                                        'div.x-price-primary')[-1].text(strip=True).replace(',', '')).group(
                                        1))
                                    try:
                                        item_weight = re.search(item_weight_pattern, json.loads(
                                            self.get_item_desc(item_specs).replace("\'", "\""))['Item Weight'])
                                        if item_weight.group(2) in ['lbs', 'pounds', 'lb']:
                                            product[data] = float(item_weight.group(1)) * 453.6
                                        elif 'kg' in item_weight.group(2):
                                            product[data] = float(item_weight.group(1)) * 1000
                                        else:
                                            product[data] = float(item_weight.group(1))
                                    except:
                                        if float(re.search(r'\$\s*([\d,]+(?:\.\d+)?)', left_panel.css(
                                            'div.x-price-primary')[-1].text(strip=True).replace(',', '')).group(
                                            1)) > 150:
                                            product[data] = 85 * 453.6
                                        else:
                                            product[data] = 15 * 453.6
                                # elif data == 'Variant Inventory Tracker':
                                #     product[data] = 'shopify'
                                # elif data == 'Variant Inventory Qty':
                                #     product[data] = 10
                                elif data == 'Variant Inventory Policy':
                                    product[data] = 'deny'
                                elif data == 'Variant Fulfillment Service':
                                    product[data] = 'manual'
                                elif data == 'Variant Compare At Price':
                                    product[data] = round(product['Variant Price'] * 1.3, 2)
                                elif data == 'Variant Requires Shipping':
                                    product[data] = True
                                elif data == 'Taxable':
                                    product[data] = True
                                elif data == 'Variant Weight Unit':
                                    product[data] = 'lb'
                                elif data == 'Cost per item':
                                    product[data] = variant_price
                                elif data == 'Status':
                                    product[data] = 'active'
                                elif data == 'Google Shopping / MPN':
                                    product[data] = UPC
                                elif data == 'Variant Barcode':
                                    product[data] = UPC
                            product_df = pd.DataFrame(product, index=[0])
                            collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)

            # save to csv file
            if os.path.exists('original/20230928_106-111_Desc_Original.csv'):
                collected_df.to_csv('original/20230928_106-111_Desc_Original.csv', index=False, mode='a', header=False)
            else:
                collected_df.to_csv('original/20230928_106-111_Desc_Original.csv', index=False)
            print('Product Scraped')
        else:
            pass

    def second_format(self, tree):
        print('second_format')
        try:
            feedbacks = int(
                re.search(r'\((\d+)\)', tree.css_first('h2.fdbk-detail-list__title > span.SECONDARY').text()).group(1))
        except:
            feedbacks = 0
        picture_panel = tree.css_first('div.item-image-wrapper')
        center_panel = tree.css_first('div#hero-item')
        product_info = tree.css_first('div.product-info.no-product-picture')
        product_detail = tree.css_first('div#ProductDetails')
        select_box = product_info.css('ul.themes-panel > li')

        empty_product = {
            'Handle': '', 'Title': '', 'Body (HTML)': '', 'Vendor': '', 'Product Category': '', 'Type': '', 'Tags': '',
            'Published': '', 'Option1 Name': '', 'Option1 Value': '', 'Option2 Name': '', 'Option2 Value': '',
            'Option3 Name': '', 'Option3 Value': '', 'Variant SKU': '', 'Variant Grams': '',
            'Variant Inventory Tracker': '', 'Variant Inventory Qty': '', 'Variant Inventory Policy': '',
            'Variant Fulfillment Service': '', 'Variant Price': '', 'Variant Compare At Price': '',
            'Variant Requires Shipping': '', 'Variant Taxable': '', 'Variant Barcode': '', 'Image Src': '',
            'Image Position': '', 'Image Alt Text': '', 'Gift Card': '', 'SEO Title': '', 'SEO Description': '',
            'Google Shopping / Google Product Category': '', 'Google Shopping / Gender': '',
            'Google Shopping / Age Group': '', 'Google Shopping / MPN': '', 'Google Shopping / AdWords Grouping': '',
            'Google Shopping / AdWords Labels': '', 'Google Shopping / Condition': '',
            'Google Shopping / Custom Product': '', 'Google Shopping / Custom Label 0': '',
            'Google Shopping / Custom Label 1': '', 'Google Shopping / Custom Label 2': '',
            'Google Shopping / Custom Label 3': '', 'Google Shopping / Custom Label 4': '', 'Variant Image': '',
            'Variant Weight Unit': '', 'Variant Tax Code': '', 'Cost per item': '', 'Price / International': '',
            'Compare At Price / International': '', 'Status': '', 'Item_Desc': {}, 'Shipping': '', 'Seller': '', 'Location':''
        }

        second_options = ['None - $0', '1 year - $89']

        if feedbacks >= 20:
            product = empty_product.copy()
            scripts = tree.css('script')
            for script in scripts:
                if '__prp' in script.text():
                    pattern = r'\((\{.*\})\)'
                    match = re.search(pattern, script.text())
                    if match:
                        json_data = match.group(1)
                        parsed_json = json.loads(json_data)

            # check for variant
            # Multi variant
            if select_box:
                # Select the options for first option
                first_options = select_box

                # find listing
                themes = parsed_json['o']['w'][7][2]['model']['themes']

                # Generate combinations of options
                for i, first_option in enumerate(first_options):
                    for j, second_option in enumerate(second_options):
                        UPC = self.get_UPC()
                        listingId = first_option.attributes.get('data-listing-id')
                        product = empty_product.copy()
                        if i == 0 and j == 0:
                            for data in product:
                                if data == 'Handle':
                                    product[data] = product_info.css_first('h1.product-title').text(strip=True).lower().replace(' -', '').replace(' ', '-').replace(',', '')
                                    # spec_rows = product_detail.css('section.product-spectification > div')
                                    # for spec_row in spec_rows:
                                    #     if 'eBay Product ID' in spec_row.text(strip=True):
                                    #         description_lists = spec_row.css('li')
                                    #         for description in description_lists:
                                    #             if 'eBay Product ID' in description.text(strip=True):
                                    #                 product[data] = description.css_first('div.s-value').text(strip=True)
                                elif data == 'Title':
                                    product[data] = product_info.css_first('h1.product-title').text(strip=True)
                                elif data == 'Body (HTML)':
                                    product[data] = product_detail.text(strip=True)
                                elif data == 'Vendor':
                                    product[data] = 'Magic Cars'
                                    # product[data] = f"{product['Handle']}"
                                elif data == 'Variant Price':
                                    if j == 0:
                                        for theme in themes:
                                            if theme['listings'][0]['listingId'] == listingId:
                                                product[data] = float(
                                                    theme['listings'][0]['displayPrice']['value']['value']) + 200.00
                                    else:
                                        for theme in themes:
                                            if theme['listings'][0]['listingId'] == listingId:
                                                product[data] = float(
                                                    theme['listings'][0]['displayPrice']['value']['value']) + 89.00 + 200.00
                                elif data == 'Google Shopping / MPN':
                                    product[data] = UPC
                                elif data == 'Variant Barcode':
                                    product[data] = UPC
                                elif data == 'Google Shopping / Condition':
                                    for theme in themes:
                                        if theme['listings'][0]['listingId'] == listingId:
                                            product[data] = theme['listings'][0]['__prp']['condition']['textSpans'][0]['text']
                                elif data == 'Google Shopping / Custom Label 1':
                                    product[data] = self.product_cat
                                elif data == 'Image Src':
                                    for theme in themes:
                                        if theme['listings'][0]['listingId'] == listingId:
                                            product[data] = theme['listings'][0]['image']['URL']
                                elif data == 'Published':
                                    product[data] = True
                                elif data == 'Option1 Name':
                                    product[data] = 'Theme'
                                elif data == 'Option1 Value':
                                    product[data] = first_option.css_first('span.theme-title').text(strip=True)
                                elif data == 'Option2 Name':
                                    product[data] = 'Warranty'
                                elif data == 'Option2 Value':
                                    product[data] = second_option
                                elif data == 'Variant SKU':
                                    spec_rows = product_detail.css('section.product-spectification > div')
                                    for spec_row in spec_rows:
                                        if 'eBay Product ID' in spec_row.text(strip=True):
                                            description_lists = spec_row.css('li')
                                            for description in description_lists:
                                                if 'eBay Product ID' in description.text(strip=True):
                                                    SKU = description.css_first('div.s-value').text(strip=True)
                                    product[data] = (str(SKU) +'-'+ product['Option1 Value'] +'-'+ product[
                                        'Option2 Value'] +'-'+ product['Option3 Value']).lower().replace(' ', '')
                                # elif data == 'Variant Inventory Tracker':
                                #     product[data] = 'shopify'
                                # elif data == 'Variant Inventory Qty':
                                #     product[data] = 10
                                elif data == 'Variant Inventory Policy':
                                    product[data] = 'deny'
                                elif data == 'Variant Fulfillment Service':
                                    product[data] = 'manual'
                                elif data == 'Variant Compare At Price':
                                    product[data] = round(product['Variant Price'] * 1.3, 2)
                                elif data == 'Variant Requires Shipping':
                                    product[data] = True
                                elif data == 'Taxable':
                                    product[data] = True
                                elif data == 'Variant Image':
                                    for theme in themes:
                                        if theme['listings'][0]['listingId'] == listingId:
                                            product[data] = theme['listings'][0]['image']['URL']
                                elif data == 'Image Position':
                                    product[data] = 1
                                elif data == 'Image Alt Text':
                                    product[data] = product['Variant Image']
                                elif data == 'Gift Card':
                                    product[data] = False
                                elif data == 'Variant Weight Unit':
                                    product[data] = 'lb'
                                elif data == 'Cost per item':
                                    product[data] = ''
                                elif data == 'Status':
                                    product[data] = 'active'
                                elif data == 'Item_Desc':
                                    product[data] = self.get_item_desc2(item_specs=center_panel)
                                elif data == 'Shipping':
                                    try:
                                        shipping_panel = product_info.css_first('div.ux-labels-values.col-12.ux-labels-values--shipping')
                                        product[data] = shipping_panel.css_first('span.ux-textspans.ux-textspans--BOLD').text(strip=True)
                                    except:
                                        product[data] = ''
                                elif data == 'Seller':
                                    product[data] = tree.css_first('h2.d-stores-info-categories__container__info__section__title').attributes.get('title')
                                elif data == 'Location':
                                    location_parent_element = tree.css_first('div.ux-labels-values.col-12.ux-labels-values--shipping')
                                    product[data] = location_parent_element.css_first('span.ux-textspans.ux-textspans--SECONDARY').text(strip=True)
                            product_df = pd.DataFrame(product, index=[0])
                            collected_df = product_df.copy()
                            main_images = self.get_main_product_images2(themes)
                            product = empty_product.copy()
                            for image in main_images:
                                for data in product:
                                    if data == 'Handle':
                                        product[data] = product_info.css_first('h1.product-title').text(
                                            strip=True).lower().replace(' -', '').replace(' ', '-').replace(',', '')
                                        # spec_rows = product_detail.css('section.product-spectification > div')
                                        # for spec_row in spec_rows:
                                        #     if 'eBay Product ID' in spec_row.text(strip=True):
                                        #         description_lists = spec_row.css('li')
                                        #         for description in description_lists:
                                        #             if 'eBay Product ID' in description.text(strip=True):
                                        #                 product[data] = description.css_first('div.s-value').text(
                                        #                     strip=True)
                                    elif data == 'Image Src':
                                        product[data] = image
                                    elif data == 'Image Alt Text':
                                        product[data] = image
                                product_df = pd.DataFrame(product, index=[0])
                                collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)
                        else:
                            for data in product:
                                if data == 'Handle':
                                    product[data] = product_info.css_first('h1.product-title').text(
                                        strip=True).lower().replace(' -', '').replace(' ', '-').replace(',', '')
                                    # spec_rows = product_detail.css('section.product-spectification > div')
                                    # for spec_row in spec_rows:
                                    #     if 'eBay Product ID' in spec_row.text(strip=True):
                                    #         description_lists = spec_row.css('li')
                                    #         for description in description_lists:
                                    #             if 'eBay Product ID' in description.text(strip=True):
                                    #                 product[data] = description.css_first('div.s-value').text(strip=True)
                                elif data == 'Variant Price':
                                    try:
                                        if j == 0:
                                            for theme in themes:
                                                if theme['listings'][0]['listingId'] == listingId:
                                                    product[data] = float(
                                                        theme['listings'][0]['displayPrice']['value']['value']) + 200.00
                                        else:
                                            for theme in themes:
                                                if theme['listings'][0]['listingId'] == listingId:
                                                    product[data] = float(
                                                        theme['listings'][0]['displayPrice']['value']['value']) + 89.00 + 200.00
                                    except:
                                        if j == 0:
                                            for theme in themes:
                                                if theme['listings'][0]['listingId'] == listingId:
                                                    product[data] = float(
                                                        theme['listings'][0]['logisticsCost']['value']['value']) + 200.00
                                        else:
                                            for theme in themes:
                                                if theme['listings'][0]['listingId'] == listingId:
                                                    product[data] = float(
                                                        theme['listings'][0]['logisticsCost']['value']['value']) + 89.00 + 200.00
                                elif data == 'Option1 Value':
                                    product[data] = first_option.css_first('span.theme-title').text(strip=True)
                                elif data == 'Option2 Value':
                                    product[data] = second_option
                                elif data == 'Variant SKU':
                                    spec_rows = product_detail.css('section.product-spectification > div')
                                    for spec_row in spec_rows:
                                        if 'eBay Product ID' in spec_row.text(strip=True):
                                            description_lists = spec_row.css('li')
                                            for description in description_lists:
                                                if 'eBay Product ID' in description.text(strip=True):
                                                    SKU = description.css_first('div.s-value').text(strip=True)
                                    product[data] = (str(SKU) +'-'+ product['Option1 Value'] +'-'+ product[
                                        'Option2 Value'] +'-'+ product['Option3 Value']).lower().replace(' ', '')
                                # elif data == 'Variant Inventory Tracker':
                                #     product[data] = 'shopify'
                                # elif data == 'Variant Inventory Qty':
                                #     product[data] = 10
                                elif data == 'Variant Inventory Policy':
                                    product[data] = 'deny'
                                elif data == 'Variant Fulfillment Service':
                                    product[data] = 'manual'
                                elif data == 'Variant Compare At Price':
                                    product[data] = round(product['Variant Price'] * 1.3, 2)
                                elif data == 'Variant Requires Shipping':
                                    product[data] = True
                                elif data == 'Taxable':
                                    product[data] = True
                                elif data == 'Variant Image':
                                    for theme in themes:
                                        if theme['listings'][0]['listingId'] == listingId:
                                            product[data] = theme['listings'][0]['image']['URL']
                                elif data == 'Variant Weight Unit':
                                    product[data] = 'lb'
                                elif data == 'Cost per item':
                                    product[data] = ''
                                elif data == 'Status':
                                    product[data] = 'active'
                                elif data == 'Google Shopping / MPN':
                                    product[data] = UPC
                                elif data == 'Variant Barcode':
                                    product[data] = UPC
                            product_df = pd.DataFrame(product, index=[0])
                            collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)

            # No Variant
            else:
                theme = parsed_json['o']['w'][7][3]['s']['model']
                for j, second_option in enumerate(second_options):
                    UPC = self.get_UPC()
                    product = empty_product.copy()
                    if j == 0:
                        for data in product:
                            if data == 'Handle':
                                product[data] = product_info.css_first('h1.product-title').text(
                                    strip=True).lower().replace(' -', '').replace(' ', '-').replace(',', '')
                                # spec_rows = product_detail.css('section.product-spectification > div')
                                # for spec_row in spec_rows:
                                #     if 'eBay Product ID' in spec_row.text(strip=True):
                                #         description_lists = spec_row.css('li')
                                #         for description in description_lists:
                                #             if 'eBay Product ID' in description.text(strip=True):
                                #                 product[data] = description.css_first('div.s-value').text(strip=True)
                            elif data == 'Title':
                                product[data] = product_info.css_first('h1.product-title').text(strip=True)
                            elif data == 'Body (HTML)':
                                product[data] = product_detail.text(strip=True)
                            elif data == 'Vendor':
                                product[data] = 'Magic Cars'
                                # product[data] = f"{product['Handle']}"
                            elif data == 'Variant Price':
                                product[data] = float(theme['listings'][0]['displayPrice']['value']['value']) + 200.00
                            elif data == 'Google Shopping / MPN':
                                product[data] = UPC
                            elif data == 'Variant Barcode':
                                product[data] = UPC
                            elif data == 'Google Shopping / Condition':
                                product[data] = theme['listings'][0]['__prp']['condition']['textSpans'][0]['text']
                            elif data == 'Google Shopping / Custom Label 1':
                                product[data] = self.product_cat
                            elif data == 'Image Src':
                                product[data] = theme['listings'][0]['image']['URL']
                            elif data == 'Published':
                                product[data] = True
                            elif data == 'Option1 Name':
                                product[data] = 'Warranty'
                            elif data == 'Option1 Value':
                                product[data] = second_option
                            elif data == 'Option2 Name':
                                product[data] = ''
                            elif data == 'Option2 Value':
                                product[data] = ''
                            elif data == 'Variant SKU':
                                spec_rows = product_detail.css('section.product-spectification > div')
                                for spec_row in spec_rows:
                                    if 'eBay Product ID' in spec_row.text(strip=True):
                                        description_lists = spec_row.css('li')
                                        for description in description_lists:
                                            if 'eBay Product ID' in description.text(strip=True):
                                                SKU = description.css_first('div.s-value').text(strip=True)
                                product[data] = (str(SKU) +'-'+ product['Option1 Value'] +'-'+ product[
                                    'Option2 Value'] +'-'+ product['Option3 Value']).lower().replace(' ', '')
                            # elif data == 'Variant Inventory Tracker':
                            #     product[data] = 'shopify'
                            # elif data == 'Variant Inventory Qty':
                            #     product[data] = 10
                            elif data == 'Variant Inventory Policy':
                                product[data] = 'deny'
                            elif data == 'Variant Fulfillment Service':
                                product[data] = 'manual'
                            elif data == 'Variant Compare At Price':
                                product[data] = round(product['Variant Price'] * 1.3, 2)
                            elif data == 'Variant Requires Shipping':
                                product[data] = True
                            elif data == 'Taxable':
                                product[data] = True
                            elif data == 'Variant Image':
                                product[data] = theme['listings'][0]['image']['URL']
                            elif data == 'Image Position':
                                product[data] = 1
                            elif data == 'Image Alt Text':
                                product[data] = product['Variant Image']
                            elif data == 'Gift Card':
                                product[data] = False
                            elif data == 'Variant Weight Unit':
                                product[data] = 'lb'
                            elif data == 'Cost per item':
                                product[data] = ''
                            elif data == 'Status':
                                product[data] = 'active'
                            elif data == 'Item_Desc':
                                product[data] = self.get_item_desc2(item_specs=center_panel)
                            elif data == 'Shipping':
                                try:
                                    shipping_panel = product_info.css_first(
                                        'div.ux-labels-values.col-12.ux-labels-values--shipping')
                                    product[data] = shipping_panel.css_first(
                                        'span.ux-textspans.ux-textspans--BOLD').text(strip=True)
                                except:
                                    product[data] = ''
                            elif data == 'Seller':
                                product[data] = tree.css_first(
                                    'h2.d-stores-info-categories__container__info__section__title').attributes.get(
                                    'title')
                            elif data == 'Location':
                                location_parent_element = tree.css_first(
                                    'div.ux-labels-values.col-12.ux-labels-values--shipping')
                                product[data] = location_parent_element.css_first(
                                    'span.ux-textspans.ux-textspans--SECONDARY').text(strip=True)
                        product_df = pd.DataFrame(product, index=[0])
                        collected_df = product_df.copy()
                        main_images = self.get_main_product_images2(theme)
                        product = empty_product.copy()
                        for image in main_images:
                            for data in product:
                                if data == 'Handle':
                                    product[data] = product_info.css_first('h1.product-title').text(
                                        strip=True).lower().replace(' -', '').replace(' ', '-').replace(',', '')
                                #     spec_rows = product_detail.css('section.product-spectification > div')
                                #     for spec_row in spec_rows:
                                #         if 'eBay Product ID' in spec_row.text(strip=True):
                                #             description_lists = spec_row.css('li')
                                #             for description in description_lists:
                                #                 if 'eBay Product ID' in description.text(strip=True):
                                #                     product[data] = description.css_first('div.s-value').text(
                                #                         strip=True)
                                elif data == 'Image Src':
                                    product[data] = image
                                elif data == 'Image Alt Text':
                                    product[data] = image
                            product_df = pd.DataFrame(product, index=[0])
                            collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)
                    else:
                        for data in product:
                            if data == 'Handle':
                                product[data] = product_info.css_first('h1.product-title').text(
                                    strip=True).lower().replace(' -', '').replace(' ', '-').replace(',', '')
                                # spec_rows = product_detail.css('section.product-spectification > div')
                                # for spec_row in spec_rows:
                                #     if 'eBay Product ID' in spec_row.text(strip=True):
                                #         description_lists = spec_row.css('li')
                                #         for description in description_lists:
                                #             if 'eBay Product ID' in description.text(strip=True):
                                #                 product[data] = description.css_first('div.s-value').text(strip=True)
                            elif data == 'Variant Price':
                                product[data] = float(theme['listings'][0]['displayPrice']['value']['value']) + 89.00 + 200.00
                            elif data == 'Option1 Value':
                                product[data] = second_option
                            elif data == 'Variant SKU':
                                spec_rows = product_detail.css('section.product-spectification > div')
                                for spec_row in spec_rows:
                                    if 'eBay Product ID' in spec_row.text(strip=True):
                                        description_lists = spec_row.css('li')
                                        for description in description_lists:
                                            if 'eBay Product ID' in description.text(strip=True):
                                                SKU = description.css_first('div.s-value').text(strip=True)
                                product[data] = (str(SKU) +'-'+ product['Option1 Value'] +'-'+ product[
                                    'Option2 Value'] +'-'+ product['Option3 Value']).lower().replace(' ', '')
                            # elif data == 'Variant Inventory Tracker':
                            #     product[data] = 'shopify'
                            # elif data == 'Variant Inventory Qty':
                            #     product[data] = 10
                            elif data == 'Variant Inventory Policy':
                                product[data] = 'deny'
                            elif data == 'Variant Fulfillment Service':
                                product[data] = 'manual'
                            elif data == 'Variant Compare At Price':
                                product[data] = round(product['Variant Price'] * 1.3, 2)
                            elif data == 'Variant Requires Shipping':
                                product[data] = True
                            elif data == 'Taxable':
                                product[data] = True
                            elif data == 'Variant Image':
                                product[data] = theme['listings'][0]['image']['URL']
                            elif data == 'Variant Weight Unit':
                                product[data] = 'lb'
                            elif data == 'Cost per item':
                                product[data] = ''
                            elif data == 'Status':
                                product[data] = 'active'
                            elif data == 'Google Shopping / MPN':
                                product[data] = UPC
                            elif data == 'Variant Barcode':
                                product[data] = UPC
                        product_df = pd.DataFrame(product, index=[0])
                        collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)

            # save to csv file
            if os.path.exists('original/20230928_106-111_Desc_Original.csv'):
                collected_df.to_csv('original/20230928_106-111_Desc_Original.csv', index=False, mode='a', header=False)
            else:
                collected_df.to_csv('original/20230928_106-111_Desc_Original.csv', index=False)
            print('Product Scraped')
        else:
            pass


    def get_data(self, response):
        print(f'Getting product data of {response.url}...')
        retries = 0
        while retries < 3:
            tree = HTMLParser(response.text)
            if tree.css_first('div.tabs__content'):
                flag = tree.css_first('div.product-info.no-product-picture')
                if flag:
                    self.second_format(tree)
                    break
                else:
                    self.first_format(tree)
                    break
            else:
                response = self.fetch(response.url)
                retries += 1
                continue

    def get_data_v2(self, response):
        print(f'Getting product data of {response.url}...')
        retries = 0
        while retries < 3:
            tree = HTMLParser(response.text)
            if tree.css_first('div#readMoreDesc'):
                flag = tree.css_first('div.product-info.no-product-picture')
                if flag:
                    self.second_format(tree)
                    break
                else:
                    self.first_format(tree)
                    break
            else:
                response = self.fetch(response.url)
                retries += 1
                continue

    def get_price(self, tree, option_value):
        script = tree.css('script')
        for item in script:
            if 'menuItemMap' in item.text():
                temp = item.text()
                break

        json_data = temp.split('concat', 1)[1][1:-1]

        if json_data:
            json_obj = json.loads(json_data)
            # print(json.dumps(json_obj, indent=2))

        var_id = json_obj['o']['w'][0][2]['model']['modules']['MSKU']['menuItemMap'][str(option_value)]['matchingVariationIds'][0]
        price = json_obj['o']['w'][0][2]['model']['modules']['MSKU']['variationsMap'][str(var_id)]['binModel']['price']['value']['value']
        currency = json_obj['o']['w'][0][2]['model']['modules']['MSKU']['variationsMap'][str(var_id)]['binModel']['price']['value']['currency']
        result = {'var_id': var_id, 'price': price, 'currency': currency}

        # try:
        #     var_id = json_obj['w'][0][2]['model']['menuItemMap'][str(option_value)]['matchingVariationIds'][0]
        #     price = json_obj['w'][0][2]['model']['variationsMap'][str(var_id)]['binModel']['price']['value']['convertedFromValue']
        #     currency = json_obj['w'][0][2]['model']['variationsMap'][str(var_id)]['binModel']['price']['value']['convertedFromCurrency']
        #     result = {'var_id': var_id, 'price': price, 'currency': currency}
        # except:
        #     var_id = json_obj['w'][0][2]['model']['menuItemMap'][str(option_value)]['matchingVariationIds'][0]
        #     price = json_obj['w'][0][2]['model']['variationsMap'][str(var_id)]['binModel']['price']['value'][
        #         'value']
        #     currency = json_obj['w'][0][2]['model']['variationsMap'][str(var_id)]['binModel']['price']['value'][
        #         'currency']
        #     result = {'var_id': var_id, 'price': price, 'currency': currency}

        return result

    def get_variant_image(self, tree, option_value):
        script = tree.css('script')
        for item in script:
            # print(item.text())
            if 'MSKU' in item.text():
                temp = item.text()
                break

        json_data = temp.split('concat', 1)[1][1:-1]

        if json_data:
            json_obj = json.loads(json_data)
            # print(json.dumps(json_obj, indent=2))

        try:
            pic_index = json_obj['o']['w'][0][2]['model']['modules']['MSKU']['menuItemPictureIndexMap'][str(option_value)]
            image_element = tree.css_first(f'div.ux-image-carousel.img-transition-medium > div[data-idx="{str(pic_index[0])}"]')
            image = image_element.css_first('img').attributes.get('data-src')
        except:
            image = ''
        return image

    def get_main_product_images(self, tree):
        images = []
        pic_index = 0
        while 1:
            image_element = tree.css_first(f'div.ux-image-carousel.img-transition-medium > div[data-idx="{str(pic_index)}"]')
            if image_element:
                image = image_element.css_first('img').attributes.get('data-src')
                if image:
                    images.append(image)
                else:
                    image = image_element.css_first('img').attributes.get('src')
                    images.append(image)
                pic_index += 1
            else:
                break
        return images

    def get_main_product_images2(self, themes):
        images = []
        if type(themes) == 'list':
            for theme in themes:
                image_list = theme['listings'][0]['__prp']['additionalImages']
                for i in image_list:
                    image = i['URL']
                    images.append(image)
        else:
            image_list = themes['listings'][0]['__prp']['additionalImages']
            for i in image_list:
                image = i['URL']
                images.append(image)
        return images

    def get_desc(self, item_id):
        url = f'https://vi.vipr.ebaydesc.com/ws/eBayISAPI.dll?ViewItemDescV4&item={item_id}'
        response = self.fetch(url)
        tree = HTMLParser(response.text)
        elements_text = []
        if len(tree.css_first('body').text()) <= 8000:
            body = tree.css_first('body').text()

        else:
            elements = tree.css("div")
            for element in elements:
                if '<style>' in element.html:
                    continue
                else:
                    elements_text.append(element.text(strip=True))
            body = '\n'.join(elements_text)
            if len(body) > 8000:
                body = body[0:8000]
        return body

    def get_product_link(self):
        pg = 106
        product_links = []
        retries = 0
        while pg < 111 and retries < 3:
            try:
                url = f'https://www.ebay.com/b/Battery-Operated-Ride-On-Toys-Accessories/145944/bn_1928511?LH_BIN=1&LH_ItemCondition=1000&mag=1&rt=nc&_pgn={str(pg)}&_sop=16&&_fcid=1'
                html = self.fetch(url)
                tree = HTMLParser(html.text)
                # print(tree.html)
                if tree.css_first('h2.srp-controls__count-heading'):
                    # products = tree.css('ul.b-list__items_nofooter.srp-results.srp-grid > li')
                    products = tree.css('ul.b-list__items_nofooter > li')
                    print(len(products))
                    for product in products:
                        product_link = product.css_first('a').attributes.get('href')
                        product_links.append(product_link)
                    print(f'page {str(pg)} scraped')
                    pg += 1
                    retries = 0
                else:
                    retries += 1
            except Exception as e:
                print(f'get product link retry due to {e}')
                retries += 1
                continue
        print(f'{len(product_links)} product links collected')

        return product_links

    def eBayAPI(self):
        pass

    def get_item_desc(self, item_specs):
        temp_dict = {}
        for item in item_specs:
            cols = item.css('div.ux-layout-section-evo__col')
            if cols:
                for col in cols:
                    if col.css_first('div.ux-labels-values__values'):
                        if col.css_first('div.ux-labels-values__labels').text(strip=True) in ['UPC', 'MPN', 'Country/Region of Manufacture', 'Condition', 'Warranty', 'Returns']:
                            continue
                        else:
                            temp_dict[col.css_first('div.ux-labels-values__labels').text(strip=True)] = col.css_first('div.ux-labels-values__values').text(strip=True)
                    else:
                        continue
        return str(temp_dict)

    def get_item_desc2(self, item_specs):
        temp_dict = {}
        for item in item_specs:
            cols = item.css('div.ux-layout-section-evo__col')
            if cols:
                for col in cols:
                    if col.css_first('div.ux-labels-values__values'):
                        if col.css_first('div.ux-labels-values__labels').text(strip=True) in ['UPC', 'MPN',
                                                                                              'Country/Region of Manufacture',
                                                                                              'Condition']:
                            continue
                        else:
                            temp_dict[col.css_first('div.ux-labels-values__labels').text(strip=True)] = col.css_first(
                                'div.ux-labels-values__values').text(strip=True)
                    else:
                        continue
        return str(temp_dict)

    def run(self):
        urls = self.get_product_link()
        # urls = ['https://www.ebay.com/itm/20230928_106-111_Desc']
        responses = [self.fetch(url) for url in urls]
        datas = [self.get_data(response) for response in responses]

if __name__ == '__main__':
    s = EbayScraper()
    s.run()