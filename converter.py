import pandas as pd
from dataclasses import dataclass

@dataclass
class converter:
    container: str = ''

    def convert_variant_price(self, price):
        if price:
            if price > 100:
                result = price + 200.00
            else:
                result = price * 1.75
        else:
            result = price
        return round(result, 2)

    def convert_variant_compare_at_price(self, price):
        if price:
            result = price * 1.3
        else:
            result = price
        return round(result, 2)

    def toggle_published(self, published):
        if pd.isna(published):
            result = published
        else:
            result = True

        return result

    def activate_status(self, status):
        if pd.isna(status):
            result = status
        else:
            result = 'active'

        return result

    def get_UPC(self, SKU):
        if pd.isna(SKU):
            result = ''
        else:
            UPCS = pd.read_csv('GasScooters30KUPC.csv')
            Available_UPC = UPCS[UPCS['status'] == 'available'].iloc[0]
            result = Available_UPC['UPC']
            UPCS.iloc[Available_UPC.name, 1] = 'used'
            UPCS.to_csv('GasScooters30KUPC.csv', index=False)
            print(Available_UPC['UPC'])

        return result

    def change_vendor(self, Vendor):
        if pd.isna(Vendor) or Vendor == '':
            result = Vendor
        else:
            result = 'Magic Cars'

        return result

    def change_tracker(self, variant_sku):
        if pd.isna(variant_sku):
            result = variant_sku
        else:
            result = 'shopify'

        return result

    def generate_variant_sku(self, handle, variant_opt1, variant_opt2, variant_opt3):
        if pd.isna(variant_opt1):
            result = variant_opt1
        else:
            keywords = [str(handle), str(variant_opt1).lower().replace(' ', '').split('-')[0], str(variant_opt2).lower().replace(' ', '').split('-')[0], str(variant_opt3).lower().replace(' ', '').split('-')[0]]
            result = '-'.join(keywords)

        return result

    def generate_handle(self, title):
        if type(title) != float:
            self.container = title.lower().replace(' -', '').replace(' ', '-').replace(',', '')
        result = self.container

        return result

    def change_tags(self, Tags):
        if pd.isna(Tags):
            result = Tags
        else:
            result = 'B72'
        return result
    def run(self):
        df = pd.read_csv('products_export_1.csv')
        df['Vendor'] = df['Vendor'].astype('Int64').astype('str').replace('<NA>', '')
        df['Variant SKU'] = df.apply(
            lambda x: self.generate_variant_sku(x['Handle'], x['Option1 Value'], x['Option2 Value'], x['Option3 Value']),
            axis=1)
        df['Handle'] = df['Title'].copy().apply(self.generate_handle)
        df['Vendor'] = df['Vendor'].copy().apply(self.change_vendor)
        df['Tags'] = df['Tags'].copy().apply(self.change_tags)
        df['Cost per item'] = df['Variant Price'].copy()
        df['Variant Price'] = df['Variant Price'].copy().apply(self.convert_variant_price)
        df['Variant Compare At Price'] = df['Variant Price'].apply(self.convert_variant_compare_at_price)
        df['Variant Inventory Tracker'] = df['Variant SKU'].apply(self.change_tracker)
        df['Published'] = df['Published'].copy().apply(self.toggle_published)
        df['Google Shopping / MPN'] = df['Variant SKU'].copy().apply(self.get_UPC)
        df['Google Shopping / Custom Label 1'] = df['Tags'].copy()
        df['Variant Barcode'] = df['Google Shopping / MPN'].copy()
        df['Status'] = df['Status'].copy().apply(self.activate_status)
        df.to_csv('shopify_product_update.csv', index=False, encoding='utf-8-sig')
        # print(len(df['Google Shopping / MPN']), len(df['Variant Barcode']))

if __name__ == '__main__':
    c = converter()
    c.run()