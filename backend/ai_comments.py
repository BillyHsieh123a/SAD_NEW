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
            {"role": "system", "content": "你是一位專業時尚顧問。"},
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
                        "text": """
                            請根據這張穿搭照給出購買建議與穿搭評價，包括整體評價、推薦建議。
                            【請輸出以下格式】

                            ### 整體評價：
                            - 風格：請填寫
                            - 顏色搭配：請填寫
                            - 合身度與版型：請填寫
                            - 適合場合：請填寫（例如約會、上班、日常）

                            ### 推薦建議（結構化）：
                            請針對以下三種服飾推薦類型，分別輸出三段語意濃縮的文字描述。每段請直接陳述內容，不要加上任何標題或分類詞，例如「推薦可搭配的服飾：」這類前綴都不需要。請使用中性、描述性的語氣，避免口語化與列點，並將每段控制在 2~3 句，方便後續進行語意向量嵌入（embedding）。
                            推薦類型如下：
                            1. 可搭配的服飾建議（如外套、鞋款、包包等）
                            2. 相似風格的商品建議（如類似風格或顏色的上衣）
                            3. 根據體型或膚色更適合的服飾建議（如剪裁、色彩）

                            請使用繁體中文輸出。
                        """
                    }
                ]
            }
        ]
    )

    # print(response.choices[0].message.content)
    ai_comment = response.choices[0].message.content

    split_marker = "### 推薦建議："

    if split_marker in ai_comment:
        overall_comment, recommendation_comment = ai_comment.split(split_marker, 1)
        overall_comment = overall_comment.replace("### 整體評價：", "").strip()
        recommendation_comment = recommendation_comment.strip()
    else:
        overall_comment = ai_comment.strip()
        recommendation_comment = ""

    return overall_comment, recommendation_comment

    # def clean_recommendation_text(raw_text: str) -> str:
    #     # 去除 markdown 編號與強調符號
    #     text = re.sub(r"\*\*|\d+\.\s*", "", raw_text)
    #     # 去除多餘空白
    #     text = re.sub(r"\n\s*", " ", text).strip()
    #     return text

    # embedding_input = clean_recommendation_text(recommendation_comment)

    # print("Embedding 輸入：")
    # print(embedding_input)

sample_image_url = "https://shoplineimg.com/5f4760ee70e52e003f4199b5/657bfa1a28b4fe001af779e3/800x.jpg"

# example
init_get_ai_comments()
overall_comment, recommendation_comment = get_comments(sample_image_url)

# 印出結果
# print("整體評價：")
# print(overall_comment)
# print("\n推薦建議：")
# print(recommendation_comment)