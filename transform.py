from dotenv import load_dotenv
import openai
import os
from dataclasses import dataclass
import pandas as pd
from langchain import PromptTemplate
from langchain.llms import OpenAI
# from langchain.prompts import ChatPromptTemplate
# from langchain.chat_models import ChatOpenAI
from selectolax.parser import HTMLParser

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
            # llm = OpenAI(model_name="text-davinci-003", temperature=0)
            llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0)
            # llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
            template = """
            You are required to generate new product description in form of only 1 paragraph (250 words maximum) and add bullet points that describe specification of product below the paragraph after write "Specification:".
            If the description contain more than 1 variant you should add more paragraph (250 words maximum for each paragraph) and bullet points to cover the other variant description.
            Description should mention "Ride On" phrase at least 1 time and the first "Ride On" phrase should be inside the article tag that link to https://teesparty.myshopify.com/ with article tag.
            You also need to remove any references to ebay or returns or things like that in the description or mentioning of not to leave bad feedback.
            The answer should be inside body tag of html format.
            All of the instruction should based on following title
            {title}
            and
            following current description
            {current_description}
            Answer:
            """

            prompt_template = PromptTemplate(
                input_variables=["title", "current_description"],
                template=template
                # messages=template
            )

            prompt = prompt_template.format(title=title, current_description=description)

            result = llm(prompt)

        return result

    def transform_description(self, df):
        df['text_desc'] = df['Body (HTML)'].apply(self.parse)
        df['Body (HTML)'] = df.apply(lambda x: self.openai_edit(x['Title'], x['text_desc']), axis=1)
        df.drop(columns='text_desc', inplace=True)
        df.to_csv('openai_result.csv', index=False)
        print(df)

    def run(self):
        df = pd.read_csv('result.csv')
        self.transform_description(df)

if __name__ == '__main__':
    t = TransformEbay()
    t.run()