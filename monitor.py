"""Monitor Cebraspe: Python 3.12+, somente biblioteca padrão."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlsplit

CONCURSOS = {
    'CBM_MA_26': 'CBMMA',
    'PC_MA_26_INVESTIGADOR': 'PC MA — Investigador',
    'PM_MA_26': 'PMMA',
    'SEAP_MA_26_INSPETOR_MONITOR': 'SEAP MA — Inspetor/Monitor',
}
API = 'https://apis.cebraspe.org.br/cebraspe/eventos/'
STATE = Path(os.environ.get('STATE_FILE', 'data/state.json'))

def request_json(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(url, data=data, headers={
        'User-Agent': 'MonitorConcursos/1.0', 'Accept': 'application/json',
        'Content-Type': 'application/json'})
    with urlopen(req, timeout=30) as response:
        return json.load(response)

def fetch(code):
    for attempt in range(3):
        try:
            return request_json(API + code)
        except Exception:
            if attempt == 2:
                raise RuntimeError('Fonte indisponível após 3 tentativas') from None
            time.sleep(2 ** attempt)

def publications(data, code):
    if not isinstance(data, dict) or data.get('eventoURL', '').upper() != code:
        raise ValueError('Resposta não corresponde ao concurso')
    if not isinstance(data.get('arquivosEdital'), list):
        raise ValueError('Estrutura da fonte mudou')
    items = {}
    for section in ('arquivosEdital', 'arquivosGabarito', 'aplicativos'):
        rows = data.get(section) or []
        if not isinstance(rows, list):
            raise ValueError('Seção inválida')
        for row in rows:
            if section == 'aplicativos':
                title, url, date = row['nomeAplicativo'], row['link'], row.get('dataInicio', '')
            else:
                title, date = row['descricaoArquivo'], row.get('dataArquivoObj') or row.get('dataArquivo', '')
                if row.get('isGuid'):
                    base = 'https://cdn.cebraspe.org.br/'
                elif row.get('tipoExtensaoArquivo') == '_explorer':
                    base = f'http://www.cespe.unb.br/concursos/{code}/arquivos/'
                else:
                    base = f'https://cdn.cebraspe.org.br/concursos/{code}/arquivos/'
                url = urljoin(base, row['nomeArquivo'])
            if not title or urlsplit(url).scheme not in ('http', 'https'):
                raise ValueError('Publicação inválida')
            item = {'section': section, 'title': ' '.join(title.split()), 'url': url, 'date': date}
            identity = hashlib.sha256(f'{section}|{url}'.encode()).hexdigest()
            items[identity] = item
    if not items:
        raise ValueError('Lista vazia: histórico preservado')
    return items

def changes(previous, current):
    return [(key, item) for key, item in current.items() if previous.get(key) != item]

def save(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(STATE)

def send(text):
    token, chat = os.environ.get('TELEGRAM_BOT_TOKEN'), os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat:
        raise RuntimeError('Configure TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID')
    try:
        result = request_json(f'https://api.telegram.org/bot{token}/sendMessage', {
            'chat_id': chat, 'text': text, 'link_preview_options': {'is_disabled': True}})
        if not result.get('ok'):
            raise RuntimeError()
    except Exception:
        # Não imprimir exceções HTTP: a URL contém o token.
        raise RuntimeError('Falha no Telegram; confira os Secrets, /start e conexão') from None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Lê a fonte sem enviar ou salvar')
    parser.add_argument('--test-message', action='store_true')
    args = parser.parse_args()
    if args.test_message:
        send('Teste do monitor Cebraspe: Telegram conectado. Este teste não ativa o monitor.')
        return 0
    if not args.dry_run and not all(os.environ.get(k) for k in ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID')):
        raise RuntimeError('Cadastre os dois Secrets antes de executar')
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {'version': 1, 'contests': {}}
    if state.get('version') != 1 or not isinstance(state.get('contests'), dict):
        raise ValueError('Estado inválido; não apagar o histórico')
    failures = 0
    for code, name in CONCURSOS.items():
        try:
            current = publications(fetch(code), code)
            old = state['contests'].get(code)
            if args.dry_run:
                print(f'{code}: {len(current)} publicações válidas; ' + ('primeira leitura' if old is None else f'{len(changes(old["seen"], current))} alterações'))
                continue
            if old is None:
                send(f'Monitor iniciado: {name}\n{len(current)} publicações registradas como referência.\nAvisarei sobre novidades após esta leitura.\nhttps://www.cebraspe.org.br/concursos/{code}')
                old = {'seen': current}
                state['contests'][code] = old
                save(state)
            else:
                for key, item in changes(old['seen'], current):
                    kind = 'PUBLICAÇÃO ALTERADA' if key in old['seen'] else 'NOVA PUBLICAÇÃO'
                    message = f'{kind} — {name}\n{item["title"][:1800]}\nData na fonte: {item["date"]}\n{item["url"]}\nPágina: https://www.cebraspe.org.br/concursos/{code}'
                    if len(message.encode('utf-16-le')) // 2 > 4000:
                        message = f'{kind} — {name}\n{item["title"][:1000]}\nhttps://www.cebraspe.org.br/concursos/{code}'
                    send(message)
                    old['seen'][key] = item
                    save(state)
                    time.sleep(1.1)
            old['last_success_utc'] = datetime.now(timezone.utc).isoformat()
            save(state)
            print(f'{code}: OK, {len(current)} publicações')
        except Exception as exc:
            failures += 1
            # Somente mensagens controladas, sem URLs de credenciais.
            print(f'{code}: falha ({type(exc).__name__}); histórico preservado. Verifique a fonte e a configuração.')
    return 1 if failures else 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as exc:
        print(str(exc))
        raise SystemExit(1)
