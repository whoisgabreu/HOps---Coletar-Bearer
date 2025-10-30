from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
import os
from .check_maintance import check_maintance

load_dotenv()
manutencao = os.getenv("MANUTENCAO")
login = os.getenv("LOGIN")
senha = os.getenv("SENHA")

def run():
    # diretório onde o perfil (cookies, localStorage, cache, etc.) será salvo
    user_data_dir = os.path.join(os.path.dirname(__file__), "user_data")  # pode ser alterado

    with sync_playwright() as p:
        # cria um contexto persistente — na primeira execução faça o login manual/automático,
        # nas próximas execuções ele já estará logado.
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            # headless=False if manutencao == "true" else True,
            headless=False,
            channel="chrome",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-infobars",
                "--window-size=1280,800",
                "--start-maximized",
            ],
        )

        try:
            page = context.pages[0] if context.pages else context.new_page()

            # Acessa a página de login
            page.goto("https://hops.mktlab.app/signin")

            # Checa manutenção (sua função)
            check_maintance()

            # Tenta clicar no "Continuar com o Google"
            # (caso o botão já tenha sido aplicado anteriormente, isso não fará login novamente)
            try:
                page.locator("span", has_text="Continuar com o Google").click(timeout=5000)
            except PlaywrightTimeoutError:
                # botão não encontrado — segue adiante (talvez já esteja logado)
                pass

            # Se ainda estiver na página de signin, realizar o login automático
            if "hops.mktlab.app/signin" in page.url:
                # Preenche e faz login via Google
                try:
                    # Preenche e avança no email
                    page.fill("#identifierId", login)
                    page.locator("span", has_text="Avançar").click()

                    # Espera campo de senha aparecer
                    page.wait_for_selector("input[type=password]", timeout=15000)
                    page.fill("input[type=password]", senha)
                    page.locator("span", has_text="Avançar").click()
                except PlaywrightTimeoutError:
                    print("⚠️ Timeout durante o fluxo de login — talvez o fluxo tenha mudado ou exigir verificação adicional.")

            # Espera redirecionamento para a área logada (ajuste o pattern se necessário)
            try:
                page.wait_for_url("**/projects/list?active=true", timeout=30000)
                print("✅ Acessou área logada.")
            except PlaywrightTimeoutError:
                print("⚠️ Não redirecionou para /projects/list?active=true dentro do tempo esperado. URL atual:", page.url)

            # Opcional: exporta storage_state (cookies + localStorage) para um arquivo JSON,
            # útil se quiser carregar a sessão sem usar o user_data_dir em outro lugar.
            try:
                context.storage_state(path=os.path.join(os.path.dirname(__file__), "auth.json"))
                print("✅ Sessão salva em auth.json")
            except Exception as e:
                print("⚠️ Falha ao salvar auth.json:", e)

        finally:
            # fecha o contexto persistente
            context.close()

# if __name__ == "__main__":
#     run()


