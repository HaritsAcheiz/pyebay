import os

import pandas as pd
import shopifyapi
from datetime import datetime
from time import sleep
import re

def generate_filename(handle, id):
    if pd.isna(id):
        result = id
    else:
        # cleaning id
        pattern = r"[a-zA-Z0-9-/.]+"
        clean_src = "".join(re.findall(pattern, id))
        add = clean_src.split('/')

        # clean handle
        clean_handle = "".join(re.findall(pattern, handle)).replace('/', '-')
        result = f'{clean_handle}-{add[-1]}'

    return result


if __name__ == '__main__':
    # read imported product data
    imported_products = pd.read_csv('final_result/20231003_186-190_Desc_B108_QC.csv',
                                    usecols=['Handle', 'Image Alt Text'],
                                    encoding='unicode_escape')
    imported_products.drop_duplicates(subset='Image Alt Text', inplace=True, ignore_index=True, keep='first')
    # print('============================Data Frame imported_products================================')
    # print(imported_products)

    # get shopify file ID
    s = shopifyapi.ShopifyApp()
    client = s.create_session()
    updated_at = '2023-10-04T00:00:00Z'
    created_at = '2023-10-02T00:00:00Z'
    hasNextPage = True
    after = ''
    retries = 0

    while hasNextPage:
        try:
            response = s.get_file(client, created_at=created_at, updated_at=updated_at, after=after)
            datas = response['data']['files']['edges']
            image_datas = []
            after = response['data']['files']['pageInfo']['endCursor']
            print(f'hasNextPage: {hasNextPage}')
            print(f'after: {after}')
            hasNextPage = response['data']['files']['pageInfo']['hasNextPage']
            for data in datas:
                image_datas.append(data['node'])
            images_df = pd.DataFrame(image_datas)
            # print('============================Data Frame shopify API================================')
            # print(images_df['alt'])

            # merge product data with shopify file ID
            merged_products = images_df.merge(imported_products, how='inner', right_on='Image Alt Text', left_on='alt')
            # print('============================Data Frame merged products================================')
            # print(merged_products)

            # generate filename
            merged_products['filename'] = merged_products.apply(lambda x: generate_filename(x['Handle'], x['id']), axis=1)

            # edit filename
            merged_products.apply(lambda x: s.edit_file(client=client, file_id=x['id'], file_name=x['filename'], altText=x['alt']), axis=1)

        except Exception as e:
            print(e)