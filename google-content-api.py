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


if __name__ == '__main__':
    GCA = GoogleContentAPI(merchantID=os.getenv('MERCHANT_ID'))
    g_service = GCA.create_service(serviceName='content', version='v2.1')
    response = GCA.get_products(g_service=g_service)
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
