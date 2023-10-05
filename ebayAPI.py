import httpx
from dataclasses import dataclass
import asyncio

@dataclass
class ebayAPI:

    def find_items_by_category(self):
        url = 'https://svcs.ebay.com/services/search/FindingService/v1'
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0',
            'Content-Type': 'application/xml',
            'X-EBAY-SOA-SECURITY-APPNAME': 'PerryCha-TrendTim-PRD-fea9be394-87a4e7c3',
            'X-EBAY-SOA-OPERATION-NAME': 'findItemsByCategory'
        }
        xml = """
        <?xml version="1.0" encoding="utf-8"?>
        <findItemsByCategoryRequest xmlns="http://www.ebay.com/marketplace/search/v1/services">
            <!-- Call-specific Input Fields -->
            <aspectFilter> AspectFilter
                <aspectName> string </aspectName>
                <aspectValueName> string </aspectValueName>
                <!-- ... more aspectValueName values allowed here ... -->
            </aspectFilter>
            <!-- ... more aspectFilter nodes allowed here ... -->
            <categoryId> 145944 </categoryId>
            <!-- ... more categoryId values allowed here ... -->
            <domainFilter> DomainFilter
                <domainName> string </domainName>
                <!-- ... more domainName values allowed here ... -->
            </domainFilter>
            <!-- ... more domainFilter nodes allowed here ... -->
            <itemFilter> ItemFilter
                <name> ItemFilterType </name>
                <paramName> token </paramName>
                <paramValue> string </paramValue>
                <value> string </value>
                <!-- ... more value values allowed here ... -->
            </itemFilter>
            <!-- ... more itemFilter nodes allowed here ... -->
            <outputSelector> OutputSelectorType </outputSelector>
            <!-- ... more outputSelector values allowed here ... -->
            <!-- Standard Input Fields -->
            <affiliate> Affiliate
                <customId> string </customId>
                <geoTargeting> boolean </geoTargeting>
                <networkId> string </networkId>
                <trackingId> string </trackingId>
            </affiliate>
            <buyerPostalCode> string </buyerPostalCode>
            <paginationInput> PaginationInput
                <entriesPerPage> int </entriesPerPage>
                <pageNumber> int </pageNumber>
            </paginationInput>
            <sortOrder> SortOrderType </sortOrder>
        </findItemsByCategoryRequest>
        """

        payload ="""
        <findItemsByCategoryRequest xmlns="http://www.ebay.com/marketplace/search/v1/services">
            <categoryId>145944</categoryId>
            <itemFilter>
                <name>Condition</name>
                <value>New</value>
            </itemFilter>
            <itemFilter>
                <name>ListingType</name>
                <value>AuctionWithBIN</value>
                <value>FixedPrice</value>
            </itemFilter>
            <paginationInput>
		        <entriesPerPage>100</entriesPerPage>
		        <pageNumber>100</pageNumber>
	        </paginationInput>
	        <sortOrder>PricePlusShippingHighest</sortOrder>
	        <outputSelector>CategoryHistogram</outputSelector>
        </findItemsByCategoryRequest>
        """
        with httpx.Client(headers=headers) as client:
            response = client.post(url, data=payload)
        print(response.read())

if __name__ == '__main__':
    api = ebayAPI()
    api.find_items_by_category()
