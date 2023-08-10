import json
import httpx
from selectolax.parser import HTMLParser
from dataclasses import dataclass
import pandas as pd
import re


@dataclass
class EbayScraper:

    def fetch(self, url):
        headers = {
            'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0'
        }
        with httpx.Client(headers=headers) as client:
            response = client.get(url)

        return response

    def get_data(self, response):
        pd.set_option('display.max_columns', 100)
        tree = HTMLParser(response.text)

        picture_panel = tree.css_first('div#PicturePanel')
        right_panel = tree.css_first('div#RightSummaryPanel')
        left_panel = tree.css_first('div#LeftSummaryPanel')
        more_desc = tree.css_first('div#readMoreDesc')
        item_specs = tree.css('div.ux-layout-section-evo__item.ux-layout-section-evo__item--table-view > div.ux-layout-section-evo__row')
        try:
            select_box = left_panel.css('span.x-msku__select-box-wrapper > select.x-msku__select-box')
        except AttributeError:
            print("Product doesn't have variant")

        if left_panel:
            if select_box:
                for i, variant in enumerate(select_box):
                    options = variant.css('option')
                    if i == 0:
                        self.option1_name = variant.css_first('select').attributes.get('selectboxlabel')
                    elif i == 1:
                        self.option2_name = variant.css_first('select').attributes.get('selectboxlabel')
                    elif i == 2:
                        self.option3_name = variant.css_first('select').attributes.get('selectboxlabel')
                    for j, option in enumerate(options):
                        if j == 0:
                            continue
                        else:
                            self.handle = more_desc.css_first(
                                'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                                strip=True)
                            self.title = left_panel.css_first('h1.x-item-title__mainTitle').text(strip=True)
                            self.description = self.get_desc(self.handle)
                            for item in item_specs:
                                cols = item.css('div.ux-layout-section-evo__col')
                                for col in cols:
                                    try:
                                        if col.css_first('div.ux-labels-values__labels').text(strip=True) == 'Brand':
                                            self.vendor = col.css_first('div.ux-labels-values__values').text(strip=True)
                                    except:
                                        self.vendor = ''
                            self.price = float(
                                re.findall(r"\d+\.\d+", left_panel.css_first('div.x-price-primary').text(strip=True))[0])
                            self.condition = left_panel.css_first('span.ux-icon-text__text > span.clipped').text(strip=True)
                            self.img_src = picture_panel.css_first('img.ux-image-magnify__image--original').attributes.get('src')
                            if i == 0:
                                self.option1_value = option.text()
                                option_value = option.attributes.get('value')
                            elif i == 1:
                                self.option2_value = option.text()
                            elif i == 2:
                                self.option3_value = option.text()
                            handle = []
                            handle.append(self.handle)
                            if i == 0 and j == 1:
                                df = pd.DataFrame(data=handle, columns=['Handle'])
                                df['Title'] = self.title
                                df['Body (HTML)'] = self.description
                                df['Vendor'] = self.vendor
                                df['Product Category'] = ''
                                df['Type'] = ''
                                df['Tags'] = ''
                                df['Published'] = True
                                try:
                                    df['Option1 Name'] = self.option1_name
                                    df['Option1 Value'] = self.option1_value
                                except AttributeError:
                                    df['Option1 Name'] = ''
                                    df['Option1 Value'] = ''
                                try:
                                    df['Option2 Name'] = self.option2_name
                                    df['Option2 Value'] = self.option2_value
                                except AttributeError:
                                    df['Option2 Name'] = ''
                                    df['Option2 Value'] = ''
                                try:
                                    df['Option3 Name'] = self.option3_name
                                    df['Option3 Value'] = self.option3_value
                                except AttributeError:
                                    df['Option3 Name'] = ''
                                    df['Option3 Value'] = ''
                                df['Variant SKU'] = handle[0]+self.option1_value.strip().lower().replace(' ', '')
                                df['Variant Grams'] = ''
                                df['Variant Inventory Tracker'] = 'shopify'
                                df['Variant Inventory Qty'] = 10
                                df['Variant Inventory Policy'] = 'deny'
                                df['Variant Fulfillment Service'] = 'manual'
                                df['Variant Price'] = self.get_price(tree,option_value=option_value)['price']
                                df['Variant Comapare At Price'] = df['Variant Price']
                                df['Variant Requires Shipping'] = True
                                df['Variant Taxable'] = True
                                df['Variant Barcode'] = ''
                                df['Image Src'] = self.img_src
                                # df['Image Src'] = self.get_main_product_images(tree)
                                df['Image Position'] = 1
                                df['Image Alt Text'] = ''
                                df['Gift Card'] = False
                                df['SEO Title'] = ''
                                df['SEO Description'] = ''
                                df['Google Shopping / Google Product Category'] = ''
                                df['Google Shopping / Gender'] = ''
                                df['Google Shopping / Age Group'] = ''
                                df['Google Shopping / MPN'] = ''
                                df['Google Shopping / AdWords Grouping'] = ''
                                df['Google Shopping / AdWords Labels'] = ''
                                df['Google Shopping / Condition'] = self.condition
                                df['Google Shopping / Custom Product'] = ''
                                df['Google Shopping / Custom Label 0'] = ''
                                df['Google Shopping / Custom Label 1'] = ''
                                df['Google Shopping / Custom Label 2'] = ''
                                df['Google Shopping / Custom Label 3'] = ''
                                df['Google Shopping / Custom Label 4'] = ''
                                df['Variant Image'] = self.get_variant_image(tree, option_value=option_value)
                                df['Variant Weight Unit'] = 'kg'
                                df['Variant Tax Code'] = ''
                                df['Cost per item'] = ''
                                df['Price / International'] = ''
                                df['Compare At Price / International'] = ''
                                df['Status'] = 'active'
                                collected_df = df.copy()
                                main_images = self.get_main_product_images(tree)
                                for image in main_images:
                                    df = pd.DataFrame(data=handle, columns=['Handle'])
                                    df['Title'] = ''
                                    df['Body (HTML)'] = ''
                                    df['Vendor'] = ''
                                    df['Product Category'] = ''
                                    df['Type'] = ''
                                    df['Tags'] = ''
                                    df['Published'] = ''
                                    df['Option1 Name'] = ''
                                    df['Option1 Value'] = ''
                                    df['Option2 Name'] = ''
                                    df['Option2 Value'] = ''
                                    df['Option3 Name'] = ''
                                    df['Option3 Value'] = ''
                                    df['Variant SKU'] = ''
                                    df['Variant Grams'] = ''
                                    df['Variant Inventory Tracker'] = ''
                                    df['Variant Inventory Qty'] = ''
                                    df['Variant Inventory Policy'] = ''
                                    df['Variant Fulfillment Service'] = ''
                                    df['Variant Price'] = ''
                                    df['Variant Comapare At Price'] = ''
                                    df['Variant Requires Shipping'] = ''
                                    df['Variant Taxable'] = ''
                                    df['Variant Barcode'] = ''
                                    df['Image Src'] = image
                                    # df['Image Src'] = self.get_main_product_images(tree)
                                    df['Image Position'] = ''
                                    df['Image Alt Text'] = ''
                                    df['Gift Card'] = ''
                                    df['SEO Title'] = ''
                                    df['SEO Description'] = ''
                                    df['Google Shopping / Google Product Category'] = ''
                                    df['Google Shopping / Gender'] = ''
                                    df['Google Shopping / Age Group'] = ''
                                    df['Google Shopping / MPN'] = ''
                                    df['Google Shopping / AdWords Grouping'] = ''
                                    df['Google Shopping / AdWords Labels'] = ''
                                    df['Google Shopping / Condition'] = ''
                                    df['Google Shopping / Custom Product'] = ''
                                    df['Google Shopping / Custom Label 0'] = ''
                                    df['Google Shopping / Custom Label 1'] = ''
                                    df['Google Shopping / Custom Label 2'] = ''
                                    df['Google Shopping / Custom Label 3'] = ''
                                    df['Google Shopping / Custom Label 4'] = ''
                                    df['Variant Image'] = ''
                                    df['Variant Weight Unit'] = ''
                                    df['Variant Tax Code'] = ''
                                    df['Cost per item'] = ''
                                    df['Price / International'] = ''
                                    df['Compare At Price / International'] = ''
                                    df['Status'] = ''
                                    collected_df = pd.concat([collected_df, df.copy()], ignore_index=True)
                            else:
                                df = pd.DataFrame(data=handle, columns=['Handle'])
                                df['Title'] = ''
                                df['Body (HTML)'] = ''
                                df['Vendor'] = ''
                                df['Product Category'] = ''
                                df['Type'] = ''
                                df['Tags'] = ''
                                df['Published'] = ''
                                df['Option1 Name'] = ''
                                try:
                                    df['Option1 Value'] = self.option1_value
                                except AttributeError:
                                    df['Option1 Value'] = ''
                                df['Option2 Name'] = ''
                                try:
                                    df['Option2 Value'] = self.option2_value
                                except AttributeError:
                                    df['Option2 Value'] = ''
                                df['Option3 Name'] = ''
                                try:
                                    df['Option3 Value'] = self.option3_value
                                except AttributeError:
                                    df['Option3 Name'] = ''
                                    df['Option3 Value'] = ''
                                df['Variant SKU'] = handle[0]+self.option1_value.strip().lower().replace(' ', '')
                                df['Variant Grams'] = ''
                                df['Variant Inventory Tracker'] = 'shopify'
                                df['Variant Inventory Qty'] = 10
                                df['Variant Inventory Policy'] = 'deny'
                                df['Variant Fulfillment Service'] = 'manual'
                                df['Variant Price'] = self.get_price(tree,option_value=option_value)['price']
                                df['Variant Comapare At Price'] = df['Variant Price']
                                df['Variant Requires Shipping'] = True
                                df['Variant Taxable'] = True
                                df['Variant Barcode'] = ''
                                df['Image Src'] = ''
                                df['Image Position'] = ''
                                df['Image Alt Text'] = ''
                                df['Gift Card'] = ''
                                df['SEO Title'] = ''
                                df['SEO Description'] = ''
                                df['Google Shopping / Google Product Category'] = ''
                                df['Google Shopping / Gender'] = ''
                                df['Google Shopping / Age Group'] = ''
                                df['Google Shopping / MPN'] = ''
                                df['Google Shopping / AdWords Grouping'] = ''
                                df['Google Shopping / AdWords Labels'] = ''
                                df['Google Shopping / Condition'] = ''
                                df['Google Shopping / Custom Product'] = ''
                                df['Google Shopping / Custom Label 0'] = ''
                                df['Google Shopping / Custom Label 1'] = ''
                                df['Google Shopping / Custom Label 2'] = ''
                                df['Google Shopping / Custom Label 3'] = ''
                                df['Google Shopping / Custom Label 4'] = ''
                                df['Variant Image'] = self.get_variant_image(tree,option_value=option_value)
                                df['Variant Weight Unit'] = 'kg'
                                df['Variant Tax Code'] = ''
                                df['Cost per item'] = ''
                                df['Price / International'] = ''
                                df['Compare At Price / International'] = ''
                                df['Status'] = 'active'
                                collected_df = pd.concat([collected_df, df.copy()], ignore_index=True)
            else:
                self.handle = more_desc.css_first(
                    'div.ux-layout-section__textual-display.ux-layout-section__textual-display--itemId > span.ux-textspans--BOLD').text(
                    strip=True)
                self.title = left_panel.css_first('h1.x-item-title__mainTitle').text(strip=True)
                self.description = self.get_desc(self.handle)
                # div.ux-layout-section-evo__item.ux-layout-section-evo__item--table-view > div.ux-layout-section-evo__row
                for item in item_specs:
                    cols = item.css('div.ux-layout-section-evo__col')
                    for col in cols:
                        try:
                            if col.css_first('div.ux-labels-values__labels').text(strip=True) == 'Brand':
                                self.vendor = col.css_first('div.ux-labels-values__values').text(strip=True)
                        except:
                            continue
                self.price = float(
                    re.findall(r"\d+\.\d+", left_panel.css_first('div.x-price-primary').text(strip=True))[0])
                self.condition = left_panel.css_first('span.ux-icon-text__text > span.clipped').text(strip=True)
                self.img_src = picture_panel.css_first('img.ux-image-magnify__image--original').attributes.get('src')
                handle = []
                handle.append(self.handle)
                df = pd.DataFrame(data=handle, columns=['Handle'])
                df['Title'] = self.title
                df['Body (HTML)'] = self.description
                df['Vendor'] = self.vendor
                df['Product Category'] = ''
                df['Type'] = ''
                df['Tags'] = ''
                df['Published'] = True
                try:
                    df['Option1 Name'] = self.option1_name
                    df['Option1 Value'] = self.option1_value
                except AttributeError:
                    df['Option1 Name'] = ''
                    df['Option1 Value'] = ''
                try:
                    df['Option2 Name'] = self.option2_name
                    df['Option2 Value'] = self.option2_value
                except AttributeError:
                    df['Option2 Name'] = ''
                    df['Option2 Value'] = ''
                try:
                    df['Option3 Name'] = self.option3_name
                    df['Option3 Value'] = self.option3_value
                except AttributeError:
                    df['Option3 Name'] = ''
                    df['Option3 Value'] = ''
                df['Variant SKU'] = handle[0]
                df['Variant Grams'] = ''
                df['Variant Inventory Tracker'] = 'shopify'
                df['Variant Inventory Qty'] = 10
                df['Variant Inventory Policy'] = 'deny'
                df['Variant Fulfillment Service'] = 'manual'
                df['Variant Price'] = self.price
                df['Variant Comapare At Price'] = df['Variant Price']
                df['Variant Requires Shipping'] = True
                df['Variant Taxable'] = True
                df['Variant Barcode'] = ''
                df['Image Src'] = self.img_src
                # df['Image Src'] = self.get_main_product_images(tree)
                df['Image Position'] = 1
                df['Image Alt Text'] = ''
                df['Gift Card'] = False
                df['SEO Title'] = ''
                df['SEO Description'] = ''
                df['Google Shopping / Google Product Category'] = ''
                df['Google Shopping / Gender'] = ''
                df['Google Shopping / Age Group'] = ''
                df['Google Shopping / MPN'] = ''
                df['Google Shopping / AdWords Grouping'] = ''
                df['Google Shopping / AdWords Labels'] = ''
                df['Google Shopping / Condition'] = self.condition
                df['Google Shopping / Custom Product'] = ''
                df['Google Shopping / Custom Label 0'] = ''
                df['Google Shopping / Custom Label 1'] = ''
                df['Google Shopping / Custom Label 2'] = ''
                df['Google Shopping / Custom Label 3'] = ''
                df['Google Shopping / Custom Label 4'] = ''
                df['Variant Image'] = ''
                df['Variant Weight Unit'] = 'kg'
                df['Variant Tax Code'] = ''
                df['Cost per item'] = ''
                df['Price / International'] = ''
                df['Compare At Price / International'] = ''
                df['Status'] = 'active'
                collected_df = df.copy()
                main_images = self.get_main_product_images(tree)
                for image in main_images:
                    df = pd.DataFrame(data=handle, columns=['Handle'])
                    df['Title'] = ''
                    df['Body (HTML)'] = ''
                    df['Vendor'] = ''
                    df['Product Category'] = ''
                    df['Type'] = ''
                    df['Tags'] = ''
                    df['Published'] = ''
                    df['Option1 Name'] = ''
                    df['Option1 Value'] = ''
                    df['Option2 Name'] = ''
                    df['Option2 Value'] = ''
                    df['Option3 Name'] = ''
                    df['Option3 Value'] = ''
                    df['Variant SKU'] = ''
                    df['Variant Grams'] = ''
                    df['Variant Inventory Tracker'] = ''
                    df['Variant Inventory Qty'] = ''
                    df['Variant Inventory Policy'] = ''
                    df['Variant Fulfillment Service'] = ''
                    df['Variant Price'] = ''
                    df['Variant Comapare At Price'] = ''
                    df['Variant Requires Shipping'] = ''
                    df['Variant Taxable'] = ''
                    df['Variant Barcode'] = ''
                    df['Image Src'] = image
                    # df['Image Src'] = self.get_main_product_images(tree)
                    df['Image Position'] = ''
                    df['Image Alt Text'] = ''
                    df['Gift Card'] = ''
                    df['SEO Title'] = ''
                    df['SEO Description'] = ''
                    df['Google Shopping / Google Product Category'] = ''
                    df['Google Shopping / Gender'] = ''
                    df['Google Shopping / Age Group'] = ''
                    df['Google Shopping / MPN'] = ''
                    df['Google Shopping / AdWords Grouping'] = ''
                    df['Google Shopping / AdWords Labels'] = ''
                    df['Google Shopping / Condition'] = ''
                    df['Google Shopping / Custom Product'] = ''
                    df['Google Shopping / Custom Label 0'] = ''
                    df['Google Shopping / Custom Label 1'] = ''
                    df['Google Shopping / Custom Label 2'] = ''
                    df['Google Shopping / Custom Label 3'] = ''
                    df['Google Shopping / Custom Label 4'] = ''
                    df['Variant Image'] = ''
                    df['Variant Weight Unit'] = ''
                    df['Variant Tax Code'] = ''
                    df['Cost per item'] = ''
                    df['Price / International'] = ''
                    df['Compare At Price / International'] = ''
                    df['Status'] = ''
                    collected_df = pd.concat([collected_df, df.copy()], ignore_index=True)

            collected_df.to_csv('result.csv', index=False)
            print('Product Scraped')

        else:
            print('Product Sold Out')

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


    def get_desc(self, item_id):
        url = f'https://vi.vipr.ebaydesc.com/ws/eBayISAPI.dll?ViewItemDescV4&item={item_id}'
        response = self.fetch(url)
        tree = HTMLParser(response.text)
        # body = tree.css_first('body').html
        body = tree.css_first('body').text()
        return body

    def run(self):
        # target = 'https://www.ebay.com/itm/225625920147'
        target = 'https://www.ebay.com/itm/394768568591'
        response = self.fetch(target)
        data = self.get_data(response)

if __name__ == '__main__':
    s = EbayScraper()
    s.run()