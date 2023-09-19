import pandas as pd

def redirect_url():
    df = pd.read_csv('products_export_1.csv')
    product_list = df[~pd.isna(df['Title'])].copy()
    product_list['Redirect from'] = product_list['Handle'].apply(lambda x: f"/products/{x}")
    product_list['Redirect to'] = f"/"
    result = product_list[['Redirect from', 'Redirect to']].reset_index(drop=True)
    result.to_csv('redirect/redirect_url.csv', index=False)

if __name__ == '__main__':
    redirect_url()