import os
import json

from google import genai

from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-3.5-flash"


def clean_json_response(text):
    return (
        text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )


def generate_collection_words(
    collection_name,
    collection_description="",
    total_words=20,
    level="beginner"
):
    prompt = f"""
    Generate {total_words} English vocabulary
    words for this topic.

    Topic:
    {collection_name}

    Description:
    {collection_description}

    Level:
    {level}

    Return ONLY valid JSON array.

    Example:

    [
      {{
        "english_word": "passport",
        "vietnamese_meaning": "hộ chiếu",
        "pronunciation": "/ˈpæspɔːrt/",
        "word_type": "noun"
      }}
    ]

    word_type must be one of:
    - noun
    - verb
    - adjective
    - adverb
    - preposition
    - conjunction
    - pronoun
    - interjection
    - other

    Rules:
    - vocabulary must match the topic
    - meaning must be Vietnamese
    - no duplicate words
    - return ONLY JSON
    """

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )

    cleaned_text = clean_json_response(response.text)

    return json.loads(cleaned_text)
