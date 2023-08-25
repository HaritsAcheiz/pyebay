from dotenv import load_dotenv
import openai
import os
from dataclasses import dataclass
import pandas as pd
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
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

    def openai_edit(self, title, description):
        if pd.isna(description):
            result = description
        else:
            # human_template_v0 = """
            # You are required to paraphrase the description that constructed by single paragraph (maximum 250 words) with only 1 additional "Ride On" phrase as "<a>" element that linked to "https://azautodetailing.com/collections/all" and bullet point of features and specifications below paragraph for each variant.
            # Change all brand names to Magic Cars.
            # Remove any info about payment, customs declaration, free shipping, shipping information, delivery service, return policy, carriers information, mentioning of not to leave bad feedback and all word reference to marketplace platform such as ebay.
            # Present the output in HTML format within a <body> element. Ensure the accuracy of information based on the given title and description.
            # Title:
            # {title}
            # Description:
            # {current_description}
            # Answer
            # """

            # human_template_v1 = """
            # You are an SEO Specialist who has 5 years of experience in product marketing. You have created many content for products that you want to market.
            # You know how to write a description of the product, so it becomes SEO-friendly.
            # You can use keywords effectively and exclude unnecessary information on product descriptions such as (payment method, shipping method, returns, leaving a bad feedback warning, about us content, copyright and reference to another marketplace platform like eBay)
            # With that experience, please diversify the following description {current_description} within 250 words maximum based on the following product title {title} that use Magic Cars as a brand name which is associated with this link "https://azautodetailing.com/collections/all" as a product catalog.
            # Remove all information about payment method, shipping method, returns, feedback, about us content, copyright and reference to another marketplace platform like eBay
            # Present the output in HTML format within a <body> element.
            # Answer:
            # """

            condition = """
            1. Remove all informations about : payment, return, feedback, about us, copyright, carriers, warranty, shipping, exchange, reference to another marketplace like eBay or Amazon,
            2. Replace all brand name with magic cars,
            3. Replace all shop name with Azautodetailing,
            4. Paragraph should has <a href=https://azautodetailing.com/collections/all>ride-on</a>. 
            """

            human_template = """
            Please diversify the following description {current_description} that should meet the following condition {condition} into a paragraph limited to 250 words based on the following product title {title}.
            Present the output in HTML format inside <body> element.
            Answer:
            """

            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
            chat_prompt_template = ChatPromptTemplate(messages=[human_message_prompt],
                                                      input_variables=['title', 'current_description', 'condition'])
            chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

            output = chat(chat_prompt_template.format_prompt(title=title, current_description=description, condition=condition).to_messages())
            content = output.content
            return content

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

            human_template = """
                        You are an SEO Specialist who has 5 years of experience in product marketing.
                        You know how to write the title of the product, so it becomes SEO-friendly.
                        You can use keywords effectively.
                        With that experience, please diversify the following title {title} within 16 words maximum based on the following product title {current_description}.
                        Identify whether the product is a toy unit or spare parts, if it is a toy unit change all brand names into "Magic Cars".
                        Answer:
                        """

            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
            chat_prompt_template = ChatPromptTemplate(messages=[human_message_prompt],
                                                      input_variables=['title', 'current_description'])

            chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

            output = chat(chat_prompt_template.format_prompt(title=title, current_description=description).to_messages())
            content = output.content
            match = re.search(r'"(.*?)"', content)

            if match:
                return match.group(1)
            else:
                return content
        return result

    def transform_description(self, df):
        df['text_desc'] = df['Body (HTML)'].apply(self.parse)
        df['Body (HTML)'] = df.apply(lambda x: self.openai_edit(x['Title'], x['text_desc']), axis=1)
        df.drop(columns='text_desc', inplace=True)

    def transform_title(self, df):
        df['Title'] = df.apply(lambda x: self.openai_edit_title(x['Title'], x['Body (HTML)']), axis=1)

    def run(self):
        df = pd.read_csv('result.csv')
        df['Vendor'] = df['Vendor'].astype('Int64').astype('str').replace('<NA>', '')
        self.transform_title(df)
        self.transform_description(df)
        df.to_csv('openai_result.csv', index=False)

if __name__ == '__main__':
    t = TransformEbay()
    t.run()