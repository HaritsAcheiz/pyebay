import json
import os.path
import time

import httpx
from selectolax.parser import HTMLParser
from dataclasses import dataclass
import pandas as pd
import re
from dotenv import load_dotenv

load_dotenv()
proxy = os.getenv('PROXY')

@dataclass
class EbayScraper:

    def fetch(self, url):
        headers = {
            'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0'
        }
        proxies = {
        'http://': proxy,
        'https://': proxy
        }

        retries = 0
        while retries < 3:
            try:
                with httpx.Client(headers=headers, proxies=proxies) as client:
                    response = client.get(url)
                retries = 0
                print('Fetch completed')
                break
            except Exception as e:
                print(f'Fetch retry due to {e}')
                time.sleep(3)
                retries += 1
                continue

        return response

    def first_format(self, tree):
        picture_panel = tree.css_first('div#PicturePanel')
        right_panel = tree.css_first('div#RightSummaryPanel')
        left_panel = tree.css_first('div#LeftSummaryPanel')
        more_desc = tree.css_first('div#readMoreDesc')
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
            'Compare At Price / International': '', 'Status': ''
        }

        second_options = ['None - $0', '1 year - $89']

        # check product availability
        if left_panel:
            product = empty_product.copy()
            # check for variant
            # Multi variant
            if select_box:
                # Select the options for first option
                first_options = select_box[-1].css('option')
                # Generate combinations of options
                for i, first_option in enumerate(first_options[1::]):
                    for j, second_option in enumerate(second_options):
                        option_value = first_option.attributes.get('value')
                        product = empty_product.copy()
                        if i == 0 and j == 0:
                            for data in product:
                                if data == 'Handle':
                                    try:
                                        product[data] = more_desc.css_first(
                                            'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                            strip=True)
                                    except:
                                        product[data] = more_desc.css_first(
                                            'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
                                            strip=True)
                                elif data == 'Title':
                                    product[data] = left_panel.css_first('h1.x-item-title__mainTitle').text(strip=True)
                                elif data == 'Body (HTML)':
                                    product[data] = self.get_desc(product['Handle'], product['Title'])
                                elif data == 'Vendor':
                                    for item in item_specs:
                                        cols = item.css('div.ux-layout-section-evo__col')
                                        for col in cols:
                                            try:
                                                if col.css_first('div.ux-labels-values__labels').text(
                                                        strip=True) == 'Brand':
                                                    product[data] = col.css_first('div.ux-labels-values__values').text(
                                                        strip=True)
                                            except:
                                                continue
                                elif data == 'Variant Price':
                                    product[data] = float(
                                        re.findall(
                                            r"\d+\.\d+",
                                            left_panel.css_first('div.x-price-primary').text(strip=True))[0])
                                elif data == 'Google Shopping / Condition':
                                    product[data] = left_panel.css_first('span.ux-icon-text__text > span.clipped').text(
                                        strip=True)
                                elif data == 'Image Src':
                                    try:
                                        product[data] = picture_panel.css_first(
                                            'img.ux-image-magnify__image--original').attributes.get('src')
                                    except:
                                        product[data] = picture_panel.css_first('img.img-scale-down').attributes.get(
                                            'src')
                                elif data == 'Published':
                                    product[data] = True
                                elif data == 'Option1 Name':
                                    product[data] = select_box[-1].attributes.get('selectboxlabel')
                                elif data == 'Option1 Value':
                                    product[data] = first_option.text()
                                elif data == 'Option2 Name':
                                    product[data] = 'Warranty'
                                elif data == 'Option2 Value':
                                    product[data] = second_option
                                elif data == 'Variant SKU':
                                    product[data] = (product['Handle'] + product['Option1 Value'] + product[
                                        'Option2 Value']).lower().replace(' ', '')
                                elif data == 'Variant Inventory Tracker':
                                    product[data] = 'shopify'
                                elif data == 'Variant Inventory Qty':
                                    product[data] = 10
                                elif data == 'Variant Inventory Policy':
                                    product[data] = 'deny'
                                elif data == 'Variant Fulfillment Service':
                                    product[data] = 'manual'
                                elif data == 'Variant Compare At Price':
                                    product[data] = product['Variant Price']
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
                                elif data == 'Gift Card':
                                    product[data] = False
                                elif data == 'Variant Weight Unit':
                                    product[data] = 'kg'
                                elif data == 'Status':
                                    product[data] = 'active'
                            product_df = pd.DataFrame(product, index=[0])
                            collected_df = product_df.copy()
                            main_images = self.get_main_product_images(tree)
                            product = empty_product.copy()
                            for image in main_images:
                                for data in product:
                                    if data == 'Handle':
                                        try:
                                            product[data] = more_desc.css_first(
                                                'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                                strip=True)
                                        except:
                                            product[data] = more_desc.css_first(
                                                'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
                                                strip=True)
                                    elif data == 'Image Src':
                                        product[data] = image
                                product_df = pd.DataFrame(product, index=[0])
                                collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)

                        else:
                            for data in product:
                                if data == 'Handle':
                                    try:
                                        product[data] = more_desc.css_first(
                                            'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                            strip=True)
                                    except:
                                        product[data] = more_desc.css_first(
                                            'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
                                            strip=True)
                                elif data == 'Variant Price':
                                    if j == 0:
                                        product[data] = float(self.get_price(tree, option_value)['price'])
                                    else:
                                        product[data] = float(self.get_price(tree, option_value)['price']) + 89.00
                                elif data == 'Option1 Value':
                                    product[data] = first_option.text()
                                elif data == 'Option2 Value':
                                    product[data] = second_option
                                elif data == 'Variant SKU':
                                    product[data] = (product['Handle'] + product['Option1 Value'] + product[
                                        'Option2 Value']).lower().replace(' ', '')
                                elif data == 'Variant Inventory Tracker':
                                    product[data] = 'shopify'
                                elif data == 'Variant Inventory Qty':
                                    product[data] = 10
                                elif data == 'Variant Inventory Policy':
                                    product[data] = 'deny'
                                elif data == 'Variant Fulfillment Service':
                                    product[data] = 'manual'
                                elif data == 'Variant Compare At Price':
                                    product[data] = product['Variant Price']
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
                                    product[data] = 'kg'
                                elif data == 'Status':
                                    product[data] = 'active'
                            product_df = pd.DataFrame(product, index=[0])
                            collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)

            # No Variant
            else:
                for j, second_option in enumerate(second_options):
                    if j == 0:
                        product = empty_product.copy()
                        for data in product:
                            if data == 'Handle':
                                try:
                                    product[data] = more_desc.css_first(
                                        'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                        strip=True)
                                except:
                                    product[data] = more_desc.css_first(
                                        'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
                                        strip=True)
                            elif data == 'Title':
                                product[data] = left_panel.css_first('h1.x-item-title__mainTitle').text(strip=True)
                            elif data == 'Body (HTML)':
                                product[data] = self.get_desc(product['Handle'], product['Title'])
                            elif data == 'Vendor':
                                for item in item_specs:
                                    cols = item.css('div.ux-layout-section-evo__col')
                                    for col in cols:
                                        try:
                                            if col.css_first('div.ux-labels-values__labels').text(
                                                    strip=True) == 'Brand':
                                                product[data] = col.css_first('div.ux-labels-values__values').text(
                                                    strip=True)
                                        except:
                                            continue
                            elif data == 'Variant Price':
                                product[data] = float(
                                    re.findall(
                                        r"\d+\.\d+",
                                        left_panel.css_first('div.x-price-primary').text(strip=True))[0])
                            elif data == 'Google Shopping / Condition':
                                product[data] = left_panel.css_first('span.ux-icon-text__text > span.clipped').text(
                                    strip=True)
                            elif data == 'Image Src':
                                try:
                                    product[data] = picture_panel.css_first(
                                        'img.ux-image-magnify__image--original').attributes.get('src')
                                except:
                                    product[data] = picture_panel.css_first('img.img-scale-down').attributes.get('src')
                            elif data == 'Published':
                                product[data] = True
                            elif data == 'Option1 Name':
                                product[data] = 'Warranty'
                            elif data == 'Option1 Value':
                                product[data] = second_option
                            elif data == 'Variant SKU':
                                product[data] = product['Handle']
                            elif data == 'Variant Inventory Tracker':
                                product[data] = 'shopify'
                            elif data == 'Variant Inventory Qty':
                                product[data] = 10
                            elif data == 'Variant Inventory Policy':
                                product[data] = 'deny'
                            elif data == 'Variant Fulfillment Service':
                                product[data] = 'manual'
                            elif data == 'Variant Compare At Price':
                                product[data] = product['Variant Price']
                            elif data == 'Variant Requires Shipping':
                                product[data] = True
                            elif data == 'Taxable':
                                product[data] = True
                            elif data == 'Image Position':
                                product[data] = 1
                            elif data == 'Gift Card':
                                product[data] = False
                            elif data == 'Variant Weight Unit':
                                product[data] = 'kg'
                            elif data == 'Status':
                                product[data] = 'active'
                            product_df = pd.DataFrame(product, index=[0])
                            collected_df = product_df.copy()

                        # insert all product images
                        main_images = self.get_main_product_images(tree)
                        product = empty_product.copy()
                        for image in main_images:
                            for data in product:
                                if data == 'Handle':
                                    try:
                                        product[data] = more_desc.css_first(
                                            'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                            strip=True)
                                    except:
                                        product[data] = more_desc.css_first(
                                            'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
                                            strip=True)
                                elif data == 'Image Src':
                                    product[data] = image
                            product_df = pd.DataFrame(product, index=[0])
                            collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)
                    else:
                        product = empty_product.copy()
                        for data in product:
                            if data == 'Handle':
                                try:
                                    product[data] = more_desc.css_first(
                                        'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                        strip=True)
                                except:
                                    product[data] = more_desc.css_first(
                                        'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
                                        strip=True)
                            elif data == 'Variant Price':
                                product[data] = float(
                                    re.findall(
                                        r"\d+\.\d+",
                                        left_panel.css_first('div.x-price-primary').text(strip=True))[0]) + 89.00
                            elif data == 'Option1 Value':
                                product[data] = second_option
                            elif data == 'Variant SKU':
                                product[data] = (product['Handle'] + product['Option1 Value']).lower().replace(' ', '')
                            elif data == 'Variant Inventory Tracker':
                                product[data] = 'shopify'
                            elif data == 'Variant Inventory Qty':
                                product[data] = 10
                            elif data == 'Variant Inventory Policy':
                                product[data] = 'deny'
                            elif data == 'Variant Fulfillment Service':
                                product[data] = 'manual'
                            elif data == 'Variant Compare At Price':
                                product[data] = product['Variant Price']
                            elif data == 'Variant Requires Shipping':
                                product[data] = True
                            elif data == 'Taxable':
                                product[data] = True
                            elif data == 'Variant Weight Unit':
                                product[data] = 'kg'
                            elif data == 'Status':
                                product[data] = 'active'
                        product_df = pd.DataFrame(product, index=[0])
                        collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)

            # save to csv file
            if os.path.exists('result.csv'):
                collected_df.to_csv('result.csv', index=False, mode='a', header=False)
            else:
                collected_df.to_csv('result.csv', index=False)
            print('Product Scraped')

    def second_format(self, tree):
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
            'Compare At Price / International': '', 'Status': ''
        }

        second_options = ['None - $0', '1 year - $89']

        product = empty_product.copy()
        scripts= tree.css('script')
        for script in scripts:
            if 'convertedFromValue' in script.text():
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

            # Generate combinations of options
            for i, first_option in enumerate(first_options):
                for j, second_option in enumerate(second_options):
                    option_value = first_option.id
                    product = empty_product.copy()
                    if i == 0 and j == 0:
                        for data in product:
                            if data == 'Handle':
                                spec_rows = product_detail.css('section.product-spectification > div')
                                for spec_row in spec_rows:
                                    if 'eBay Product ID' in spec_row.text(strip=True):
                                        description_lists = spec_row.css('li')
                                        for description in description_lists:
                                            if 'eBay Product ID' in description.text(strip=True):
                                                product[data] = description.css_first('div.s-value').text(strip=True)
                            elif data == 'Title':
                                product[data] = product_info.css_first('h1.product-title').text(strip=True)
                            elif data == 'Body (HTML)':
                                product[data] = product_detail.text(strip=True)
                            elif data == 'Vendor':
                                spec_rows = product_detail.css('section.product-spectification > div')
                                for spec_row in spec_rows:
                                    if 'Brand' in spec_row.text(strip=True):
                                        description_lists = spec_row.css('li')
                                        for description in description_lists:
                                            if 'Brand' in description.text(strip=True):
                                                product[data] = description.css_first('div.s-value').text(strip=True)
                            elif data == 'Variant Price':
                                price = parsed_json['o']['w'][7][2]['model']['themes']#['listings']
                                print(price)
                                # product[data] = float(re.findall(r"\d+\.\d+", price)[0])
                            elif data == 'Google Shopping / Condition':
                                product[data] = center_panel.css_first(f'div[aria-labelledby="{option_value}"]').css_first('span.cc-ts-BOLD').text(strip=True)
                            elif data == 'Image Src':
                                product[data] = picture_panel.css_first('img.vi-image-gallery__image.vi-image-gallery__image--absolute-center').attributes.get('src')
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
                                product[data] = (product['Handle'] + product['Option1 Value'] + product[
                                    'Option2 Value']).lower().replace(' ', '')
                            elif data == 'Variant Inventory Tracker':
                                product[data] = 'shopify'
                            elif data == 'Variant Inventory Qty':
                                product[data] = 10
                            elif data == 'Variant Inventory Policy':
                                product[data] = 'deny'
                            elif data == 'Variant Fulfillment Service':
                                product[data] = 'manual'
                            elif data == 'Variant Compare At Price':
                                product[data] = product['Variant Price']
                            elif data == 'Variant Requires Shipping':
                                product[data] = True
                            elif data == 'Taxable':
                                product[data] = True
                            elif data == 'Variant Image':
                                product[data] = center_panel.css_first(f'div[aria-labelledby="{option_value}"]').css_first('li').css_first('img').attributes.get('src')
                            elif data == 'Image Position':
                                product[data] = 1
                            elif data == 'Gift Card':
                                product[data] = False
                            elif data == 'Variant Weight Unit':
                                product[data] = 'kg'
                            elif data == 'Status':
                                product[data] = 'active'
                        product_df = pd.DataFrame(product, index=[0])
                        collected_df = product_df.copy()
                        main_images = self.get_main_product_images2(tree)
                        product = empty_product.copy()
                        for image in main_images:
                            for data in product:
                                if data == 'Handle':
                                    spec_rows = product_detail.css('section.product-spectification > div')
                                    for spec_row in spec_rows:
                                        if 'eBay Product ID' in spec_row.text(strip=True):
                                            description_lists = spec_row.css('li')
                                            for description in description_lists:
                                                if 'eBay Product ID' in description.text(strip=True):
                                                    product[data] = description.css_first('div.s-value').text(
                                                        strip=True)
                                elif data == 'Image Src':
                                    product[data] = image
                            product_df = pd.DataFrame(product, index=[0])
                            collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)
                        # print(collected_df)

        #             else:
        #                 for data in product:
        #                     if data == 'Handle':
        #                         try:
        #                             product[data] = more_desc.css_first(
        #                                 'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
        #                                 strip=True)
        #                         except:
        #                             product[data] = more_desc.css_first(
        #                                 'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
        #                                 strip=True)
        #                     elif data == 'Variant Price':
        #                         if j == 0:
        #                             product[data] = float(self.get_price(tree, option_value)['price'])
        #                         else:
        #                             product[data] = float(self.get_price(tree, option_value)['price']) + 89.00
        #                     elif data == 'Option1 Value':
        #                         product[data] = first_option.text()
        #                     elif data == 'Option2 Value':
        #                         product[data] = second_option
        #                     elif data == 'Variant SKU':
        #                         product[data] = (product['Handle'] + product['Option1 Value'] + product[
        #                             'Option2 Value']).lower().replace(' ', '')
        #                     elif data == 'Variant Inventory Tracker':
        #                         product[data] = 'shopify'
        #                     elif data == 'Variant Inventory Qty':
        #                         product[data] = 10
        #                     elif data == 'Variant Inventory Policy':
        #                         product[data] = 'deny'
        #                     elif data == 'Variant Fulfillment Service':
        #                         product[data] = 'manual'
        #                     elif data == 'Variant Compare At Price':
        #                         product[data] = product['Variant Price']
        #                     elif data == 'Variant Requires Shipping':
        #                         product[data] = True
        #                     elif data == 'Taxable':
        #                         product[data] = True
        #                     elif data == 'Variant Image':
        #                         try:
        #                             product[data] = self.get_variant_image(tree, option_value=option_value)
        #                         except Exception as e:
        #                             print(e)
        #                             product[data] = ''
        #                     elif data == 'Variant Weight Unit':
        #                         product[data] = 'kg'
        #                     elif data == 'Status':
        #                         product[data] = 'active'
        #                 product_df = pd.DataFrame(product, index=[0])
        #                 collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)
        #

        # No Variant
        else:
            pass
        #     for j, second_option in enumerate(second_options):
        #         if j == 0:
        #             product = empty_product.copy()
        #             for data in product:
        #                 if data == 'Handle':
        #                     try:
        #                         product[data] = more_desc.css_first(
        #                             'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
        #                             strip=True)
        #                     except:
        #                         product[data] = more_desc.css_first(
        #                             'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
        #                             strip=True)
        #                 elif data == 'Title':
        #                     product[data] = left_panel.css_first('h1.x-item-title__mainTitle').text(strip=True)
        #                 elif data == 'Body (HTML)':
        #                     product[data] = self.get_desc(product['Handle'], product['Title'])
        #                 elif data == 'Vendor':
        #                     for item in item_specs:
        #                         cols = item.css('div.ux-layout-section-evo__col')
        #                         for col in cols:
        #                             try:
        #                                 if col.css_first('div.ux-labels-values__labels').text(
        #                                         strip=True) == 'Brand':
        #                                     product[data] = col.css_first('div.ux-labels-values__values').text(
        #                                         strip=True)
        #                             except:
        #                                 continue
        #                 elif data == 'Variant Price':
        #                     product[data] = float(
        #                         re.findall(
        #                             r"\d+\.\d+",
        #                             left_panel.css_first('div.x-price-primary').text(strip=True))[0])
        #                 elif data == 'Google Shopping / Condition':
        #                     product[data] = left_panel.css_first('span.ux-icon-text__text > span.clipped').text(
        #                         strip=True)
        #                 elif data == 'Image Src':
        #                     try:
        #                         product[data] = picture_panel.css_first(
        #                             'img.ux-image-magnify__image--original').attributes.get('src')
        #                     except:
        #                         product[data] = picture_panel.css_first('img.img-scale-down').attributes.get('src')
        #                 elif data == 'Published':
        #                     product[data] = True
        #                 elif data == 'Option1 Name':
        #                     product[data] = 'Warranty'
        #                 elif data == 'Option1 Value':
        #                     product[data] = second_option
        #                 elif data == 'Variant SKU':
        #                     product[data] = product['Handle']
        #                 elif data == 'Variant Inventory Tracker':
        #                     product[data] = 'shopify'
        #                 elif data == 'Variant Inventory Qty':
        #                     product[data] = 10
        #                 elif data == 'Variant Inventory Policy':
        #                     product[data] = 'deny'
        #                 elif data == 'Variant Fulfillment Service':
        #                     product[data] = 'manual'
        #                 elif data == 'Variant Compare At Price':
        #                     product[data] = product['Variant Price']
        #                 elif data == 'Variant Requires Shipping':
        #                     product[data] = True
        #                 elif data == 'Taxable':
        #                     product[data] = True
        #                 elif data == 'Image Position':
        #                     product[data] = 1
        #                 elif data == 'Gift Card':
        #                     product[data] = False
        #                 elif data == 'Variant Weight Unit':
        #                     product[data] = 'kg'
        #                 elif data == 'Status':
        #                     product[data] = 'active'
        #                 product_df = pd.DataFrame(product, index=[0])
        #                 collected_df = product_df.copy()
        #
        #             # insert all product images
        #             main_images = self.get_main_product_images(tree)
        #             product = empty_product.copy()
        #             for image in main_images:
        #                 for data in product:
        #                     if data == 'Handle':
        #                         try:
        #                             product[data] = more_desc.css_first(
        #                                 'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
        #                                 strip=True)
        #                         except:
        #                             product[data] = more_desc.css_first(
        #                                 'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
        #                                 strip=True)
        #                     elif data == 'Image Src':
        #                         product[data] = image
        #                 product_df = pd.DataFrame(product, index=[0])
        #                 collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)
        #         else:
        #             product = empty_product.copy()
        #             for data in product:
        #                 if data == 'Handle':
        #                     try:
        #                         product[data] = more_desc.css_first(
        #                             'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
        #                             strip=True)
        #                     except:
        #                         product[data] = more_desc.css_first(
        #                             'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > ux-textspans.ux-textspans--BOLD').text(
        #                             strip=True)
        #                 elif data == 'Variant Price':
        #                     product[data] = float(
        #                         re.findall(
        #                             r"\d+\.\d+",
        #                             left_panel.css_first('div.x-price-primary').text(strip=True))[0]) + 89.00
        #                 elif data == 'Option1 Value':
        #                     product[data] = second_option
        #                 elif data == 'Variant SKU':
        #                     product[data] = (product['Handle'] + product['Option1 Value']).lower().replace(' ', '')
        #                 elif data == 'Variant Inventory Tracker':
        #                     product[data] = 'shopify'
        #                 elif data == 'Variant Inventory Qty':
        #                     product[data] = 10
        #                 elif data == 'Variant Inventory Policy':
        #                     product[data] = 'deny'
        #                 elif data == 'Variant Fulfillment Service':
        #                     product[data] = 'manual'
        #                 elif data == 'Variant Compare At Price':
        #                     product[data] = product['Variant Price']
        #                 elif data == 'Variant Requires Shipping':
        #                     product[data] = True
        #                 elif data == 'Taxable':
        #                     product[data] = True
        #                 elif data == 'Variant Weight Unit':
        #                     product[data] = 'kg'
        #                 elif data == 'Status':
        #                     product[data] = 'active'
        #             product_df = pd.DataFrame(product, index=[0])
        #             collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)
        #
        # # save to csv file
        # if os.path.exists('result.csv'):
        #     collected_df.to_csv('result.csv', index=False, mode='a', header=False)
        # else:
        #     collected_df.to_csv('result.csv', index=False)
        # print('Product Scraped')

    def get_script_data(self, tree):
        pass

    def get_data(self, response):
        print(f'Getting product data of {response.url}...')
        pd.set_option('display.max_columns', 100)
        tree = HTMLParser(response.text)
        if tree.css_first('div#LeftSummaryPanel'):
            self.first_format(tree)
        else:
            self.second_format(tree)



    def get_price(self, tree, option_value):
        script = tree.css('script')
        for item in script:
            if 'MSKU' in item.text():
                temp = item.text()

        json_data = re.search(r'\{.*\}', temp)
        if json_data:
            json_str = json_data.group()
            json_obj = json.loads(json_str)

        var_id = json_obj['w'][0][2]['model']['menuItemMap'][str(option_value)]['matchingVariationIds'][0]
        price = json_obj['w'][0][2]['model']['variationsMap'][str(var_id)]['binModel']['price']['value']['convertedFromValue']
        currency = json_obj['w'][0][2]['model']['variationsMap'][str(var_id)]['binModel']['price']['value']['convertedFromCurrency']
        result = {'var_id': var_id, 'price': price, 'currency': currency}

        return result

    def get_variant_image(self, tree, option_value):
        script = tree.css('script')
        for item in script:
            if 'MSKU' in item.text():
                temp = item.text()

        json_data = re.search(r'\{.*\}', temp)
        if json_data:
            json_str = json_data.group()
            json_obj = json.loads(json_str)
        # print(json.dumps(json_obj, indent=2))

        pic_index = json_obj['w'][0][2]['model']['menuItemPictureIndexMap'][str(option_value)]
        image_element = tree.css_first(f'div.ux-image-carousel.img-transition-medium > div[data-idx="{str(pic_index[0])}"]')
        image = image_element.css_first('img').attributes.get('data-src')
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

    def get_main_product_images2(self, tree):
        images = []
        center_panel = tree.css_first('div#hero-item')
        # image_elements = center_panel.css('div.app-theme-item-wrapper')
        image_elements = center_panel.css('div[aria-labelledby="1"]')
        print(image_elements)
        for image_element in image_elements:
            images.append(image_element.attributes.get('data-originalimg'))

        return images


    def get_desc(self, item_id, product_title):
        url = f'https://vi.vipr.ebaydesc.com/ws/eBayISAPI.dll?ViewItemDescV4&item={item_id}'
        response = self.fetch(url)
        tree = HTMLParser(response.text)
        body=''
        if len(tree.css_first('body').text()) <= 10000:
            body = tree.css_first('body').text()
        else:
            div_elements = tree.css('div')
            for element in div_elements[::-1]:
                if ('description' in element.text(strip=True).lower()) or (product_title.lower() in element.text(strip=True).lower()):
                    body = element.text(strip=True)
                    break
                else:
                    continue
        return body

    def get_product_link(self):
        pg = 1
        product_links = []
        retries = 0
        while pg < 11 and retries < 3:
            try:
                url = f'https://www.ebay.com/b/Battery-Operated-Ride-On-Toys-Accessories/145944/bn_1928511?LH_BIN=1&LH_ItemCondition=1000&mag=1&rt=nc&_pgn={str(pg)}'
                html = self.fetch(url)
                tree = HTMLParser(html.text)
                if tree.css_first('h2.srp-controls__count-heading'):
                    products = tree.css('ul.b-list__items_nofooter.srp-results.srp-grid > li')
                    for product in products:
                        product_link = product.css_first('a').attributes.get('href')
                        product_links.append(product_link)
                    print(f'page {str(pg)} scraped')
                    pg += 1
                    retries = 0
            except Exception as e:
                print(f'get product link retry due to {e}')
                retries += 1
                continue


        return product_links

    def run(self):
        # urls = self.get_product_link()
        urls = ['https://www.ebay.com/p/710160160']
        responses = [self.fetch(url) for url in urls]
        datas = [self.get_data(response) for response in responses]
        # print(datas)

if __name__ == '__main__':
    # urls = [
    #     'https://www.ebay.com/itm/126042540408',
    #     'https://www.ebay.com/itm/385740921094',
    #     'https://www.ebay.com/itm/385717993904']
    s = EbayScraper()
    s.run()