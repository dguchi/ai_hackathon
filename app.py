# app.py
import random
import string
import os
import re

from flask import Flask, request, redirect ,render_template,jsonify
from openai import OpenAI
from dotenv import load_dotenv
from generate_image import generate_hero_image_DallE

load_dotenv()
key = os.getenv('OPENAI_API_KEY')
stable_difussion_key = os.getenv('STABLE_DIFUSION_API_KEY')

HTML_FOLDER = './html/'

# キーは環境変数に設定
client = OpenAI(
   api_key=key
)

app = Flask(__name__,static_folder='html')

def extract_html_content(text):
    new_string = text.replace("```html", "")
    new_string = new_string.replace("```", "")
    return new_string

def addCondition(prompt,conditonType,condition):
    if(len(condition) != 0):
        prompt += "\n" + "・"
        if (len(conditonType) != 0):
            prompt += str(conditonType) + "は" + str(condition)
        else:
            prompt += condition    
    return prompt

def makePromptForCatchcopy(businessType,target,personasGender,age,imageColor,detail):
    prompt = "以下の特徴をもつビジネスのキャッチコピーを考えてください。"
    addCondition(prompt,"業界",businessType)
    prompt = addCondition(prompt,"ターゲット",target)
    prompt = addCondition(prompt,"ペルソナの性別",personasGender)
    prompt = addCondition(prompt,"ペルソナの年齢",age)
#    prompt = addCondition(prompt,"LPのイメージカラー",imageColor)
    prompt = addCondition(prompt,"",detail)
    
    return prompt

def makepromptForSalesPoint(businessType, target, personasGender, age, imageColor, detail, catchcopy):    
    prompt = "以下の特徴をもつランディングページに記載するセールスポイントを3つ考えてください。"
    addCondition(prompt,"業界", businessType)
    prompt = addCondition(prompt,"ターゲット", target)
    prompt = addCondition(prompt,"ペルソナの性別", personasGender)
    prompt = addCondition(prompt,"ペルソナの年齢", age)
 #   prompt = addCondition(prompt,"LPのイメージカラー", imageColor)
    prompt = addCondition(prompt,"キャッチコピー", catchcopy)
    prompt = addCondition(prompt,"サービス概要", detail)
    prompt += "その際、返答の形式は「1.」「2.」「3.」で並べる形でお願いします。"

    return prompt

def makepromptForLP(referenceUrl,businessType,target,personasGender,age,imageColor,detail,catchcopy,sales_points):    
    prompt = "以下の特徴をもつランディングページのHTMLを作成してください。\n"
    addCondition(prompt,"業界",businessType)
    prompt = addCondition(prompt,"ターゲット",target)
    prompt = addCondition(prompt,"ペルソナの性別",personasGender)
    prompt = addCondition(prompt,"ペルソナの年齢",age)
    prompt = addCondition(prompt,"LPのイメージカラー",imageColor)
    prompt = addCondition(prompt,"キャッチコピー",catchcopy)
    prompt = addCondition(prompt,"サービス概要",detail)
    for index, point in enumerate(sales_points):
        prompt = addCondition(prompt, "セールスポイント" + str(index), point)

    prompt += "キャッチコピー、セールスポイントの内容はページ内で必ず記載し、下記ページを参照しながらレスポンシブデザイン、を充実させてください。\n"
    prompt += referenceUrl
    prompt += "\nセールスポイントの内容は「1.」「2.」「3.」でそれぞれboxに入れて横に並べる形でお願いします。"
    prompt += "回答はHTML部分を返答してください。\n"
    prompt += 'また背景画像として、background-image: url("./hero.png");」を指定するようにしてください。'

    return prompt

def split_by_delimiters(input_string):
    # 正規表現パターンを定義して、「1.」、「2.」、「3.」のような形式をマッチさせる
    pattern = r'\d+\.'  # 区切り文字をキャプチャしない
    # パターンに基づいて分割
    parts = re.split(pattern, input_string)
    # 最初の要素は空文字になるため、削除
    if parts[0] == '':
        parts = parts[1:]
    return parts

@app.route('/')
def form():
    return render_template('index.html')

@app.route('/lp')
def lp():
    return render_template('lp.html')


@app.route('/html/<filename>', methods=['GET'])
def htmlimage(filename):
    return app.send_static_file(filename)

def openai_llm(question, context):
    messages = [
        {"role": "system", "content": question},
        {"role": "user", "content": context},
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=1
    )
    response_message = response.choices[0].message.content
    return response_message

def generate_random_filename(length=10, extension=None):
    # 使用する文字のセットを定義
    characters = string.ascii_letters + string.digits
    # 指定された長さのランダムな文字列を生成
    random_string = ''.join(random.choice(characters) for _ in range(length))
    
    if extension:
        # 拡張子の先頭にドットがない場合は追加
        if not extension.startswith('.'):
            extension = '.' + extension
        return random_string + extension
    else:
        return random_string


@app.route('/createCatchcopy', methods=['POST'])
def submit():
    form_data = request.form.to_dict()
    
    industry = form_data.get('industry')
    target = form_data.get('target')
    gender = form_data.get('gender')
    color = form_data.get('color')
    age = form_data.get('age')
    url = form_data.get('url')
    detail = form_data.get('detail')

    #キャッチコピーを考えさせる
    context = makePromptForCatchcopy(industry,target,gender,age,color,detail)
    catchcopy = openai_llm("あなたはプロのライターです。", context)
    
    print(context)

    #cathcopyをJson形式で返す
    return jsonify({"catchcopy": catchcopy,
                    "prompt": context})

    
@app.route('/submit', methods=['POST'])
def createHtml():    
    form_data = request.form.to_dict()
    
    industry = form_data.get('industry')
    target = form_data.get('target')
    gender = form_data.get('gender')
    color = form_data.get('color')
    age = form_data.get('age')
    url = form_data.get('url')
    detail = form_data.get('detail')
    
    catchcopy = form_data.get('catchcopy')
    
    #セールスポイント作成
    context = makepromptForSalesPoint(industry,target,gender,age,color,detail,catchcopy)
    sales_points_res = openai_llm("あなたはプロのライターです。", context)
    sales_points = split_by_delimiters(sales_points_res)

    #画像生成
    form_data['catchcopy']= catchcopy
    generate_hero_image_DallE(client,form_data)

    #HTMLを生成させる
    context = makepromptForLP(url, industry,target,gender,age,color,detail,catchcopy,sales_points)
    response_message = openai_llm("あなたはプロのwebデザイナーです。", context)

    #return catchcopy + '\n' + response_message

    filename = HTML_FOLDER + generate_random_filename(10,"html")
    with open(filename, 'w', encoding='utf-8') as f:
        html_text = extract_html_content(response_message)
        f.write(html_text)
    
    return redirect(filename)

if __name__ == '__main__':
    app.run(debug=True)


