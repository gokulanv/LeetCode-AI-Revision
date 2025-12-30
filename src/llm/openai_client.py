from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()

def get_completion(message: str):
    completion = client.chat.completions.create(
        model = os.getenv("OPENAI_MODEL") or "gpt-4o",
        messages=[
            {
                "role": "developer", 
                "content": "How would programming experts revise this problem and solution to help learn patterns and critical details needed for a coding interview from the problem and solution? \
                    Help me revise my approach with a short explanation for each pattern and detail. "},
            {
                "role": "user",
                "content": message,
            },
        ],
    )
    return completion.choices[0].message.content
