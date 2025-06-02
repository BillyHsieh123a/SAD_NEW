from openai import OpenAI
import os
from dotenv import load_dotenv
# import re

OPENAI_API_KEY = None

def init_get_ai_comments():
    global OPENAI_API_KEY
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_comments(image_url): # need to pass OPENAI_API_KEY and image url
    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional fashion consultant."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    },
                    {
                        "type": "text",
                        "text": (
                            "Please give a very concise, single-paragraph overall outfit comment and suggestion in English, "
                            "no more than 30 words. Do not use bullet points, titles, or line breaks."
                        )
                    }
                ]
            }
        ]
    )

    ai_comment = response.choices[0].message.content.strip()
    return ai_comment, ""  # Only one concise comment, no recommendation section

    # def clean_recommendation_text(raw_text: str) -> str:
    #     # 去除 markdown 編號與強調符號
    #     text = re.sub(r"\*\*|\d+\.\s*", "", raw_text)
    #     # 去除多餘空白
    #     text = re.sub(r"\n\s*", " ", text).strip()
    #     return text

    # embedding_input = clean_recommendation_text(recommendation_comment)

    # print("Embedding 輸入：")
    # print(embedding_input)

# sample_image_url = "https://shoplineimg.com/5f4760ee70e52e003f4199b5/657bfa1a28b4fe001af779e3/800x.jpg"
# # example
# init_get_ai_comments()
# overall_comment, recommendation_comment = get_comments(sample_image_url)

# 印出結果
# print("整體評價：")
# print(overall_comment)
# print("\n推薦建議：")
# print(recommendation_comment)