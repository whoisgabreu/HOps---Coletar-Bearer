import websocket
import json
import time

import requests
from threading import Thread
import subprocess

# def worker():

#     subprocess.run('"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222 --user-data-dir="C:\ChromeDebug" --remote-allow-origins=*', check = True)

# t = Thread(target = worker, daemon = True)
# t.start()



socket_id = None

base_url  = "31.97.27.195:9223"

r = requests.get(f"http://{base_url}/json")
json_str = r.content.decode("utf-8-sig")
pages = json.loads(json_str)

for page in pages:
    if page.get("title") == "HOps":
        socket_id = page.get("id")


# 🔧 Cole aqui o WebSocket da aba Chrome que você quer controlar:
CDP_URL = f"ws://{base_url}/devtools/page/{socket_id}"

# Abre a conexão WebSocket com o Chrome
ws = websocket.create_connection(CDP_URL)

# Função utilitária para enviar comandos CDP
def cdp_send(method, params=None, _id=[1]):
    msg = {
        "id": _id[0],
        "method": method,
        "params": params or {}
    }
    _id[0] += 1
    ws.send(json.dumps(msg))
    response = ws.recv()
    print(f"[{method}] => {response}")
    return response

# 1️⃣ Habilita páginas
cdp_send("Page.enable")

# 2️⃣ Navega até a URL desejada
time.sleep(2)

# 3️⃣ Executa JS para modificar o DOM (inserir input e botão)
def cdp_send_and_wait(ws, method, params=None, _id=[1], timeout=5):
    msg = {"id": _id[0], "method": method, "params": params or {}}
    current_id = _id[0]
    _id[0] += 1
    ws.send(json.dumps(msg))

    # aguarda respostas até achar a que tem o mesmo id
    start = time.time()
    while True:
        if time.time() - start > timeout:
            raise TimeoutError("Timeout aguardando resposta CDP")
        raw = ws.recv()
        data = json.loads(raw)
        # resposta direta com mesmo id
        if isinstance(data, dict) and data.get("id") == current_id:
            return data
        # às vezes chegam eventos (sem id) — ignoramos
        # loop continua até achar a resposta com o id

# Exemplo seguro: monta um dicionário com os cookies e retorna o valor do cookie "__session"
expr = r"""
(function(){
  const d = {};
  document.cookie.split(';').forEach(s=>{
    const parts = s.split('=');
    const k = parts.shift().trim();
    const v = parts.join('=').trim();
    d[k] = v;
  });
  // retorna o valor em JSON (garante serialização segura)
  return JSON.stringify(d['__session'] || null);
})()
"""

# Chama Runtime.evaluate pedindo returnByValue para ter o valor diretamente
resp = cdp_send_and_wait(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True})

cdp_send("Runtime.evaluate", {
    "expression": """
        let dicionario = {}
        for (string of document.cookie.split(";")) {
            dicionario[string.split("=")[0]] = string.split("=")[1]
        }

        console.log(dicionario[' __session'])
    """
})

# Agora parseia o resultado
# Estrutura esperada: { "id": N, "result": { "result": { "type": "string", "value": "\"valor\""} } }
result_field = resp.get("result", {}).get("result", {})

value = None
if "value" in result_field:
    # value já contém a string retornada pela expressão (no caso é JSON string)
    # desserializa para obter o valor real
    try:
        value = json.loads(result_field["value"])
    except Exception:
        value = result_field["value"]
elif "objectId" in result_field:
    # se o CDP retornou um objectId, podemos chamar Runtime.getProperties ou Runtime.callFunctionOn
    object_id = result_field["objectId"]
    props = cdp_send_and_wait(ws, "Runtime.getProperties", {"objectId": object_id, "ownProperties": True})
    value = props  # processar conforme necessidade

print("Bearer "+value)

time.sleep(5)
ws.close()
print("✅ Finalizado com sucesso.")
