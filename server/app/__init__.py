"""
Authors: Eric Pan, Martin Kess
Description: Initiates server (Flask app, mongoDB connection). Also contains website views
"""

import mongoengine
from flask import Flask
from flask import render_template, request, jsonify, redirect
from flask_login import LoginManager
import argparse
from models import * # imports all objects from models
# === Server start-up ===
"""
Run once, this starts mongoDB on default port 27017
Local copy -- multi-server hosting requires more params (passed in **args)
"""

# Setting-up mongoDB connection
alias = 'core'
name = 'zwDBconnect'
mongoengine.register_connection(alias=alias,name=name)
client = mongoengine.connect(name)  # http://docs.mongoengine.org/guide/connecting.html
db = client.zwDatabaseMain # Establishing main db

# Setting-up Flask instance
app = Flask(__name__)
app.config.from_object('config')

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'

login_manager.init_app(app)

# Load CC-CEDICT function definition
def loadCEDICT():
    """
    Loads CEDICT collection into database
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--cedict', default='cedict_ts.u8')

    args = parser.parse_args()

    CEDICT.objects.delete()  # Clear the dictionary first.

    print("Loading CEDICT - this takes a few seconds...")
    with open(args.cedict) as f:
        entry_list = []
        for line in f:
            line = line.strip()
            if len(line) == 0 or line[0] == '#':
                continue

            trad, simp, rest = [tok for tok in line.split(' ', 2)]
            print(trad,simp,rest)
            close_bracket = rest.find(']')  # close bracket on pinyin

            pinyin = rest[1:close_bracket]
            defn = rest[close_bracket+2:]

            entry_list.append(CEDICT(traditional=trad, simplified=simp, pinyin=pinyin, definition=defn))
        print("Loaded. Sending to db...")
        CEDICT.objects.insert(entry_list)
        print("Completed")
    pass

# === Context processor ===
@app.context_processor
def jinja_functions():
    """
    Provides library functions available to rest of templates
    :return: dict of functions to use
    """
    from app.lib.zhongwen import render_chinese_word, render_document
    return dict(
        render_chinese_word=render_chinese_word,
        render_document=render_document
    )

# === Views (newly implemented) ===
@app.route('/') # Default landing page
@app.route('/index')
def landing():
    return render_template('index.html')

"""
Example post data
{
  "URL": "https://zh.wikipedia.org/wiki/Wikipedia:%E9%A6%96%E9%A1%B5",
  "body": "\uff0c\u7f8e\u56fd\u80af\u5854\u57fa\u5dde\u7684\u653f\u6cbb\u5bb6\uff0c\u66fe\u62c5\u4efb\u8be5\u5dde\u7b2c44\u548c49\u4efb\u5dde\u957f\u548c\u8054\u90a6\u53c2\u8bae\u5458\u3002",
  "title": "\u7ef4\u57fa\u767e\u79d1\uff0c\u81ea\u7531\u7684\u767e\u79d1\u5168\u4e66",
  "user": "108978819231638632466"
}
"""

@app.route('/uploadText',methods=['POST'])
def postMethod(): # https://stackoverflow.com/questions/42893826/flask-listen-to-post-request
    # TODO: Have this upload to database (for given user), then redirect to page with the loaded data
    data = request.get_json(force=True)
    newDoc = zwDocument(user_id=data["user"],body=data["body"],context_title=data["title"],context_url=data["URL"])
    newDoc.save()
    return jsonify(data)

# === Main function ===
if __name__ == '__main__':
    loadCEDICT()
    app.run(debug=True,use_reloader=False)