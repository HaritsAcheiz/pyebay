from dotenv import load_dotenv
import openai
import os
from dataclasses import dataclass
import pandas as pd

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = openai_api_key

@dataclass
class TransformEbay:

    def read_csv(self):
        df = pd.read_csv('result.csv')

        return df

    def to_csv(self):
        pass

    def openai_edit(self, input_text):
        if (input_text != '') or input_text:
            response = openai.Edit.create(
                model='text-davinci-edit-001',
                input=input_text,
                instruction="""
                In the body of the text such as you will see it says Ride On at least 1 time.
                I only want one of those keywords to link to the homepage.
                I do NOT want every phrase ride on to be a hyperlink as then it will look spammy.
                I just need the power of one hyperlink on each description of each page.
                I also need to remove any references to ebay or returns or things like that in the description or mentioning of not to leave bad feedback.
                I just need the description
                """,
                temperature=0,
                n=5
            )

            choices = []
            for choice in response['choices']:
                choices.append(choice['text'])
            result = ',\n'.join(choices)
        else:
            result = ''
        print(result)

        return result

    def edit_description(self, df):
        descriptions = df['Body (HTML)']
        df['description'] = df['Body (HTML)'].apply(self.openai_edit)
        print(df)

    def run(self):
        df = self.read_csv()
        self.edit_description(df)

if __name__ == '__main__':
    t = TransformEbay()
    t.run()