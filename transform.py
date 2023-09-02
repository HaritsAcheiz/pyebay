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
        html = """
        *Step 15: Present Output in HTML Format*
        Format the output in HTML format, incorporating all the above steps. The final product description should be presented in valid HTML markup.
                   
        *Step 13: Insert HTML Element*
        Insert the following HTML element exactly as shown: <a href="https://www.magiccars.com">Check out our ride-on collection</a>. This element must contain the phrase "ride-on" and link to the provided URL.
        """
        if pd.isna(description):
            result = description

        else:
            human_template = """
            Your task is to follow the steps outlined below to ensure the generated description adheres to the specified conditions:
            
            *Step 1: Introduction*
            Create a single paragraph limited to 250 words, based on the given product title, description and additional specification. Ensure that the description does not start with the word "Introducing". The aim is to provide concise and relevant information while ensuring compliance with specific conditions.
            
            *Step 2: Remove Payment Details*
            Omit any references to payment methods and options, ensuring that no payment-related details are mentioned within the paragraph.
            
            *Step 3: Exclude Return Policies*
            Remove all information related to return policies and procedures, ensuring that the paragraph does not contain any references to returns.
            
            *Step 4: Omit Feedback References*
            Exclude any references to feedback, whether positive or negative, to keep the focus on the product's specifications and features.
            
            *Step 5: Remove Company Background*
            Omit any content about the company ("us") and its background, ensuring that the paragraph solely focuses on the product.
            
            *Step 6: Exclude Warranty Terms*
            Remove any mentions of warranty terms or coverage, shifting the focus to the product's attributes rather than its warranty.
            
            *Step 7: Exclude Shipping Information*
            Exclude all information about shipping, including shipping options and delivery times, as these details are not required in the paragraph.
            
            *Step 8: Remove Marketplace References*
            Omit any references to other marketplaces such as eBay or Amazon, maintaining a singular focus on the product.
            
            *Step 9: Remove ASIN Number*
            Ensure that any mentions of ASIN numbers are removed from the paragraph.
            
            *Step 10: Add Bullet Points for Specifications*
            Add bullet points to the paragraph to highlight key specifications and features of the product, enhancing readability and clarity.
            
            *Step 11: Brand Name Considerations*
            Remove all brand names from the paragraph unless the product is identified as a spare part. In the case of the brand name "Power Wheel," retain it.
            
            *Step 12: Replace Shop Name*
            Replace the shop name in the paragraph with "MagicCars" as specified.
            
            *Step 13: Create Closing Sentence with "Ride On" Link*
            Craft an enticing closing sentence that incorporates the phrase "<a href='https://www.magiccars.com/'>ride on</a>" while seamlessly inviting the reader to explore the product further through the provided link. Ensure that this HTML element <a href='https://www.magiccars.com/'>ride on</a> consistently connects the "ride on" phrase in all generated descriptions.

            *Step 14: Ensure Unique Description*
            To ensure that the generated description looks different from the provided one, emphasize distinct phrasing, synonyms, and alternative sentence structures while highlighting the product's key features and specifications.
            
            Product Title: {title}
            Product Description: {current_description}
            Additional Specification: {additional_spec}
            
            Answer:
            """

            system_template = """As a content writer for an e-commerce site, your task is to create an engaging product description using the provided title and description. Emphasize the product's features and specifications while adhering to specific guidelines. Craft a description that not only informs but is also SEO-friendly."""

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
                        Your task is Transform the Ordinary into the Extraordinary: Take this {title} to the Next Level with Feature or Benefit mentioned in the {current_description} adheres to the specified conditions:

                        *Step 1: Summarize Information from Title and Description*
                        Generate a title that succinctly summarizes the key information from both the title and description in 16 words or less.

                        *Step 2: Brand Name Considerations*
                        Remove all brand names from the title unless the product is identified as a spare part. In the case of the brand name "Power Wheel," retain it.

                        *Step 3: Exclude Return Policies*
                        Remove all information related to return policies and procedures, ensuring that the paragraph does not contain any references to returns.

                        *Step 4: Ensure Unique Title*
                        To ensure that the generated title looks different from the provided one, emphasize distinct phrasing, synonyms, and alternative sentence structures while highlighting the product title.

                        *Step 5: Exclude Shipping Information*
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