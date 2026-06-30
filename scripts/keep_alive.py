from playwright.sync_api import sync_playwright
import sys

URL = "https://kaggle-data-cx-cs.streamlit.app/"

def acordar_app():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(5000)

            botao_acordar = page.get_by_role("button", name="Yes, get this app back up!")

            if botao_acordar.count() > 0:
                print(f"App estava dormindo. Clicando para acordar: {URL}")
                botao_acordar.click()
                page.wait_for_timeout(60000)
                print("App acordado com sucesso.")
            else:
                print(f"App já estava ativo: {URL}")

        except Exception as e:
            print(f"Erro ao acessar o app: {e}")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    acordar_app()
