import json
from random import choice
from dotenv import load_dotenv
import openai
import os
from dataclasses import dataclass
import pandas as pd
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, PromptTemplate
from langchain.chat_models import ChatOpenAI
from selectolax.parser import HTMLParser
import re

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = openai_api_key
special = 'Â'

@dataclass
class TransformEbay:
    container: str = ''

    def parse(self, html):
        if pd.isna(html):
            result = html
        else:
            tree = HTMLParser(html)
            result = tree.css_first('body').text(strip=True)

        return result

    def desc_correction(self, description):
        if pd.isna(description):
            pass
        else:
            if "<li>" in description:
                pass
            else:
                description = description.replace('\n', '<br/>')
            description = description.replace('Ã—', '×')
            description = description.replace('€“', '-')
            description = description.replace('€™', "'")
            description = description.replace('€', '"')
            description = description.replace('Â', '')

        # Define a regular expression pattern to match paragraphs containing the word "warranty"
        # pattern = r'<p>.*?warranty.*?</p>'

        # Use re.sub() to remove matching paragraphs
        # description_no_warranty = re.sub(pattern, '', description, flags=re.IGNORECASE)

        return description

    def title_correction(self, title):
        if pd.isna(title):
            pass
        else:
            title = title.replace('Ã—', '×')
            title = title.replace('€“', '-')
            title = title.replace('€™', "'")
            title = title.replace('€', '"')
            title = title.replace('Â', '')

        return title

    def generate_handle(self, title):
        if type(title) != float:
            self.container = title.lower().replace(' -', '').replace(' ', '-').replace(',', '')
        result = self.container

        return result

    def openai_edit(self, title, description, additional_spec):
        # try:
        if pd.isna(description):
            result = description

        else:

    #            """Rewrite the {current_description} for a product with the title '{title}' and include the following additional specification: '{additional_spec}'. Organize and emphasize its key features and technical specifications using bullet points consistently throughout the description. Ensure that the description is engaging and informative while consistently excluding any payment details, return policies, feedback references, company background, warranty terms, shipping information, marketplace references, or ASIN number. Begin each description uniquely avoid description begin with 'introducing' or 'experience'. Maintain consistency by always beginning with a compelling opening sentence and incorporating the phrase 'ride-on' in an engaging manner. Utilize distinct phrasing, synonyms, and alternative sentence structures to consistently create a unique product description."""
    #             human_template = """Rewrite this {current_description} description for a product with the title '{title}' and include the following additional specification: '{additional_spec}'. Remove information about payment, return, feedback, company background, warranty, shipping, marketplace references, and ASIN number. Maintain consistency by always beginning with a compelling opening sentence and incorporating the phrase 'ride-on' in an engaging manner. Prohibited to begin description with 'introducing' or 'experience'. Utilize distinct phrasing, synonyms, and alternative sentence structures to consistently create a unique product description. Present output in form of paragraph and bullet point of key features and specifications."""

    # -2 Original prompt
    #             human_template = """Rewrite this {current_description} with an adventurous and playful tone for a product titled '{title}' that embodies the spirit of outdoor fun and imaginative exploration. Include the following additional specification: '{additional_spec}'. Remove information about payment, return, feedback, company background, warranty, shipping, marketplace references, and ASIN number. Begin with an exciting opening sentence that captures the essence of the ride-on experience. Infuse the description with enthusiasm and creativity, always incorporating the phrase 'ride-on' in a way that ignites the reader's sense of adventure. Avoid starting the description with 'introducing', 'experience' or 'get ready'. Utilize vivid language, unique phrasing, synonyms, and alternative sentence structures to consistently create a unique product description. Present the output as a paragraph while also including bullet points to highlight key features and specifications. Use imperial metrics for all measurement unit and convert its value.
    # """

    # -1 Original prompt
    #             human_template = """Rewrite this {current_description} description with an adventurous and playful tone for a product titled '{title}' that embodies the spirit of outdoor fun and imaginative exploration. Include the following additional specification: '{additional_spec}'. Remove information about payment, return, feedback, company background, warranty, shipping, marketplace references, and ASIN number. Begin with an exciting opening sentence that captures the essence of the ride-on experience. Infuse the description with enthusiasm and creativity, always incorporating the phrase 'ride-on' in a way that ignites the reader's sense of adventure. avoids using words commonly associated with product introductions, such as 'introducing,' 'experience,' and 'get ready'. Instead, find a dynamic and creative way to capture the essence of the ride-on experience and ignite the reader's sense of adventure. Utilize vivid language, unique phrasing, synonyms, and alternative sentence structures to consistently craft a product description that radiates the thrill of playtime. Present the output as a paragraph while also including bullet points to highlight key features and specifications. Use imperial metrics for all measurement unit and convert its value.
    # """

    # Original prompt
    #             system_template = """
    #             You are an SEO specialist in a ride-on toy company. Your task is to enhance the provided product description for the given product title by enriching it with the provided additional specifications. Infuse the description with an adventurous and playful tone that embodies the spirit of outdoor fun and imaginative exploration. Include all the provided additional specifications, key features, and product specifications. Remove all special characters. Remove any information regarding payment, return, feedback, company background, warranty, shipping, contact us. Remove information regarding marketplace platform such as eBay, Amazon, etc. Remove information regarding health issue warning such as cancer, reproductive harm, birth defects. In the opening paragraph, always use the {title} itself without any word before it except "The". Always incorporate the phrase 'ride-on' seamlessly into the description. Utilize vivid language, unique phrasing, synonyms, and alternative sentence structures to consistently create a one-of-a-kind product description. Use imperial metrics for all measurement units and convert their values where necessary. Avoid to put note in the description. Present the output in HTML format with a well-structured parahgraph that constantly including all key features and specifications in bullet points. Your ultimate goal is to create an engaging and SEO-friendly product description.
    #             """
    #
    #             human_template = """
    #             Please elevate {current_description} of {title} product which has {additional_spec} as additional specification. Answer:
    #             """

                # Describe every each variant of product individually for all product variant provided.

            # system_template = """
            # You are an SEO specialist in a ride-on toy company. Your task is to diversify the provided product description using vivid language, unique phrasing, synonyms, and alternative sentence structures with adventurous and playful tone that completely describes every each variant of the product individually for all product variant provided and make clear boundaries between them. Enriching it with the provided this following additional specifications. Include all the provided additional specifications, key features, and product specifications. Completely eliminate any reference to payment, return, feedback, company background, warranty, shipping, contact us, eBay, Amazon, cancer, reproductive harm, birth defects or similar terms from the new description. In the opening paragraph, always use the {title} itself without any word before it except "The". Always incorporate the phrase 'ride-on' seamlessly into the description. Keep the terms "car" and "truck" intact, without substituting them with synonyms. Use imperial metrics for all measurement units and convert their values where necessary. Avoid to put note in the description. Present the output in HTML format with a well-structured parahgraph that constantly including all key features and specifications in bullet points.
            # """

            system_template = """
            You are an SEO specialist in a ride-on toy company. Your task is to diversify the provided product description. Describe every each variant of product individually for all product variant provided and make clear boundaries between them. Enriching it with the provided additional specifications. Include all the provided additional specifications, key features, and product specifications. Remove any information regarding payment, return, feedback, company background, warranty, shipping, contact us. Remove information regarding marketplace platform such as eBay, Amazon, etc. Remove information regarding health issue warning such as cancer, reproductive harm, birth defects. In the opening paragraph, always use the {title} itself without any word before it except "The". Always incorporate the phrase 'ride-on' seamlessly into the description. Utilize vivid language, unique phrasing, synonyms, and alternative sentence structures with adventurous and playful tone to consistently create a one-of-a-kind product description. Keep the terms "car" and "truck" intact, without substituting them with synonyms. Use imperial metrics for all measurement units and convert their values where necessary. Avoid to put note in the description. Present the output in HTML format with a well-structured parahgraph that constantly including all key features and specifications in bullet points. Your ultimate goal is to create an engaging and SEO-friendly product description.
            """

            # human_template = """
            # Please boost {current_description} and enrich it with {additional_spec} as additional specification. Answer:
            # """

            human_template = """
            Current description: {current_description}
            Additional specification: {additional_spec}
            Answer:
            """

            # prompt_template = """
            # You are an SEO specialist in a ride-on toy company. Your task is to diversify this following description {current_description}. Describe every each variant of product individually for all product variant provided and make clear boundaries between them. Enriching it with the provided additional specifications {additional_spec}. Include all the provided additional specifications, key features, and product specifications. Remove any information regarding payment, return, feedback, company background, warranty, shipping, contact us. Remove information regarding marketplace platform such as eBay, Amazon, etc. Remove information regarding health issue warning such as cancer, reproductive harm, birth defects. In the opening paragraph, always use the {title} itself without any word before it except "The". Always incorporate the phrase 'ride-on' seamlessly into the description. Utilize vivid language, unique phrasing, synonyms, and alternative sentence structures with adventurous and playful tone to consistently create a one-of-a-kind product description. Keep the terms "car" and "truck" intact, without substituting them with synonyms. Use imperial metrics for all measurement units and convert their values where necessary. Avoid to put note in the description. Present the output in HTML format with a well-structured parahgraph that constantly including all key features and specifications in bullet points. Your ultimate goal is to create an engaging and SEO-friendly product description.
            # """

            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
            system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
            chat_prompt_template = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
            chat_prompt_format = chat_prompt_template.format_messages(title=title, current_description=description,
                                                                      additional_spec=additional_spec)
            chat = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=0.4, request_timeout=120)

            output = chat(chat_prompt_format)
            content = output.content
            result = content
            print(f'Transform {title} description completed!')
        # except:
        #     result = "Failed"

        return result

    def openai_edit_title(self, title, description):
        if pd.isna(title):
            result = title

        else:
            # prompt_template = """Generate a new product title based on the original title {title} completely eliminate any reference to shipping, delivery, or similar terms from the new title. Instead, focus on paraphrasing the title using synonyms and alternative phrasing while maintaining its original essence."""

            prompt_template = """Paraphrasing the original title {title} into 1 fresh product title that completely eliminate any reference to shipping, delivery, or similar terms and avoid to use "Ultimate" word.""" #using synonyms and alternative phrasing while maintaining its original essence."""
            prompt = PromptTemplate.from_template(prompt_template)
            prompt_format = prompt.format_prompt(title=title)

            chat = openai.Completion.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt_format.text,
                temperature=0.6,
                top_p=0.37,
                max_tokens=80,
                request_timeout=60
            )

            content = chat.choices[0].text.replace('"', '').strip()
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
        threshold = len(df) * 0.7
        df['Body (HTML)'] = df.apply(lambda x: self.replace_rideon(x['Body (HTML)']) if x.name < threshold else self.replace_rideon2(x['Body (HTML)']), axis=1)
        df.drop(columns=['text_desc'], inplace=True)

    def transform_title(self, df):
        df['Title'] = df.apply(lambda x: self.openai_edit_title(x['Title'], x['Body (HTML)']), axis=1)

    def replace_rideon(self, description):
        try:
            count_of_rideon = description.count('ride-on')
            if count_of_rideon > 1:
                stage1 = description.replace('ride-on', '<a href=https://www.magiccars.com>ride-on</a>', 2)
                result = stage1.replace('<a href=https://www.magiccars.com>ride-on</a>', 'ride-on', 1)
            else:
                result = description.replace('ride-on', '<a href=https://www.magiccars.com>ride-on</a>', 1)
        except:
            result = description
        return result

    def replace_rideon2(self, description):
        subtitute_words = ['remote control ride on', 'rc ride on']
        choosen_sub_word = choice(subtitute_words)
        try:
            count_of_rideon = description.count('ride-on')
            if 'remote' in description.lower():
                if count_of_rideon > 1:
                    stage1 = description.replace('ride-on', f'<a href=https://www.magiccars.com>{choosen_sub_word}</a>', 2)
                    result = stage1.replace(f'<a href=https://www.magiccars.com>{choosen_sub_word}</a>', 'ride-on', 1)
                else:
                    result = description.replace('ride-on', f'<a href=https://www.magiccars.com>{choosen_sub_word}</a>', 1)
            else:
                if count_of_rideon > 1:
                    stage1 = description.replace('ride-on', f'<a href=https://www.magiccars.com>ride-on</a>', 2)
                    result = stage1.replace(f'<a href=https://www.magiccars.com>ride-on</a>', 'ride-on', 1)
                else:
                    result = description.replace('ride-on', f'<a href=https://www.magiccars.com>ride-on</a>', 1)
        except:
            result = description
        return result

    def run(self):
        file_name = '20230926_041-045_Desc'
        df = pd.read_csv(
            f'original/{file_name}_Original.csv'
            # 'cek_Original.csv'
        )
        # df['Vendor'] = df['Vendor'].astype('Int64').astype('str').replace('<NA>', '')
        self.transform_title(df)
        self.transform_description(df)

        # Generate Transformed File
        transformed_df = df.copy()
        transformed_df['Body (HTML)'] = transformed_df['Body (HTML)'].apply(self.desc_correction)
        transformed_df['Title'] = transformed_df['Title'].apply(self.title_correction)
        transformed_df['Handle'] = transformed_df['Title'].apply(self.generate_handle)
        transformed_df.to_csv(
            f'transformed/{file_name}_Transformed.csv',
            index=False, encoding="utf-8-sig")

        # Generate Catalog File
        catalog_df = transformed_df.loc[transformed_df['Vendor'] == 'Magic Cars'].copy()
        catalog_df['Brand'] = catalog_df['Item_Desc'].apply(self.extract_brand)
        catalog_df.drop(columns=['Item_Desc'], inplace=True)
        catalog_df.to_csv(
            f'catalogue/{file_name}_Catalogue.csv',
            index=False, encoding="utf-8-sig")

        # Generate Final File
        final_df = transformed_df.drop(columns=['Item_Desc', 'Shipping'], axis=1)
        final_df.to_csv(
            f'final_result/{file_name}_Final.csv',
            index=False, encoding="utf-8-sig")

    def extract_brand(self, item_specs):
        if pd.isna(item_specs):
            result = item_specs
        else:
            item_specs = item_specs.replace("\'", "\"")
            try:
                item_specs_data = json.loads(item_specs)
                result = item_specs_data['Brand']
            except Exception as e:
                print(e)
                result = ''

        return result

    def extract_weight(self, item_specs):
        item_specs = item_specs.replace("\'", "\"")
        try:
            item_specs_data = json.loads(item_specs)
            weight = item_specs_data['Item Weight']
            pattern = r'(\d+)\s*(\S+)'
            match = re.match(pattern, weight)
            if match:
                weight_value = int(match.group(1))
                weight_unit = match.group(2)
                weight_info = {
                    'weight_value': weight_value,
                    'weight_unit': weight_unit
                }
                result = weight_info
            else:
                result = ''
        except Exception as e:
            print(e)
            result = ''
        return result


if __name__ == '__main__':
    t = TransformEbay()
    t.run()