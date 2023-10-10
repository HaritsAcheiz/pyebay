import os
import httpx
from dataclasses import dataclass
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import json
from dotenv import load_dotenv

load_dotenv()

@dataclass
class GoogleContentAPI:
    serviceEndpoint: str = 'https://shoppingcontent.googleapis.com'
    merchantID:str = None

    def create_service(self, serviceName, version):

        # Specify the path to the service account key file
        key_path = 'magiccarsgca-95f473463412.json'

        # Create a credentials object
        creds = Credentials.from_service_account_file(key_path)

        g_service = build(serviceName=serviceName, version=version, credentials=creds)
        return g_service

    def get_products(self, g_service):
        result = g_service.products().list(merchantId=self.merchantID).execute()
        return result

    def get_product(self, g_service, productId):
        result = g_service.products().get(merchantId=self.merchantID, productId=productId).execute()
        return result

    def get_datafeedstatus(self, g_service):
        result = g_service.datafeedstatuses().list(merchantId=self.merchantID, maxResults=10).execute()
        return result

    def get_datafeeds(self, g_service, datafeedId):
        result = g_service.datafeeds().get(merchantId=self.merchantID, datafeedId=datafeedId).execute()
        return result

    def list_datafeeds(self, g_service):
        result = g_service.datafeeds().list(merchantId=self.merchantID).execute()

if __name__ == '__main__':
    GCA = GoogleContentAPI(merchantID=os.getenv('MERCHANT_ID'))
    g_service = GCA.create_service(serviceName='content', version='v2.1')
    # response = GCA.get_products(g_service=g_service)
    # response = GCA.get_datafeeds(g_service=g_service)
    response = GCA.get_product(g_service=g_service, productId='online:en:US:shopify_US_8491785158887_47874778923239')
    print(response)
    # response = GCA.get_datafeeds(g_service=g_service, datafeedId='online:en:US:shopify_US_8491785158887_47874778923239')
    # print(response)
    response = GCA.list_datafeeds(g_service=g_service)
    print(response)


    # response = GCA.getList()
    # print(response.text)

    # Specify the project ID
    # projectId = 'magiccarsgca'

    # Create a Content API client
    # with build('content', 'v2.1', credentials=creds) as service:
    #     result = service.products().list(merchantId=120221182).execute()
    #
    #
    # print(result)
