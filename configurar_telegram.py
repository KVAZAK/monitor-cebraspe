"""Execute localmente; token digitado sem exibição, nunca salvo."""
from getpass import getpass
from monitor import request_json

token = getpass('Token fornecido pelo BotFather (entrada oculta): ').strip()
try:
    result = request_json(f'https://api.telegram.org/bot{token}/getUpdates')
    chats = {}
    for update in result.get('result', []):
        chat = update.get('message', {}).get('chat', {})
        if chat.get('type') == 'private':
            chats[chat['id']] = chat.get('first_name', '')
    if not chats:
        print('Envie /start ao seu novo bot e execute novamente. Use um bot exclusivo, sem webhook.')
    for chat_id, name in chats.items():
        print(f'Conversa: {name} | TELEGRAM_CHAT_ID: {chat_id}')
    print('Selecione somente a sua conversa; copie o ID para o Secret no GitHub.')
except Exception:
    print('Falha ao consultar Telegram. Confira token, conexão e se há webhook neste bot. Token não exibido.')
