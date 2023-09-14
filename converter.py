import pandas as pd

def convert_variant_price(price):
    if price:
        if price > 100:
            result = price + 200.00
        else:
            result = price * 1.75
    else:
        result = price
    return round(result, 2)

def convert_variant_compare_at_price(price):
    if price:
        result = price * 1.3
    else:
        result = price
    return round(result, 2)

def toggle_published(published):
    if pd.isna(published):
        result = published
    else:
        result = True

    return result

def activate_status(status):
    if pd.isna(status):
        result = status
    else:
        result = 'active'

    return result

def get_UPC(MPN):
    UPCS = pd.read_csv('GasScooters30KUPC.csv')
    Available_UPC = UPCS[UPCS['status'] == 'available'].iloc[0]
    UPCS.iloc[Available_UPC.name, 1] = 'used'
    UPCS.to_csv('GasScooters30KUPC.csv', index=False)
    print(Available_UPC['UPC'])

    return Available_UPC['UPC']

if __name__ == '__main__':
    df = pd.read_csv('products_export_1.csv')
    df['Vendor'] = df['Vendor'].astype('Int64').astype('str').replace('<NA>', '')
    df['Cost per item'] = df['Variant Price'].copy()
    df['Variant Price'] = df['Variant Price'].copy().apply(convert_variant_price)
    df['Variant Compare At Price'] = df['Variant Price'].apply(convert_variant_compare_at_price)
    df['Published'] = df['Published'].copy().apply(toggle_published)
    df['Google Shopping / MPN'] = df['Google Shopping / MPN'].copy().apply(get_UPC)
    df['Status'] = df['Status'].copy().apply(activate_status)
    df.to_csv('shopify_product_update.csv', index=False, encoding='utf-8-sig')