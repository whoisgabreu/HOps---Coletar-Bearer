import json

def get_bearer():
    bearer = None
    with open(r"modules/auth.json", "r", encoding = "utf-8-sig") as f:
        cookies = json.load(f)

    for cookie in cookies["cookies"]:
        if cookie["name"] == "__session":
            bearer =  cookie["value"]
    
    if bearer:
        return bearer

    return None
