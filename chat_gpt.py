from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.chat_models import ChatOpenAI
import pandas as pd
from dotenv import load_dotenv
import openai
import os
import re

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = openai_api_key


def openai_edit_title(title):
    if pd.isna(title):
        result = title

    else:
        # system_template = """As a content writer for an e-commerce site, Your goal is to create an attractive and SEO-friendly product title."""

        # human_template = """Generate a product title within 70 characters or less for our ride-on toy that evokes a sense of adventure and playfulness without using initiation words such as 'embark,' 'unleash,' etc. Remove any information about payment, return, feedback, company background, warranty, shipping, marketplace references, and ASIN number. Draw inspiration from the following description {current_description} while maintaining a adventurous and playful tone. Utilize vivid language, unique phrasing, synonyms, and alternative sentence structures to avoid plagiarism from this {title}. Ensure there is no exclamation mark in the end of the title. """

        system_template = """You are SEO specialist in ride-on toy company. Your job is diversify provided title so it is not considered as duplicate content. Remove all information about shipping and return. Utilize synonyms and alternative word to consistently create a one-of-a-kind product title."""  # Your ultimate goal is to create an engaging and SEO-friendly product title"""

        human_template = """Provide 5 new unique product titles by diversifying the following product title {title}. Answer:"""

        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        chat_prompt_template = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
        chat_prompt_format = chat_prompt_template.format_messages(title=title)
        chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7, request_timeout=60)

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

if __name__ == '__main__':
    df = pd.read_csv('diversify title.csv', encoding='utf-8-sig')
    df['title2'] = df['title'].apply(openai_edit_title)
    df.to_csv('diversified title 2.csv', encoding='utf-8-sig')