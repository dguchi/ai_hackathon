# app.py
import random
import string

from flask import Flask, request, redirect ,render_template
from openai import OpenAI

HTML_FOLDER = './html/'

# キーは環境変数に設定
client = OpenAI(
    #    api_key=apikey
)

app = Flask(__name__,static_folder='html')

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
        temperature=0
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


@app.route('/submit', methods=['POST'])
def submit():
    industry = request.form['industry']
    target = request.form['target']
    gender = request.form['gender']
    color = request.form['color']
    age = request.form['age']
    url = request.form['url']
    detail = ''
    
    #キャッチコピーを考えさせる
    context = makePromptForCatchcopy(industry,target,gender,age,color,detail)
    catchcopy = openai_llm("あなたはプロのwebデザイナーです。", context) 

    #HTMLを生成させる
    context = makepromptForLP(url, industry,target,gender,age,color,detail,catchcopy)
    response_message = openai_llm(question, context)

    filename = HTML_FOLDER + generate_random_filename(10,"html")
    with open(filename, 'w') as f:
        f.write(response_message)
    
    return redirect(filename)

if __name__ == '__main__':
    app.run(debug=True)


def makePromptForCatchcopy(businessType,target,personasGender,age,imageColor,detail):
    prompt = "以下の特徴をもつビジネスのキャッチコピーを考えてください。"
    addCondition(prompt,"業界",businessType)
    prompt = addCondition(prompt,"ターゲット",target)
    prompt = addCondition(prompt,"ペルソナの性別",personasGender)
    prompt = addCondition(prompt,"ペルソナの年齢",age)
    prompt = addCondition(prompt,"LPのイメージカラー",imageColor)
    prompt = addCondition(prompt,"",detail)
    
    return prompt


def makepromptForLP(referenceUrl,businessType,target,personasGender,age,imageColor,detail,catchcopy):    
    prompt = "以下の特徴をもつランディングページのHTMLを作成してください。\n" + "その際、以下のようなページを参照してください。" + referenceUrl
    addCondition(prompt,"業界",businessType)
    prompt = addCondition(prompt,"ターゲット",target)
    prompt = addCondition(prompt,"ペルソナの性別",personasGender)
    prompt = addCondition(prompt,"ペルソナの年齢",age)
    prompt = addCondition(prompt,"LPのイメージカラー",imageColor)
    prompt = addCondition(prompt,catchcopy)
    prompt = addCondition(prompt,"",detail)
        
    return prompt


def addCondition(prompt,conditonType,condition):
    if(len(condition) != 0):
        prompt += "\n" + "・"
        if (len(conditonType) != 0):
            prompt += str(conditonType) + "は" + str(condition)
        else:
            prompt += condition    
    return prompt