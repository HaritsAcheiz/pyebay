import json

from dotenv import load_dotenv
import openai
import os
from dataclasses import dataclass
import pandas as pd
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.chat_models import ChatOpenAI
from selectolax.parser import HTMLParser
import re

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = openai_api_key

@dataclass
class TransformEbay:

    def parse(self, html):
        if pd.isna(html):
            result = html
        else:
            tree = HTMLParser(html)
            result = tree.css_first('body').text(strip=True)

        return result

    def openai_edit(self, title, description, additional_spec):
        if pd.isna(description):
            result = description

        else:
            human_template = """
            Generate unique product descriptions based on the provided title, description, and product specifications. Ensure that the rewritten descriptions follow these specific steps:
            Step 1: Remove Payment Details.
            Step 2: Exclude Return Policies.
            Step 3: Omit Feedback References.
            Step 4: Remove Company Background.
            Step 5: Exclude Warranty Terms.
            Step 6: Exclude Shipping Information.
            Step 7: Remove Marketplace References.
            Step 8: Remove ASIN Number.
            Step 9: Add Bullet Points for Specifications.
            Step 10: Create Closing Sentence with '<a href='https://www.magiccars.com/'>ride on</a>' Link.
            Step 11: Ensure Unique Description by emphasizing distinct phrasing, synonyms, and alternative sentence structures while highlighting the product's key features and specifications.

            Here's the original product description:
            {current_description}
            Here's the title:
            {title}
            Here's the item specification:
            {additional_spec}
            
            Please rewrite this description following the provided steps and guidelines to ensure it is unique and optimized for our e-commerce website.
            Answer:
            """

            system_template = """You are looking to create unique product descriptions for your e-commerce website, ensuring that the descriptions are not considered plagiarism. You have a dataset of product titles, descriptions, and specifications, but you want to rewrite them to remove certain elements (payment details, return policies, feedback references, company background, warranty terms, shipping information, marketplace references, ASIN numbers) and enhance the readability and clarity by adding bullet points for specifications and creating an enticing closing sentence with a consistent link to encourage readers to explore the product further on your website."""

            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
            system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
            chat_prompt_template = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
            chat_prompt_format = chat_prompt_template.format_messages(title=title, current_description=description, additional_spec=additional_spec)
            chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1)

            output = chat(chat_prompt_format)
            content = output.content
            result = content
            print(f'Transform {title} description completed!')

        return result

    def openai_edit_title(self, title, description):
        if pd.isna(title):
            result = title
        else:
            # human_template_v0 = """
            # Sensationalize the title of the product within 16 words maximum based on the following title and description. Change all brand name to Magic Cars.
            # Title:
            # {title}
            # Description:
            # {current_description}
            # """

            # human_template_v1 = """
            # You are an SEO Specialist who has 5 years of experience in product marketing. You have created many content for products that you want to market.
            # You know how to write title of the product, so it becomes SEO-friendly.
            # You can use keywords effectively, With that experience, please diversify the following title {title} within 16 words maximum based on the following product title {current_description} that use Magic Cars as a brand name.
            # Answer:
            # """

            # human_template = """
            #             You are an SEO Specialist who has 5 years of experience in product marketing.
            #             You know how to write the title of the product, so it becomes SEO-friendly.
            #             You can use keywords effectively.
            #             With that experience, please diversify and sensationalize the following title {title} in 16 words maximum based on the following product description {current_description}. Ensure that the paragraph meets the following conditions:
            #             1. Identify whether the product is a toy unit or spare parts, if the product is toy unit remove all brand names execpt for Power Wheel brand.
            #             Answer:
            #             """
            #
            # human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
            # chat_prompt_template = ChatPromptTemplate(messages=[human_message_prompt],
            #                                           input_variables=['title', 'current_description'])

            human_template = """
                        please diversify and sensationalize the following title {title} in 16 words maximum based on the following product description {current_description}. Ensure that the paragraph meets the following conditions:

                        *Step 1: Brand Name Considerations*
                        Remove all brand names from the title unless the product is identified as a spare part. In the case of the brand name "Power Wheel," retain it.

                        *Step 2: Exclude Return Policies*
                        Remove all information related to return policies and procedures, ensuring that the paragraph does not contain any references to returns.

                        *Step 3: Ensure Unique Title*
                        To ensure that the generated title looks different from the provided one, emphasize distinct phrasing, synonyms, and alternative sentence structures while highlighting the product title.

                        *Step 4: Exclude Shipping Information*
                        Exclude all information about shipping.
                        
                        Answer:
                        """

            system_template = """As a content writer for an e-commerce site, Your goal is to create an attractive and SEO-friendly product title."""

            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
            system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
            chat_prompt_template = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
            chat_prompt_format = chat_prompt_template.format_messages(title=title, current_description=description)
            chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

            output = chat(chat_prompt_format)
            content = output.content
            match = re.findall(r'"(.*?)"', content)
            if match:
                print(f'Transform {title} title completed!')
                result = match[0]
            else:
                print(f'Transform {title} title completed!')
                result = content
        return result

    def transform_description(self, df):
        df['text_desc'] = df['Body (HTML)'].apply(self.parse)
        df['Body (HTML)'] = df.apply(lambda x: self.openai_edit(x['Title'], x['text_desc'], x['Item_Desc']), axis=1)
        df.drop(columns=['text_desc'], inplace=True)

    def transform_title(self, df):
        df['Title'] = df.apply(lambda x: self.openai_edit_title(x['Title'], x['Body (HTML)']), axis=1)

    def run(self):
        file_name = '001-005 Desc'
        df = pd.read_csv(
            f'original/{file_name}.csv'
            # 'cek.csv'
        )
        df['Vendor'] = df['Vendor'].astype('Int64').astype('str').replace('<NA>', '')
        self.transform_title(df)
        self.transform_description(df)
        catalog_df = df.loc[df['Vendor'] != ''].copy()
        catalog_df['Brand'] = catalog_df['Item_Desc'].apply(self.extract_brand)
        df.to_csv(
            f'final_result/{file_name}.csv',
            index=False)
        catalog_df.drop(columns=['Item_Desc'], inplace=True)
        catalog_df.to_csv(
            f'catalogue/{file_name}.csv',
            index=False
        )

    def extract_brand(self, item_specs):
        item_specs = item_specs.replace("\'", "\"")
        try:
            item_specs_data = json.loads(item_specs)
            result = item_specs_data['Brand']
        except:
            result = 'No Brand'
        return result

if __name__ == '__main__':
    t = TransformEbay()
    t.run()