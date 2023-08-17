from dotenv import load_dotenv
import openai
import os
from dataclasses import dataclass
import pandas as pd
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.chat_models import ChatOpenAI
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
            human_template = """
            You are required to modify the description. The description constructed by single paragraph (maximum 250 words) and should has "Ride On" phrase at least 1 if it is not found you should insert it as part of sentence of the paragraph without make new sentence.
            Next step You have to make the first "Ride On" phrase linked to https://teesparty.myshopify.com/ with article tag for each variant.
            Then You need to create bullet point of features and specifications for each variant below each paragraph.
            You also need to remove any references to ebay or returns or things like that in the description or mentioning of not to leave bad feedback.
            Ensure that the result is in body element of HTML format and follows the provided title and description.
            Title:
            {title}
            Description:
            {current_description}
            """

            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
            chat_prompt_template = ChatPromptTemplate(messages=[human_message_prompt],
                                                      input_variables=['title', 'current_description'])

            chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.1)

            output = chat(chat_prompt_template.format_prompt(title=title, current_description=description).to_messages())
            result = output.content
        return result

    def transform_description(self, df):
        df['text_desc'] = df['Body (HTML)'].apply(self.parse)
        df['Body (HTML)'] = df.apply(lambda x: self.openai_edit(x['Title'], x['text_desc']), axis=1)
        df.drop(columns='text_desc', inplace=True)
        df.to_csv('openai_result.csv', index=False)

    def run(self):
        df = pd.read_csv('result.csv')
        self.transform_description(df)

if __name__ == '__main__':
    t = TransformEbay()
    t.run()