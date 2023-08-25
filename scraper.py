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
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0'
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
                if response.status_code == 200:
                    print('Fetch completed')
                    break
                else:
                    print(f'Fetch retry with status code{response.status_code}')
                    time.sleep(3)
                    retries += 1
                    continue
            except Exception as e:
                print(f'Fetch retry due to {e}')
                time.sleep(3)
                retries += 1
                continue

        return response

    def first_format(self, tree):
        try:
            feedbacks = int(re.search(r'\((\d+)\)', tree.css_first('h2.fdbk-detail-list__title > span.SECONDARY').text()).group(1))
        except:
            feedbacks = 0
        print(feedbacks)

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

        # check product availability and seller feedbacks
        if left_panel and feedbacks >= 20:
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
                                    product[data] = f"{product['Handle']}"
                                    # for item in item_specs:
                                    #     cols = item.css('div.ux-layout-section-evo__col')
                                    #     for col in cols:
                                    #         try:
                                    #             if col.css_first('div.ux-labels-values__labels').text(
                                    #                     strip=True) == 'Brand':
                                    #                 product[data] = col.css_first('div.ux-labels-values__values').text(
                                    #                     strip=True)
                                    #         except:
                                    #             continue
                                elif data == 'Variant Price':
                                    product[data] = float(
                                        re.findall(
                                            r"\d+\.\d+", left_panel.css('div.x-price-primary')[-1].text(strip=True))[0])
                                elif data == 'Google Shopping / Condition':
                                    product[data] = left_panel.css_first('span.ux-icon-text__text > span.clipped').text(
                                        strip=True)
                                elif data == 'Image Src':
                                    try:
                                        product[data] = picture_panel.css_first(
                                            'div.ux-image-carousel-item.draft.image').css_first('img').attributes.get(
                                            'src')
                                    except:
                                        product[data] = picture_panel.css_first(
                                            'div.ux-image-carousel-item.active.image').css_first('img').attributes.get(
                                            'src')
                                elif data == 'Published':
                                    product[data] = False
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
                                    product[data] = 'draft'
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
                                                'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans.ux-textspans--BOLD').text(
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
                                            'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans.ux-textspans--BOLD').text(
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
                                    product[data] = 'draft'
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
                                        'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans.ux-textspans--BOLD').text(
                                        strip=True)
                            elif data == 'Title':
                                product[data] = left_panel.css_first('h1.x-item-title__mainTitle').text(strip=True)
                            elif data == 'Body (HTML)':
                                product[data] = self.get_desc(product['Handle'], product['Title'])
                            elif data == 'Vendor':
                                product[data] = f"{product['Handle']}"
                                # for item in item_specs:
                                #     cols = item.css('div.ux-layout-section-evo__col')
                                #     for col in cols:
                                #         try:
                                #             if col.css_first('div.ux-labels-values__labels').text(
                                #                     strip=True) == 'Brand':
                                #                 product[data] = col.css_first('div.ux-labels-values__values').text(
                                #                     strip=True)
                                #         except:
                                #             continue
                            elif data == 'Variant Price':
                                product[data] = float(
                                    re.findall(
                                        r"\d+\.\d+", left_panel.css('div.x-price-primary')[-1].text(strip=True))[0])
                            elif data == 'Google Shopping / Condition':
                                product[data] = left_panel.css_first('span.ux-icon-text__text > span.clipped').text(
                                    strip=True)
                            elif data == 'Image Src':
                                try:
                                    product[data] = picture_panel.css_first(
                                        'div.ux-image-carousel-item.draft.image').css_first('img').attributes.get('src')
                                except:
                                    product[data] = picture_panel.css_first(
                                        'div.ux-image-carousel-item.active.image').css_first('img').attributes.get('src')
                            elif data == 'Published':
                                product[data] = False
                            elif data == 'Option1 Name':
                                product[data] = 'Warranty'
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
                            elif data == 'Image Position':
                                product[data] = 1
                            elif data == 'Gift Card':
                                product[data] = False
                            elif data == 'Variant Weight Unit':
                                product[data] = 'kg'
                            elif data == 'Status':
                                product[data] = 'draft'
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
                                            'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans.ux-textspans--BOLD').text(
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
                                        'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans.ux-textspans--BOLD').text(
                                        strip=True)
                            elif data == 'Variant Price':
                                product[data] = float(
                                    re.findall(
                                        r"\d+\.\d+", left_panel.css('div.x-price-primary')[-1].text(strip=True))[0]) + 89.00
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
                                product[data] = 'draft'
                        product_df = pd.DataFrame(product, index=[0])
                        collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)

            # save to csv file
            if os.path.exists('result2.csv'):
                collected_df.to_csv('result2.csv', index=False, mode='a', header=False)
            else:
                collected_df.to_csv('result2.csv', index=False)
            print('Product Scraped')
        else:
            pass

    def second_format(self, tree):
        try:
            feedbacks = int(
                re.search(r'\((\d+)\)', tree.css_first('h2.fdbk-detail-list__title > span.SECONDARY').text()).group(1))
        except:
            feedbacks = 0
        print(feedbacks)
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

        if feedbacks >= 20:
            product = empty_product.copy()
            scripts= tree.css('script')
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
                        listingId = first_option.attributes.get('data-listing-id')
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
                                    product[data] = f"{product['Handle']}"
                                    # spec_rows = product_detail.css('section.product-spectification > div')
                                    # for spec_row in spec_rows:
                                    #     if 'Brand' in spec_row.text(strip=True):
                                    #         description_lists = spec_row.css('li')
                                    #         for description in description_lists:
                                    #             if 'Brand' in description.text(strip=True):
                                    #                 product[data] = description.css_first('div.s-value').text(strip=True)
                                elif data == 'Variant Price':
                                    if j == 0:
                                        for theme in themes:
                                            if theme['listings'][0]['listingId'] == listingId:
                                                product[data] = float(
                                                    theme['listings'][0]['displayPrice']['value']['value'])
                                    else:
                                        for theme in themes:
                                            if theme['listings'][0]['listingId'] == listingId:
                                                product[data] = float(
                                                    theme['listings'][0]['displayPrice']['value']['value']) + 89.00
                                elif data == 'Google Shopping / Condition':
                                    for theme in themes:
                                        if theme['listings'][0]['listingId'] == listingId:
                                            product[data] = theme['listings'][0]['__prp']['condition']['textSpans'][0]['text']
                                elif data == 'Image Src':
                                    for theme in themes:
                                        if theme['listings'][0]['listingId'] == listingId:
                                            product[data] = theme['listings'][0]['image']['URL']
                                elif data == 'Published':
                                    product[data] = False
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
                                    for theme in themes:
                                        if theme['listings'][0]['listingId'] == listingId:
                                            product[data] = theme['listings'][0]['image']['URL']
                                elif data == 'Image Position':
                                    product[data] = 1
                                elif data == 'Gift Card':
                                    product[data] = False
                                elif data == 'Variant Weight Unit':
                                    product[data] = 'kg'
                                elif data == 'Status':
                                    product[data] = 'draft'
                            product_df = pd.DataFrame(product, index=[0])
                            collected_df = product_df.copy()
                            main_images = self.get_main_product_images2(themes)
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
                        else:
                            for data in product:
                                if data == 'Handle':
                                    spec_rows = product_detail.css('section.product-spectification > div')
                                    for spec_row in spec_rows:
                                        if 'eBay Product ID' in spec_row.text(strip=True):
                                            description_lists = spec_row.css('li')
                                            for description in description_lists:
                                                if 'eBay Product ID' in description.text(strip=True):
                                                    product[data] = description.css_first('div.s-value').text(strip=True)
                                elif data == 'Variant Price':
                                    try:
                                        if j == 0:
                                            for theme in themes:
                                                if theme['listings'][0]['listingId'] == listingId:
                                                    product[data] = float(
                                                        theme['listings'][0]['displayPrice']['value']['value'])
                                        else:
                                            for theme in themes:
                                                if theme['listings'][0]['listingId'] == listingId:
                                                    product[data] = float(
                                                        theme['listings'][0]['displayPrice']['value']['value']) + 89.00
                                    except:
                                        if j == 0:
                                            for theme in themes:
                                                if theme['listings'][0]['listingId'] == listingId:
                                                    product[data] = float(
                                                        theme['listings'][0]['logisticsCost']['value']['value'])
                                        else:
                                            for theme in themes:
                                                if theme['listings'][0]['listingId'] == listingId:
                                                    product[data] = float(
                                                        theme['listings'][0]['logisticsCost']['value']['value']) + 89.00
                                elif data == 'Option1 Value':
                                    product[data] = first_option.css_first('span.theme-title').text(strip=True)
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
                                    for theme in themes:
                                        if theme['listings'][0]['listingId'] == listingId:
                                            product[data] = theme['listings'][0]['image']['URL']
                                elif data == 'Variant Weight Unit':
                                    product[data] = 'kg'
                                elif data == 'Status':
                                    product[data] = 'draft'
                            product_df = pd.DataFrame(product, index=[0])
                            collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)

            # No Variant
            else:
                theme = parsed_json['o']['w'][7][3]['s']['model']
                for j, second_option in enumerate(second_options):
                    product = empty_product.copy()
                    if j == 0:
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
                                product[data] = f"{product['Handle']}"
                                # spec_rows = product_detail.css('section.product-spectification > div')
                                # for spec_row in spec_rows:
                                #     if 'Brand' in spec_row.text(strip=True):
                                #         description_lists = spec_row.css('li')
                                #         for description in description_lists:
                                #             if 'Brand' in description.text(strip=True):
                                #                 product[data] = description.css_first('div.s-value').text(strip=True)
                            elif data == 'Variant Price':
                                product[data] = float(theme['listings'][0]['displayPrice']['value']['value'])
                            elif data == 'Google Shopping / Condition':
                                product[data] = theme['listings'][0]['__prp']['condition']['textSpans'][0]['text']
                            elif data == 'Image Src':
                                product[data] = theme['listings'][0]['image']['URL']
                            elif data == 'Published':
                                product[data] = False
                            elif data == 'Option1 Name':
                                product[data] = 'Warranty'
                            elif data == 'Option1 Value':
                                product[data] = second_option
                            elif data == 'Option2 Name':
                                product[data] = ''
                            elif data == 'Option2 Value':
                                product[data] = ''
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
                                product[data] = theme['listings'][0]['image']['URL']
                            elif data == 'Image Position':
                                product[data] = 1
                            elif data == 'Gift Card':
                                product[data] = False
                            elif data == 'Variant Weight Unit':
                                product[data] = 'kg'
                            elif data == 'Status':
                                product[data] = 'draft'
                        product_df = pd.DataFrame(product, index=[0])
                        collected_df = product_df.copy()
                        main_images = self.get_main_product_images2(theme)
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
                    else:
                        for data in product:
                            if data == 'Handle':
                                spec_rows = product_detail.css('section.product-spectification > div')
                                for spec_row in spec_rows:
                                    if 'eBay Product ID' in spec_row.text(strip=True):
                                        description_lists = spec_row.css('li')
                                        for description in description_lists:
                                            if 'eBay Product ID' in description.text(strip=True):
                                                product[data] = description.css_first('div.s-value').text(strip=True)
                            elif data == 'Variant Price':
                                product[data] = float(theme['listings'][0]['displayPrice']['value']['value']) + 89.00
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
                            elif data == 'Variant Image':
                                product[data] = theme['listings'][0]['image']['URL']
                            elif data == 'Variant Weight Unit':
                                product[data] = 'kg'
                            elif data == 'Status':
                                product[data] = 'draft'
                        product_df = pd.DataFrame(product, index=[0])
                        collected_df = pd.concat([collected_df, product_df.copy()], ignore_index=True)

            # save to csv file
            if os.path.exists('result2.csv'):
                collected_df.to_csv('result2.csv', index=False, mode='a', header=False)
            else:
                collected_df.to_csv('result2.csv', index=False)
            print('Product Scraped')
        else:
            pass


    def get_data(self, response):
        print(f'Getting product data of {response.url}...')
        retries = 0
        while retries < 3:
            tree = HTMLParser(response.text)
            if tree.css_first('div#readMoreDesc'):
                flag = tree.css_first('div.product-info no-product-picture')
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
            if 'MSKU' in item.text():
                temp = item.text()

        json_data = re.search(r'\{.*\}', temp)
        if json_data:
            json_str = json_data.group()
            json_obj = json.loads(json_str)
        try:
            var_id = json_obj['w'][0][2]['model']['menuItemMap'][str(option_value)]['matchingVariationIds'][0]
            price = json_obj['w'][0][2]['model']['variationsMap'][str(var_id)]['binModel']['price']['value']['convertedFromValue']
            currency = json_obj['w'][0][2]['model']['variationsMap'][str(var_id)]['binModel']['price']['value']['convertedFromCurrency']
            result = {'var_id': var_id, 'price': price, 'currency': currency}
        except:
            var_id = json_obj['w'][0][2]['model']['menuItemMap'][str(option_value)]['matchingVariationIds'][0]
            price = json_obj['w'][0][2]['model']['variationsMap'][str(var_id)]['binModel']['price']['value'][
                'value']
            currency = json_obj['w'][0][2]['model']['variationsMap'][str(var_id)]['binModel']['price']['value'][
                'currency']
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
        while pg < 3 and retries < 3:
            try:
                url = f'https://www.ebay.com/b/Battery-Operated-Ride-On-Toys-Accessories/145944/bn_1928511?LH_BIN=1&LH_ItemCondition=1000&mag=1&rt=nc&_pgn={str(pg)}&_sop=16'
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
                else:
                    break
            except Exception as e:
                print(f'get product link retry due to {e}')
                retries += 1
                continue
        print(f'{len(product_links)} product links collected')

        return product_links

    def run(self):
        # urls = self.get_product_link()
        urls = ['https://www.ebay.com/itm/364430102406']
        responses = [self.fetch(url) for url in urls]
        datas = [self.get_data(response) for response in responses]
        # print(datas)

if __name__ == '__main__':
    s = EbayScraper()
    s.run()