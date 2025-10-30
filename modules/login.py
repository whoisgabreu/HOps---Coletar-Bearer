from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
import os
import random
from .check_maintance import check_maintance

load_dotenv()
manutencao = os.getenv("MANUTENCAO")
login = os.getenv("LOGIN")
senha = os.getenv("SENHA")

def run():
    # Diretório onde o perfil será salvo
    user_data_dir = os.path.join(os.path.dirname(__file__), "user_data")

    # User agents realistas (rotaciona entre eles)
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    ]

    with sync_playwright() as p:
        # Contexto persistente com configurações anti-detecção
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False if manutencao == "true" else True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-infobars",
                "--disable-gpu",
                "--window-size=1920,1080",
                "--start-maximized",
                "--disable-software-rasterizer",
                "--disable-extensions",
            ],
            # Configurações extras para parecer mais humano
            viewport={'width': 1920, 'height': 1080},
            user_agent=random.choice(user_agents),
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            color_scheme='light',
            has_touch=False,
            is_mobile=False,
            device_scale_factor=1,
            java_script_enabled=True,
            bypass_csp=True,
            ignore_https_errors=True,
        )

        try:
            page = context.pages[0] if context.pages else context.new_page()

            # Script para remover marcadores de automação
            page.add_init_script("""
                // Remove webdriver flag
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Mock chrome object
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en-US', 'en']
                });
            """)

            print("🚀 Iniciando navegação...")
            
            # Acessa a página de login com timeout maior
            page.goto("https://hops.mktlab.app/signin", wait_until="networkidle", timeout=60000)
            
            # Delay humano
            page.wait_for_timeout(random.randint(2000, 4000))

            # Checa manutenção
            check_maintance()

            # Tenta clicar no "Continuar com o Google"
            try:
                print("🔍 Procurando botão 'Continuar com o Google'...")
                page.locator("span", has_text="Continuar com o Google").click(timeout=10000)
                print("✅ Clicou em 'Continuar com o Google'")
                page.wait_for_timeout(random.randint(2000, 3000))
            except PlaywrightTimeoutError:
                print("⚠️ Botão 'Continuar com o Google' não encontrado - pode já estar logado")

            # Se ainda estiver na página de signin, realizar o login automático
            if "hops.mktlab.app/signin" in page.url or "accounts.google.com" in page.url:
                try:
                    print("📝 Iniciando processo de login Google...")
                    
                    # Aguarda o campo de email aparecer
                    page.wait_for_selector("#identifierId", timeout=15000)
                    
                    # Simula digitação humana
                    page.fill("#identifierId", "", timeout=5000)  # Limpa campo
                    page.wait_for_timeout(random.randint(500, 1000))
                    
                    # Digita o email com delay
                    for char in login:
                        page.type("#identifierId", char, delay=random.randint(50, 150))
                    
                    page.wait_for_timeout(random.randint(1000, 2000))
                    
                    # Clica em Avançar
                    page.locator("span", has_text="Avançar").click()
                    print("✅ Email preenchido, avançando...")

                    # Espera campo de senha aparecer
                    page.wait_for_selector("input[type=password]", timeout=20000)
                    page.wait_for_timeout(random.randint(1500, 2500))
                    
                    # Digita a senha com delay
                    for char in senha:
                        page.type("input[type=password]", char, delay=random.randint(50, 150))
                    
                    page.wait_for_timeout(random.randint(1000, 2000))
                    
                    # Clica em Avançar
                    page.locator("span", has_text="Avançar").click()
                    print("✅ Senha preenchida, fazendo login...")
                    
                except PlaywrightTimeoutError as e:
                    print(f"⚠️ Timeout durante o fluxo de login: {e}")
                    # Tira screenshot para debug
                    page.screenshot(path=os.path.join(os.path.dirname(__file__), "erro_login.png"))
                    print("📸 Screenshot salvo em erro_login.png")

            # Espera redirecionamento para a área logada
            try:
                print("⏳ Aguardando redirecionamento para área logada...")
                page.wait_for_url("**/projects/list?active=true", timeout=45000)
                print("✅ Acesso realizado com sucesso!")
            except PlaywrightTimeoutError:
                print(f"⚠️ Não redirecionou para /projects/list?active=true. URL atual: {page.url}")
                # Tira screenshot para debug
                page.screenshot(path=os.path.join(os.path.dirname(__file__), "erro_redirect.png"))
                print("📸 Screenshot salvo em erro_redirect.png")

            # Salva o estado da sessão
            try:
                auth_path = os.path.join(os.path.dirname(__file__), "auth.json")
                context.storage_state(path=auth_path)
                print(f"✅ Sessão salva em {auth_path}")
            except Exception as e:
                print(f"⚠️ Falha ao salvar auth.json: {e}")

            # Delay antes de fechar (comportamento humano)
            page.wait_for_timeout(random.randint(2000, 4000))

        except Exception as e:
            print(f"❌ Erro durante execução: {e}")
            # Tira screenshot do erro
            try:
                if 'page' in locals():
                    page.screenshot(path=os.path.join(os.path.dirname(__file__), "erro_geral.png"))
                    print("📸 Screenshot do erro salvo em erro_geral.png")
            except:
                pass
            raise

        finally:
            # Fecha o contexto persistente
            context.close()
            print("👋 Contexto fechado")

# if __name__ == "__main__":
#     run()
