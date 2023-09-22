import httpx
from dataclasses import dataclass
import json
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ShopifyApp:
    store_name: str = os.getenv('STORE_NAME')
    access_token: str = os.getenv('ACCESS_TOKEN')

    def create_session(self):
        print("Creating session...")
        client = httpx.Client()
        headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
        client.headers.update(headers)
        return client

    def query_shop(self, client):
        print("Fetching shop data...")
        query = '''
                {
                    shop{
                        name
                    }
                }
                '''

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": query})
        print(response)
        print(response.json())
        print('')

    def query_product(self, client):
        print("Fetching product data...")
        query = '''
                {
                    products(first: 3) {
                        edges {
                            node {
                                id
                                title
                            }
                        }
                    }
                }
                '''

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": query})
        print(response)
        print(response.json())
        print('')

    def create_product(self, client):
        print("Creating product...")
        mutation = '''
                    mutation (
                            $handle: String,
                            $title: String,
                            $vendor: String,
                            $productType: String,
                            $variantTitle: String,
                            $variantPrice: Money,
                            $inventoryManagement: ProductVariantInventoryManagement,
                            $inventoryPolicy: ProductVariantInventoryPolicy,
                            $mediaOriginalSource: String!,
                            $mediaContentType: MediaContentType!
                    )
                    {
                        productCreate(
                            input: {
                                handle: $handle,
                                title: $title,
                                productType: $productType,
                                vendor: $vendor
                                variants: [
                                    {
                                        title: $variantTitle,
                                        price: $variantPrice,
                                        inventoryManagement: $inventoryManagement,
                                        inventoryPolicy: $inventoryPolicy
                                    }
                                ]
                            }
                            media: {
                                originalSource: $mediaOriginalSource,
                                mediaContentType: $mediaContentType
                            }    
                        )
                        {
                            product {
                                id
                            }
                        }
                    }
                    '''

        variables = {
            'handle': "BAB063",
            'title': "Xmas Rocks Beavis And Butt-Head Shirt",
            'productType': "Shirts",
            'vendor': "MyStore",
            'variantsTitle': "Default",
            'variantPrice': "79.99",
            'inventoryManagement': 'SHOPIFY',
            'inventoryPolicy': 'DENY',
            'mediaOriginalSource': "https://80steess3.imgix.net/production/products/BAB061/xmas-rocks-beavis-and-butt-head-hoodie.master.png",
            'mediaContentType': 'IMAGE'
            }

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": mutation, 'variables':variables})
        print(response)
        print(response.json())
        print('')

    def generate_staged_target(self, client):
        print("Creating stage upload...")
        mutation = '''
                    mutation {
                        stagedUploadsCreate(
                            input:{
                                resource: BULK_MUTATION_VARIABLES,
                                filename: "bulk_op_vars.jsonl",
                                mimeType: "text/jsonl",
                                httpMethod: POST
                            }
                        )
                        {
                            userErrors{
                                field,
                                message
                            }
                            stagedTargets{
                                url,
                                resourceUrl,
                                parameters {
                                    name,
                                    value
                                }    
                            }
                        }
                    }
                    '''

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": mutation})
        print(response)
        print(response.json())
        print('')
        return response.json()

    def create_products(self, client, staged_target):
        print('Creating products...')
        # mutation = '''
        #             mutation ($stagedUploadPath: String!){
        #                 bulkOperationRunMutation(
        #                     mutation: "mutation call($input: ProductInput!)
        #                     { productCreate(input: $input) { product {id title variants(first: 10) {edges {node {id title inventoryQuantity }}}} userErrors { message field } } }",
        #                     stagedUploadPath: $stagedUploadPath
        #                 )
        #                 {
        #                     bulkOperation {
        #                         id
        #                         url
        #                         status
        #                     }
        #                     userErrors {
        #                         message
        #                         field
        #                     }
        #                 }
        #             }
        #             '''

        mutation = '''
                            mutation ($stagedUploadPath: String!){
                                bulkOperationRunMutation(
                                    mutation: "mutation call($input: ProductInput!, $media: [CreateMediaInput!])
                                    { productCreate(input: $input, media: $media) { product {id title variants(first: 10) {edges {node {id title inventoryQuantity }}}} userErrors { message field } } }",
                                    stagedUploadPath: $stagedUploadPath
                                )
                                {
                                    bulkOperation {
                                        id
                                        url
                                        status
                                    }
                                    userErrors {
                                        message
                                        field
                                    }
                                }
                            }
                            '''

        variables = {
            "stagedUploadPath": staged_target['data']['stagedUploadsCreate']['stagedTargets'][0]['parameters'][3]['value']
        }

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": mutation, "variables": variables})

        print(response)
        print(response.json())
        print('')

    def csv_to_jsonl(self, csv_filename, jsonl_filename):
        print("Converting csv to jsonl file...")
        df = pd.read_csv(os.path.join(os.getcwd(), csv_filename), encoding='utf-16')
        pd.options.display.max_columns = 100

        # get product taxonomy node
        taxonomy_list = []
        with open("D:/Naru/shopifyAPI/product_taxonomy_node.txt", "r") as taxonomy:
            for i, x in enumerate(taxonomy):
                if i > 0:
                    taxonomy_list.append(x.split('-')[1].strip())

        # Create formatted dictionary
        datas = []
        for index in df.index:
            data_dict = {"input": dict(), "media": dict()}
            data_dict['input']['title'] = df.iloc[index]['Title']
            data_dict['input']['descriptionHtml'] = df.iloc[index]['Body(HTML)']
            data_dict['input']['vendor'] = df.iloc[index]['Vendor']
            if df.iloc[index]['Product Category'] in taxonomy_list:
                taxonomy_id = taxonomy_list.index(df.iloc[index]['Product Category']) + 1
            data_dict['input']['productCategory'] = {'productTaxonomyNodeId': f"gid://shopify/ProductTaxonomyNode/{str(taxonomy_id)}"}
            data_dict['input']['productType'] = df.iloc[index]['Type']
            data_dict['input']['tags'] = df.iloc[index]['Tags']
            data_dict['input']['options'] = [df.iloc[index]['Option1 Name'],
                                             df.iloc[index]['Option2 Name'],
                                             df.iloc[index]['Option3 Name']
                                             ]

            if df.iloc[index]['Variant Weight Unit'] == "g":
                df.loc[index, 'Variant Weight Unit'] = "GRAMS"
            elif df.iloc[index]['Variant Weight Unit'] == "kg":
                df.loc[index, 'Variant Weight Unit'] = "KILOGRAMS"

            data_dict['input']['variants'] = [
                {'sku': df.iloc[index]['Variant SKU'],
                 'options': [
                     df.iloc[index]['Option1 Value'],
                     df.iloc[index]['Option2 Value'],
                     df.iloc[index]['Option3 Value']
                 ],
                 'weight': int(df.iloc[index]['Variant Grams']),
                 'weightUnit': df.iloc[index]['Variant Weight Unit'],
                 'inventoryManagement': df.iloc[index]['Variant Inventory Tracker'].upper(),
                 'inventoryPolicy': df.iloc[index]['Variant Inventory Policy'].upper(),
                 'price': str(df.iloc[index]['Variant Price']),
                 'compareAtPrice': str(df.iloc[index]['Variant Compare At Price']),
                 'requiresShipping': bool(df.iloc[index]['Variant Requires Shipping']),
                 'taxable': bool(df.iloc[index]['Variant Taxable']),
                 'imageSrc': f"https:{df.iloc[index]['Image Src']}",
                 'title': 'Default'
                 }
            ]
            data_dict['input']['giftCard'] = bool(df.iloc[index]['Gift Card'])
            data_dict['input']['status'] = df.iloc[index]['Status'].upper()
            data_dict['media'] = {'originalSource': f"https:{df.iloc[index]['Image Src']}", 'mediaContentType': 'IMAGE'}

            datas.append(data_dict.copy())
        print(datas)
        with open(os.path.join(os.getcwd(), jsonl_filename), 'w') as jsonlfile:
            for item in datas:
                json.dump(item, jsonlfile)
                jsonlfile.write('\n')


        # csvfile = pd.read_csv(os.path.join(os.getcwd(), csv_filename), encoding='utf-16')
        #
        #
        #     print(csvfile.to_json(orient='records', lines=True), file=jsonfile, flush=False)
        # print('')

    def upload_jsonl(self, staged_target, jsonl_path):
        print("Uploading jsonl file to staged path...")
        url = staged_target['data']['stagedUploadsCreate']['stagedTargets'][0]['url']
        parameters = staged_target['data']['stagedUploadsCreate']['stagedTargets'][0]['parameters']
        files = dict()
        for parameter in parameters:
            files[f"{parameter['name']}"] = (None, parameter['value'])
        files['file'] = open(jsonl_path, 'rb')

        # with httpx.Client(timeout=None, follow_redirects=True) as sess:
        response = httpx.post(url, files=files)

        print(response)
        print(response.content)
        print('')

    def webhook_subscription(self, client):
        print("Subscribing webhook...")
        mutation = '''
                    mutation {
                        webhookSubscriptionCreate(
                            topic: BULK_OPERATIONS_FINISH
                            webhookSubscription: {
                                format: JSON,
                                callbackUrl: "https://12345.ngrok.io/"
                                }
                        )
                        {
                            userErrors {
                                field
                                message
                            }
                            webhookSubscription {
                                id
                            }
                        }
                    }
        '''

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": mutation})
        print(response)
        print(response.json())
        print('')

    def pool_operation_status(self,client):
        print("Pooling operation status...")
        query = '''
                    query {
                        currentBulkOperation(type: MUTATION) {
                            id
                            status
                            errorCode
                            createdAt
                            completedAt
                            objectCount
                            fileSize
                            url
                            partialDataUrl
                        }
                    }
                '''

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": query})
        print(response)
        print(response.json())
        print('')

    def import_bulk_data(self, client, csv_filename, jsonl_filename):
        self.csv_to_jsonl(csv_filename=csv_filename, jsonl_filename=jsonl_filename)
        staged_target = self.generate_staged_target(client)
        self.upload_jsonl(staged_target=staged_target, jsonl_path=jsonl_filename)
        self.create_products(client, staged_target=staged_target)

    def create_collection(self, client):
        print('Creating collection...')
        mutation = '''
        mutation ($descriptionHtml: String!, $title: String!){
            collectionCreate(
                input: {
                    descriptionHtml: $descriptionHtml
                    title: $title
                }
            )
            {
                collection{
                    id
                    productsCount
                }
                userErrors{
                    field
                    message
                }   
            }
        }    
        '''

        variables = {
            'descriptionHtml': "<p>This Collection is created as a training material</p>",
            'title': "Collection1"
        }

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": mutation, 'variables': variables})
        print(response)
        print(response.json())
        print('')

    def get_publications(self, client):
        print('Getting publications list...')
        query = '''
        query {
            publications(first: 10){
                edges{
                    node{
                        id
                        name
                    }
                }
            }
        }
        '''

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": query})
        print(response)
        print(response.json())
        print('')

    def publish_collection(self, client):
        print('Publishing collection...')
        mutation = '''
        mutation {
            collectionPublish(
                input: {
                    id: "",
                    collectionPublications: {
                        publicationId: "gid://shopify/Publication/178396725562"
                        }
                    }
                )
            )
            {
                collectionPublications{
                    publishDate
                }
                userErrors{
                    field
                    message
            }
        }    
        '''

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": mutation})
        print(response)
        print(response.json())
        print('')

    def get_collections(self, client):
        print('Getting collection list...')
        query = '''
                query {
                    collections(first: 10){
                        edges{
                            node{
                                id
                                title
                                handle
                                updatedAt
                                productsCount
                            }
                        }
                    }
                }
                '''

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": query})
        print(response)
        print(response.json())
        print('')

    def check_bulk_operation_status(self, client, bulk_operation_id):
        query = f'''
            query {{
                node(id: "{bulk_operation_id}") {{
                    ... on BulkOperation {{
                        id
                        status
                    }}
                }}
            }}
        '''

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": query})

        response_data = response.json()
        status = response_data['data']['node']['status']
        return status

    def products_to_collection(self, client):
        pass

    def get_files(self, client, filename):
        print("Fetching files data...")
        query = '''
        query getFilesByFilename($filename:String!)
        {
            files(first:1, query:$filename) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
        '''

        variables = {'filename': filename}

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={'query': query, 'variables': variables})
        print(response)
        print(response.json())
        print('')

    def edit_file(self, client, variable):
        print("Fetching files data...")
        query = '''
                        {
                            files(first: 3) {
                                edges {
                                    node {
                                        id
                                    }
                                }
                            }
                        }
                        '''

        response = client.post(f'https://{self.store_name}.myshopify.com/admin/api/2023-07/graphql.json',
                               json={"query": query})
        print(response)
        print(response.json())
        print('')

if __name__ == '__main__':
    s = ShopifyApp()
    client = s.create_session()
    s.get_files(client, filename='s-l1600_2d1fdefc-ba9a-4089-b87e-45351e1968b7')

    # s.query_shop(client)
    # s.query_product(client)
    # s.create_product(client)
    # s.csv_to_jsonl(csv_filename='result.csv', jsonl_filename='test2.jsonl')
    # staged_target = s.generate_staged_target(client)
    # s.upload_jsonl(staged_target=staged_target, jsonl_path="D:/Naru/shopifyAPI/bulk_op_vars.jsonl")
    # s.create_products(client, staged_target=staged_target)
    # s.import_bulk_data(client=client, csv_filename='result.csv', jsonl_filename='bulk_op_vars.jsonl')
    # s.webhook_subscription(client)
    # s.create_collection(client)
    # s.query_product(client)
    # s.get_publications(client)
    # s.get_collections(client)
    # s.pool_operation_status(client)
    # print(s.check_bulk_operation_status(client, bulk_operation_id='gid://shopify/BulkOperation/3252439023930'))