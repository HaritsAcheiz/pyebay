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

            # condition = """
            # 1. Remove informations about payment,
            # 2. Remove informations about return,
            # 3. Remove information about feedback,
            # 4. Remove information about us,
            # 5. Remove information about copyright,
            # 6. Remove information about warranty,
            # 7. Remove information about shipping,
            # 8. Remove reference to another marketplace like eBay or Amazon,
            # 9. Replace all brand name with magic cars,
            # 10. Replace all shop name with Azautodetailing,
            # 11. Paragraph should has <a href=https://azautodetailing.com/collections/all>ride-on</a>.
            # """
            #
            # human_template = """
            # Please diversify the following description {current_description} that should meet the following condition {condition} into a paragraph limited to 250 words based on the following product title {title}.
            # Present the output in HTML format inside <body> element.
            # Answer:
            # """

            human_template = """
            Please create only 1 paragraph limited to 250 words based on the given product title and description. Ensure that the paragraph meets the following conditions:
            1. Remove any mention of payment details, including methods and options.
            2. Omit all information related to return policies and procedures.
            3. Exclude any references to feedback, both positive and negative.
            4. Leave out any content about the company ("us") and its background.
            5. Do not include any references to copyright or legal information.
            6. Remove any mentions of warranty terms or coverage.
            7. Exclude all information about shipping, including options and times.
            8. Exclude any references to other marketplaces like eBay or Amazon.
            9. Remove any mentions of ASIN number.
            10. Add bullet points to mention key specifications and features of the product.
            11. Remove all brand names except the brand name is Power Wheels if product is not identified as spare part.
            12. Replace the shop name with "Azautodetailing".
            13. **Specific Instruction: Insert the following HTML element exactly as shown, make it blend with the paragraph. This element must contain the phrase "ride-on" and link to "https://azautodetailing.com/collections/all":**
            <a href="https://azautodetailing.com/collections/all">ride-on</a>
            14. Present the output in HTML format.
            Product Title: {title}
            Product Description: {current_description}
            Answer:
            """

            human_template = """
            Craft a captivating and unique product description for a {title} that instantly grabs the customer's attention. Highlight the [MAIN BENEFIT/FEATURE] that sets it apart from the rest. Infuse excitement by showcasing the [QUALITY/EXPERIENCE] and [KEY FEATURES] that make this product a must-have. Engage the reader with details about [USER AGE], [USAGE METHOD], and [ADDITIONAL FEATURES]. Provide [SPECIFICATIONS] in [USA MEASUREMENTS] to offer a clear picture of the product's dimensions and capabilities. Use enticing language to create a sense of urgency and encourage immediate action. Make sure to exclude any references to [PAYMENT METHODS], [FEEDBACK], [SHIPPING], [RETURN & REFUND POLICY], [WARRANTY], [EBAY] or [RATINGS], focusing solely on igniting the desire to own this exceptional product. Conclude by inviting customers to EMBEDDED LINK: CONTACT US for personalized assistance. Additionally, embed a hyperlink for the term 'ride on' that directs to [EMBEDDED LINK: www.MagicCars.com]."""

            # human_template = """
            #             Please diversify this following description: {current_description} into only 1 paragraph limited to 250 words based on this following product title {title}. Ensure that the paragraph meets the following conditions:
            #             1. Remove any mention of payment details, including methods and options.
            #             2. Omit all information related to return policies and procedures.
            #             3. Exclude any references to feedback, both positive and negative.
            #             4. Leave out any content about the company ("us") and its background.
            #             5. Do not include any references to copyright or legal information.
            #             6. Remove any mentions of warranty terms or coverage.
            #             7. Exclude all information about shipping, including options and times.
            #             8. Exclude any references to other marketplaces like eBay or Amazon.
            #             9. Remove any mentions of ASIN number.
            #             10. Add bullet points to mention key specifications and features of the product.
            #             11. Remove all brand names if product is not identified as spare part except the brand name is Power Wheels.
            #             12. Replace the shop name with "Azautodetailing".
            #             13. **Specific Instruction: Insert the following HTML element exactly as shown, make it blend with the paragraph. This element must contain the phrase "ride-on" and link to "https://azautodetailing.com/collections/all":**
            #             <a href="https://azautodetailing.com/collections/all">ride-on</a>
            #             14. Present the output in HTML format.
            #             Product Title: {title}
            #             Product Description: {current_description}
            #             Answer:
            #             """

            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
            chat_prompt_template = ChatPromptTemplate(messages=[human_message_prompt],
                                                      # input_variables=['title', 'current_description'])
                                                      input_variable=['title'])
            chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.9)

            # output = chat(chat_prompt_template.format_prompt(title=title, current_description=description).to_messages())
            output = chat(
                chat_prompt_template.format_prompt(title=title).to_messages())
            content = output.content
            print(f'Transform {title} description completed!')
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
                        With that experience, please diversify and sensationalize the following title {title} in 16 words maximum based on the following product description {current_description}. Ensure that the paragraph meets the following conditions:
                        1. Identify whether the product is a toy unit or spare parts, if the product is toy unit remove all brand names execpt for Power Wheel brand.
                        Answer:
                        """

            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
            chat_prompt_template = ChatPromptTemplate(messages=[human_message_prompt],
                                                      input_variables=['title', 'current_description'])

            chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.9)

            output = chat(chat_prompt_template.format_prompt(title=title, current_description=description).to_messages())
            content = output.content
            match = re.search(r'"(.*?)"', content)

            if match:
                return match.group(1)
                print(f'Transform {title} title completed!')
            else:
                print(f'Transform {title} title completed!')
                return content
        return result

    def transform_description(self, df):
        df['text_desc'] = df['Body (HTML)'].apply(self.parse)
        df['Body (HTML)'] = df.apply(lambda x: self.openai_edit(x['Title'], x['text_desc']), axis=1)
        df.drop(columns='text_desc', inplace=True)

    def transform_title(self, df):
        df['Title'] = df.apply(lambda x: self.openai_edit_title(x['Title'], x['Body (HTML)']), axis=1)

    def run(self):
        df = pd.read_csv('result 1-5.csv')
        df['Vendor'] = df['Vendor'].astype('Int64').astype('str').replace('<NA>', '')
        self.transform_title(df)
        self.transform_description(df)
        df.to_csv('openai_result 1-5.csv', index=False)

if __name__ == '__main__':
    t = TransformEbay()
    t.run()