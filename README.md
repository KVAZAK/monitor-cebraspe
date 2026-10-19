# Monitor Cebraspe → Telegram

Monitora CBM_MA_26, PC_MA_26_INVESTIGADOR, PM_MA_26 e SEAP_MA_26_INSPETOR_MONITOR.
Executa na nuvem com GitHub Actions, aproximadamente a cada 30 minutos, nos minutos 17 e 47.
Não precisa de Vercel, Supabase, assinatura de API de IA nem bibliotecas Python externas.

## 1. Criar seu bot

1. Abra https://t.me/BotFather no Telegram (bot oficial).
2. Envie `/newbot`, escolha um nome e um usuário terminado em `bot`.
3. Guarde o token como senha. Não publique no código, em prints ou no chat.
4. Abra o bot criado e envie `/start`. Ele só poderá enviar mensagens privadas após você iniciar a conversa.
5. Instale Python 3.12 ou superior no computador, se necessário, apenas para obter o ID da conversa.
6. Extraia este ZIP, abra um terminal na pasta e execute no Windows:

```powershell
py configurar_telegram.py
```

No macOS/Linux use `python3 configurar_telegram.py`. Cole o token quando solicitado (a digitação fica oculta). O programa consulta o próprio Telegram, mostra os IDs de conversas privadas recentes e não salva o token. Escolha a sua conversa. Se não aparecer, envie uma nova mensagem ao bot e tente novamente. Não reutilize um bot com webhook ou outro programa consumindo mensagens.

## 2. Criar repositório separado no GitHub

Crie um repositório chamado `monitor-cebraspe`, com branch padrão `main`.
Para usar executores padrão sem cobrança de minutos, escolha público. Em repositório privado, acompanhe a franquia da sua conta.
O código e o histórico público de publicações ficarão visíveis. Token e chat ID ficam somente nos Secrets.

Envie o CONTEÚDO da pasta deste ZIP para a raiz do repositório. Não envie o ZIP.
É indispensável que exista o arquivo `.github/workflows/monitor.yml`: pastas iniciadas por ponto podem ficar ocultas.
Pelo navegador, se essa pasta não subir, use **Add file → Create new file**, escreva o caminho completo `.github/workflows/monitor.yml` e cole o conteúdo do arquivo fornecido.

## 3. Cadastrar os Secrets

No repositório: **Settings → Secrets and variables → Actions → New repository secret**.

| Nome exato | Valor |
|---|---|
| TELEGRAM_BOT_TOKEN | Token do BotFather |
| TELEGRAM_CHAT_ID | ID da SUA conversa obtido pelo programa |

Em **Settings → Actions → General**, permita Actions. O workflow solicita `contents: write` para salvar o histórico. Se a política do repositório/organização bloquear, será necessário liberar essa permissão. Proteção de branch que exige PR para cada alteração também pode impedir o salvamento: use este repositório exclusivo para o monitor e confira o passo de persistência.

## 4. Validar e ativar

O envio inicial dos arquivos e alterações em `monitor.py` ou no workflow também iniciam uma execução. Se os Secrets já estiverem cadastrados, a primeira execução registra a referência e envia as confirmações automaticamente. Commits somente do histórico não iniciam outra execução.

1. Abra **Actions → Monitor Cebraspe → Run workflow**.
2. Escolha **dry-run**. Deve mostrar quatro concursos com contagens de publicações válidas. Não envia nem salva nada.
3. Execute **test**. Você deverá receber uma mensagem de teste no Telegram.
4. Execute **monitor**. Na primeira leitura de cada concurso, ele registra as publicações existentes e envia uma confirmação com a contagem. Não envia os documentos antigos individualmente.
5. Confira se o passo **Preservar histórico** ficou verde e se `data/state.json` apareceu no repositório.
6. Após cerca de 30–60 minutos, confira uma execução automática. O agendamento fica habilitado quando o workflow está na branch padrão; não há garantia de pontualidade.

Só considere a instalação concluída após os testes, a persistência do histórico e uma execução agendada bem-sucedida. Ative notificações do GitHub para falhas de Actions e confira-as periodicamente: se Telegram falhar, ele não consegue avisar pelo próprio Telegram.

## Como funciona

- Consulta a API pública usada pelo JavaScript das páginas do Cebraspe, identificada no código do próprio site.
- Compara editais/comunicados (`arquivosEdital`), gabaritos (`arquivosGabarito`) e consultas/links (`aplicativos`).
- Detecta novos links e mudanças no título ou data de um link conhecido.
- Mantém registros removidos no histórico para evitar novo aviso quando um link idêntico reaparece. Remoções não geram aviso.
- PDFs e versões em VLibras são publicações separadas e podem gerar dois avisos.
- Não acessa dados individuais de candidatos, nem faz login nas consultas.
- SEAP acompanha a página inteira, incluindo publicações conjuntas ou específicas de Monitor de Ressocialização.
- Preserva o estado se a fonte estiver indisponível, vazia, inválida ou mudar sua estrutura.
- Só marca a publicação como enviada após a confirmação do Telegram. Uma falha ambígua de rede ou de salvamento pode ocasionar aviso duplicado; não há garantia de entrega exatamente uma vez.
- Cada execução bem-sucedida grava o horário da última consulta no histórico. Não apague `data/state.json`, pois isso reinicia a referência e ignora novidades ocorridas antes da nova primeira leitura.
- O histórico não contém token nem chat ID.

## Limitações e manutenção

O script compara metadados e links; não baixa nem compara o conteúdo dos PDFs. Se o Cebraspe trocar o conteúdo de um PDF mantendo o mesmo nome, título e data, essa mudança não será detectada.
A API não é um contrato público de estabilidade: mudanças do Cebraspe podem exigir manutenção.
Agendamentos do GitHub podem atrasar ou ser descartados em períodos de carga. Em repositórios públicos, o GitHub pode desabilitar agendamentos após 60 dias sem atividade. Confira o painel Actions.
O cancelamento abrupto de uma execução ou a falha de `git push` pode perder o progresso daquela execução e repetir avisos na próxima.
Não há monitor externo de disponibilidade incluso. Para pausar, use **Actions → Monitor Cebraspe → Disable workflow**.

## Verificação na preparação

A API retornou dados dos quatro concursos durante a preparação em 19/10/2026. A leitura foi testada sem credenciais. Telegram e GitHub Actions precisam ser validados na sua conta; nenhum serviço foi ativado por este pacote.

## Referências

- https://core.telegram.org/bots/tutorial
- https://core.telegram.org/bots/api
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://www.cebraspe.org.br/concursos/CBM_MA_26
- https://www.cebraspe.org.br/concursos/PC_MA_26_INVESTIGADOR
- https://www.cebraspe.org.br/concursos/PM_MA_26
- https://www.cebraspe.org.br/concursos/SEAP_MA_26_INSPETOR_MONITOR
