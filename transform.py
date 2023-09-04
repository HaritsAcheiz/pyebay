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

#            """Rewrite the {current_description} for a product with the title '{title}' and include the following additional specification: '{additional_spec}'. Organize and emphasize its key features and technical specifications using bullet points consistently throughout the description. Ensure that the description is engaging and informative while consistently excluding any payment details, return policies, feedback references, company background, warranty terms, shipping information, marketplace references, or ASIN number. Begin each description uniquely avoid description begin with 'introducing' or 'experience'. Maintain consistency by always beginning with a compelling opening sentence and incorporating the phrase 'ride-on' in an engaging manner. Utilize distinct phrasing, synonyms, and alternative sentence structures to consistently create a unique product description."""
            human_template = """Rewrite this {current_description} description for a product with the title '{title}' and include the following additional specification: '{additional_spec}'. Remove information about payment, return, feedback, company background, warranty, shipping, marketplace references, and ASIN number. Maintain consistency by always beginning with a compelling opening sentence and incorporating the phrase 'ride-on' in an engaging manner. Prohibited to begin description with 'introducing' or 'experience'. Utilize distinct phrasing, synonyms, and alternative sentence structures to consistently create a unique product description. Present output in form of paragraph and bullet point of key features and specifications."""

            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
            chat_prompt_template = ChatPromptTemplate.from_messages([human_message_prompt])
            chat_prompt_format = chat_prompt_template.format_messages(title=title, current_description=description,
                                                                      additional_spec=additional_spec)
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
            human_template = """
                        please diversify and sensationalize the following title {title} in 16 words maximum based on the following product description {current_description}. Ensure that the paragraph meets the following conditions:

                        *Step 1: Brand Name Considerations*
                        Remove all brand names from the title unless the product is identified as a spare part. In the case of the brand name "Power Wheel," retain it.

                        *Step 2: Exclude Return Policies*
                        Remove all information related to return policies and procedures, ensuring that the paragraph does not contain any references to returns.

                        *Step 3: Enhance Sensational Impact*
                        Encourage the AI to generate a sensational and attention-grabbing title without using specific words like "Ultimate". Emphasize the importance of creating a title that is exciting, compelling, and intriguing, ensuring it captures the essence of the product in an impactful way.

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
        df['Body (HTML)'] = df['Body (HTML)'].apply(self.replace_rideon)
        df.drop(columns=['text_desc'], inplace=True)

    def transform_title(self, df):
        df['Title'] = df.apply(lambda x: self.openai_edit_title(x['Title'], x['Body (HTML)']), axis=1)

    def replace_rideon(self, description):
        try:
            result = description.replace('ride-on', '<a href=https://www.magiccars.com>ride-on</a>', 1)
        except:
            result = description
        return result

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
        df.drop(columns=['Item_Desc', 'Shipping'], inplace=True)
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