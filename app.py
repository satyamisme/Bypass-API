import os

from flask import Flask, jsonify, request

from main import loopthread

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


@app.route("/bypass")
def bypass():
    url = request.args.get("url")
    bypass = loopthread(url)
    response_data = {"query": url, "bypassed_url": bypass}
    return jsonify(response_data)


@app.route("/")
def home():
    return "Site Running"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
