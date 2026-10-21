

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote
from html import escape
import os
import hmac
import base64


from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
from html import escape
import os
import hmac
import base64

# ==========================================
# CONFIGURAÇÕES DO SERVIDOR
# ==========================================

PASTA = Path.home() / "mini-servidor" / "arquivos"
HOST = "0.0.0.0"
PORTA = 8000

USUARIO = os.environ.get("SERVIDOR_USUARIO")
SENHA = os.environ.get("SERVIDOR_SENHA")


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def formatar_tamanho(bytes_total):
    if bytes_total < 1024:
        return f"{bytes_total} B"

    if bytes_total < 1024 ** 2:
        return f"{bytes_total / 1024:.1f} KB"

    if bytes_total < 1024 ** 3:
        return f"{bytes_total / (1024 ** 2):.1f} MB"

    return f"{bytes_total / (1024 ** 3):.1f} GB"


# ==========================================
# CLASSE DO SERVIDOR
# ==========================================

class ServidorArquivos(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            directory=str(PASTA),
            **kwargs
        )

    # --------------------------------------
    # VERIFICA USUÁRIO E SENHA
    # --------------------------------------

    def verificar_acesso(self):
        autenticacao = self.headers.get("Authorization", "")
        
        if not USUARIO or not SENHA:
            self.send_error(
                503,
                "Servidor sem credenciais configuradas."
            )
            return False

        esperado = "Basic " + base64.b64encode(
            f"{USUARIO}:{SENHA}".encode("utf-8")
        ).decode("ascii")

        if hmac.compare_digest(autenticacao, esperado):
            return True

        self.send_response(401)
        self.send_header(
            "WWW-Authenticate",
            'Basic realm="Servidor de arquivos"'
        )
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def do_HEAD(self):
        if not self.verificar_acesso():
            return

        return super().do_HEAD()

    # --------------------------------------
    # PÁGINA PRINCIPAL E DOWNLOADS
    # --------------------------------------

    def do_GET(self):
        if not self.verificar_acesso():
            return

        caminho_url = unquote(urlsplit(self.path).path)

        if caminho_url != "/":
            return super().do_GET()

        try:
            arquivos = sorted(
                (
                    item for item in PASTA.iterdir()
                    if item.is_file()
                ),
                key=lambda item: item.name.lower()
            )
        except OSError:
            self.send_error(500, "Não foi possível listar os arquivos.")
            return

        cartoes = ""

        for arquivo in arquivos:
            nome = escape(arquivo.name)
            link = quote(arquivo.name, safe="")
            tamanho = formatar_tamanho(arquivo.stat().st_size)

            cartoes += f"""
            <article class="arquivo"
                     data-nome="{escape(arquivo.name.lower(), quote=True)}">
                <div class="icone">📄</div>

                <div class="detalhes">
                    <strong>{nome}</strong>
                    <span>{tamanho}</span>
                </div>

                <a class="baixar" href="/{link}">
                    Baixar ↓
                </a>
            </article>
            """

        if not cartoes:
            cartoes = """
            <p class="vazio">
                Nenhum arquivo disponível ainda.
                Adicione arquivos à pasta compartilhada.
            </p>
            """

        pagina = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Meu Servidor | Arquivos</title>

<style>
* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: #f1f5f9;
    color: #172033;
    font-family: Arial, sans-serif;
}}

header {{
    background: #111c35;
    color: white;
    padding: 28px max(20px, calc((100% - 960px) / 2));
}}

header h1 {{
    margin: 0 0 8px;
    font-size: 26px;
}}

header p {{
    margin: 0;
    color: #cbd5e1;
}}

main {{
    max-width: 960px;
    margin: 32px auto;
    padding: 0 20px;
}}

.resumo {{
    background: white;
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 22px;
    box-shadow: 0 4px 18px #1720330b;
}}

.numero {{
    font-size: 30px;
    font-weight: bold;
    color: #2563eb;
}}

input {{
    width: 100%;
    padding: 13px;
    margin-top: 18px;
    border: 1px solid #d8deea;
    border-radius: 9px;
    font-size: 16px;
}}

h2 {{
    font-size: 19px;
    margin: 26px 0 14px;
}}

.arquivo {{
    display: flex;
    align-items: center;
    gap: 14px;
    background: white;
    padding: 16px;
    margin-bottom: 10px;
    border-radius: 12px;
    border: 1px solid #e3e8f1;
}}

.icone {{
    font-size: 27px;
}}

.detalhes {{
    flex: 1;
    min-width: 0;
}}

.detalhes strong {{
    display: block;
    overflow-wrap: anywhere;
}}

.detalhes span {{
    display: block;
    color: #64748b;
    font-size: 13px;
    margin-top: 5px;
}}

.baixar {{
    background: #2563eb;
    color: white;
    text-decoration: none;
    padding: 10px 13px;
    border-radius: 8px;
    white-space: nowrap;
}}

.baixar:hover {{
    background: #1d4ed8;
}}

.vazio {{
    background: white;
    padding: 20px;
    border-radius: 12px;
}}

footer {{
    text-align: center;
    color: #64748b;
    padding: 30px;
    font-size: 13px;
}}

[hidden] {{
    display: none !important;
}}

@media (max-width: 480px) {{
    .arquivo {{
        gap: 9px;
        padding: 12px;
    }}

    .baixar {{
        padding: 9px;
        font-size: 13px;
    }}
}}
</style>
</head>

<body>

<header>
    <h1>📁 Meu Servidor</h1>
    <p>Central de arquivos da minha rede local</p>
</header>

<main>

    <section class="resumo">
        <div>Arquivos disponíveis</div>
        <div class="numero">{len(arquivos)}</div>

        <input
            id="busca"
            type="search"
            placeholder="🔎 Pesquisar arquivos..."
            aria-label="Pesquisar arquivos"
        >
    </section>

    <h2>Seus arquivos</h2>

    <section id="lista">
        {cartoes}
    </section>

</main>

<footer>
    Servidor desenvolvido com Python · Uso na rede local
</footer>

<script>
const busca = document.getElementById("busca");

busca.addEventListener("input", () => {{
    const termo = busca.value.toLowerCase();

    document.querySelectorAll(".arquivo").forEach(item => {{
        item.hidden = !item.dataset.nome.includes(termo);
    }});
}});
</script>

</body>
</html>"""

        conteudo = pagina.encode("utf-8")

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(conteudo))
        )
        self.end_headers()
        self.wfile.write(conteudo)


# ==========================================
# INICIALIZAÇÃO DO SERVIDOR
# ==========================================

if __name__ == "__main__":

    if not PASTA.is_dir():
        raise SystemExit(
            f"Pasta não encontrada: {PASTA}"
        )

    if not USUARIO or not SENHA:
        raise SystemExit(
            "Configure SERVIDOR_USUARIO e SERVIDOR_SENHA antes de iniciar."
        )

    servidor = ThreadingHTTPServer(
        (HOST, PORTA),
        ServidorArquivos
    )

    print("=" * 45)
    print("       MINI SERVIDOR DE ARQUIVOS")
    print("=" * 45)
    print(f"Porta: {PORTA}")
    print(f"Pasta compartilhada: {PASTA}")
    print(f"Usuário configurado: {USUARIO}")
    print(f"Acesso local: http://127.0.0.1:{PORTA}")
    print("Pressione Ctrl+C para encerrar.")
    print("=" * 45)

    try:
        servidor.serve_forever()

    except KeyboardInterrupt:
        print("\nEncerrando o servidor...")

    finally:
        servidor.server_close()
        print("Servidor encerrado.")
