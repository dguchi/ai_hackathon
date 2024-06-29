# @title Install requirements
import json
import os
import time

#import deepl
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
# 環境変数を上書き
os.environ["STABILITY_KEY"] = ""
# @title Define functions

# STABILITY_KEY = os.getenv("STABILITY_KEY")
STABILITY_KEY = ""
# DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
#DEEPL_API_KEY = ""


print(STABILITY_KEY)


def send_generation_request(
    host,
    params,
):
    headers = {"Accept": "image/*", "Authorization": f"Bearer {STABILITY_KEY}"}

    # Encode parameters
    files = {}
    image = params.pop("image", None)
    mask = params.pop("mask", None)
    if image is not None and image != "":
        files["image"] = open(image, "rb")
    if mask is not None and mask != "":
        files["mask"] = open(mask, "rb")
    if len(files) == 0:
        files["none"] = ""

    # Send request
    print(f"Sending REST request to {host}...")
    response = requests.post(host, headers=headers, files=files, data=params)
    if not response.ok:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

    return response


def send_async_generation_request(
    host,
    params,
):
    headers = {"Accept": "application/json", "Authorization": f"Bearer {STABILITY_KEY}"}

    # Encode parameters
    files = {}
    if "image" in params:
        image = params.pop("image")
        files = {"image": open(image, "rb")}

    # Send request
    print(f"Sending REST request to {host}...")
    response = requests.post(host, headers=headers, files=files, data=params)
    if not response.ok:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

    # Process async response
    response_dict = json.loads(response.text)
    generation_id = response_dict.get("id", None)
    assert generation_id is not None, "Expected id in response"

    # Loop until result or timeout
    timeout = int(os.getenv("WORKER_TIMEOUT", 500))
    start = time.time()
    status_code = 202
    while status_code == 202:
        response = requests.get(
            f"{host}/result/{generation_id}",
            headers={**headers, "Accept": "image/*"},
        )

        if not response.ok:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        status_code = response.status_code
        time.sleep(10)
        if time.time() - start > timeout:
            raise Exception(f"Timeout after {timeout} seconds")

    return response


# @title Stable Image Ultra
def generate_image(prompt: str, file_name: str):
    prompt = prompt  # @param {type:"string"}
    negative_prompt = ""  # @param {type:"string"}
    aspect_ratio = "3:2"  # @param ["21:9", "16:9", "3:2", "5:4", "1:1", "4:5", "2:3", "9:16", "9:21"]
    seed = 0  # @param {type:"integer"}
    output_format = "png"  # @param ["webp", "jpeg", "png"]
    engine_id = "sd3"
    host = f"https://api.stability.ai/v2beta/stable-image/generate/{engine_id}"

    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "aspect_ratio": aspect_ratio,
        "seed": seed,
        "output_format": output_format,
    }

    response = send_generation_request(host, params)

    # Decode response
    output_image = response.content
    finish_reason = response.headers.get("finish-reason")
    seed = response.headers.get("seed")

    # Check for NSFW classification
    if finish_reason == "CONTENT_FILTERED":
        raise Warning("Generation failed NSFW classifier")

    # Save and display result
    generated = f"{'html/' + file_name}.{output_format}"
    with open(generated, "wb") as f:
        f.write(output_image)
    print(f"Saved image {generated}")


def make_prompt_for_main_image(business_type, target, personas_gender, age, image_color, detail, catchcopy):
    prompt = "あなたは魅力的で目を引くランディングページのメイン背景画像を生成します。\n"
    prompt = addCondition(prompt, "ビジネスタイプ", business_type)
    prompt = addCondition(prompt, "ターゲット", target)
    prompt = addCondition(prompt, "ペルソナの性別", personas_gender)
    prompt = addCondition(prompt, "ペルソナの年齢", age)
    prompt = addCondition(prompt, "LPのイメージカラー", image_color)
    prompt = addCondition(prompt, "キャッチコピー", catchcopy)
    prompt = addCondition(prompt, "", detail)
    prompt += "\nこの画像は、訪問者に強い印象を与え、ページの目的を明確に伝えるものでなければなりません。また文字を画像内に表示する必要はありません。"
    return prompt


def make_prompt_for_feature_images(sales_points: list[str]):
    prompts = []
    for sales_point in sales_points:
        prompt = f"""
ランディングページのセールスポイント「{sales_point}」を視覚的に表現する画像を生成します。
この画像は、訪問者に即座に理解され、感情的な共鳴を呼び起こすデザインで、製品やサービスの核心的な魅力を際立たせます。
"""
        prompts.append(prompt)
    return prompts


def addCondition(pronpt, conditonType, condition):
    if len(condition) != 0:
        pronpt += "\n" + "・"
        if len(conditonType) != 0:
            pronpt += str(conditonType) + "は" + str(condition)
        else:
            pronpt += condition
    return pronpt


def translate_text(text, target_lang):
    #translator = deepl.Translator(DEEPL_API_KEY)
    #result = translator.translate_text(text, target_lang=target_lang)
    return text


def generate_hero_image(
    business_type: str, target: str, personas_gender: str, age: str, image_color: str, detail: str, catchcopy: str
):
    prompt = make_prompt_for_main_image(business_type, target, personas_gender, age, image_color, detail, catchcopy)
    translated_prompt = translate_text(prompt, "EN-US")
    print(translated_prompt)
    generate_image(translated_prompt, "hero")


def generate_feature_images(sales_points: list[str]):
    prompts = make_prompt_for_feature_images(sales_points)
    translated_prompts = [translate_text(prompt, "EN-US") for prompt in prompts]
    for index, prompt in enumerate(translated_prompts):
        generate_image(prompt, f"feature_{index}")


def generate_hero_image_DallE(
    client: OpenAI,
    form_data: dict
):  
    prompt = make_prompt_for_main_image(form_data.get("industry"),
                                        form_data.get("target"),
                                        form_data.get("gender"),
                                        form_data.get("age"), 
                                        form_data.get("color"), 
                                        form_data.get("detail"),
                                        form_data.get("catchcopy"))
    print(prompt)
    response = client.images.generate(
        model="dall-e-2",
        prompt=prompt,
        size="256x256",
        quality="standard",
        n=1
    )
    image_url = response.data[0].url
    image_data = requests.get(image_url).content

    with open("./html/hero.png", "wb") as file:
        file.write(image_data)


# genereate_hero_image(
#     business_type="飲食店",
#     target="",
#     personas_gender="女性",
#     age="20代",
#     image_color="オレンジ",
#     detail="",
#     catchcopy="",
# )
