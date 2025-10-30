from flask import Flask, request, jsonify, Response
import requests
from modules import login, retornar_bearer
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

API_KEY = os.getenv("API_KEY")

def require_api_key(func):
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-KEY")
        if key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def validar_bearer():

    url = "https://api.hops.mktlab.app/projects/details?page=1&limit=10&filters.active=true"

    header = {
        "authority": "api.hops.mktlab.app",
        "method": "GET",
        "path": "/projects/details?page=1&limit=10&filters.active=true",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": "Bearer "+retornar_bearer.get_bearer(),
        "content-type": "application/json",
        "origin": "https://hops.mktlab.app",
        "priority": "u=1, i",
        "referer": "https://hops.mktlab.app/",
        "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    }

    response = requests.get(url = url, headers = header)

    if response.status_code != 200:
        print(response.status_code, "Pegando novo Bearer.")
        login.run()

    return retornar_bearer.get_bearer()


@app.route("/hops/extrair_bearer", methods=["GET"])
# @require_api_key
def extrair_bearer():
    try:
        bearer = validar_bearer()
        return jsonify({"broker_bearer": bearer})
    except Exception as e:
        return jsonify({"erro": str(e)}), 400


app.run("0.0.0.0", 5000)