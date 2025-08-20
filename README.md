# Alpes Site Monitor · Etapa 2

Solução que verifica periodicamente se os sites estão online e notifica via webhook do Discord no canal `#notificações`.
A aplicação **envia mensagens quando está OK** e quando encontra **erros**.

> Nota: como não há acesso ao servidor da etapa (pasta `/home/sites/vhosts`), a lista de domínios é mantida no arquivo `configs/domains.yml`. Em produção, a descoberta pode ser automatizada lendo os vhosts.

---

## Como funciona

Fluxo por domínio:

1. **DNS**
   * Resolve registros A e AAAA.
   * Se não houver IP, registra: “DNS não retornou A/AAAA”.
2. **Cloudflare**
   * Detecta se os **NS** são `*.cloudflare.com` e se os IPs A ou AAAA pertencem às faixas públicas da Cloudflare.
   * Se usar Cloudflare nos NS, mas o IP não for Cloudflare, marca “DNS Only expondo origin”.
3. **Apontamento para IPs esperados**
   * Se não estiver atrás da Cloudflare, compara A e AAAA com a lista oficial `EXPECTED_IPS` do `.env`.
   * Se nenhum IP bater, registra: “A/AAAA diferente dos IPs esperados”.
4. **HTTP**
   * Faz requisição HTTPS com follow redirect e timeout.
   * Considera OK se o status for 2xx ou 3xx, o corpo tiver tamanho mínimo e não contiver marcadores comuns de erro.
5. **Notificação**
   * Envia embed ao Discord com: Domínio, IPs, NS, status Cloudflare, status HTTP e problemas encontrados.
   * Envia **OK** também, para dar visibilidade contínua.

---

## Requisitos

* Python 3.9 ou superior
* Windows, Linux ou macOS
* Acesso à internet para DNS e HTTP

---

## Instalação

```powershell
# clonagem
git clone https://github.com/hugogalli/alpes-site-monitor.git
cd alpes-site-monitor

# ambiente virtual (Windows)
py -3.9 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate

# dependências
pip install -r requirements.txt
```

Linux ou macOS:

```bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Configuração

Crie o arquivo `.env` na raiz. Há um `.env.example` para referência.

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/SEU_ID/SEU_TOKEN
EXPECTED_IPS=LISTA_IPS
MIN_BODY_BYTES=1024
REQUEST_TIMEOUT_SECONDS=10
```

Edite `configs/domains.yml` para listar os domínios:

```yaml
domains:
  # Exemplo por trás da Cloudflare (apenas monitorar HTTP e DNS)
  - host: www.cloudflare.com
    skip_ip_check: true

  # Exemplo simples
  - host: example.com
    skip_ip_check: true

  # Simulando os hosts do grupo carbel para teste
  - host: grupocarbel.com.br
    skip_ip_check: false
  - host: carbel.com.br
    skip_ip_check: false
  - host: carbelbyd.com.br
    skip_ip_check: false
  - host: carbelkorea.com.br
    skip_ip_check: false
```

Opções por domínio:

* `host`: nome do domínio
* `skip_ip_check`: se verdadeiro, não compara A e AAAA com `EXPECTED_IPS`
* `expected_ips`: lista de IPs esperados específicos para o domínio  
  Se omitido, usa o valor global de `EXPECTED_IPS`

---

## Execução

Rodada única:

```bash
python -m monitor
```

Loop interno para testes locais:

```bash
python -m monitor --interval 300
```

> Observação: para produção, é recomendável usar o agendador do sistema operacional para chamar a aplicação uma vez por intervalo e encerrar. Exemplo Task Scheduler no Windows ou systemd timer no Linux. Durante o desenvolvimento rodei no Windows e mantive a opção de loop para simplificar a demonstração.

---

## Envio ao Discord

Formato enviado:

-- IMAGENS

---

## Respostas às perguntas da etapa

**O domínio está apontando corretamente para nossos servidores?**  
Sim. Quando o domínio não está atrás da Cloudflare, os registros A e AAAA resolvidos são comparados com os IPs oficiais informados no `.env`:
```
54.243.82.193
3.89.13.179
44.199.57.56
```
Se pelo menos um IP bater, consideramos apontando corretamente. Caso contrário, geramos alerta com os IPs observados.

**O domínio está funcionando corretamente?**  
Validamos duas frentes:
* **DNS** resolvendo para A e AAAA. Se não houver IP, registramos “DNS não retornou A/AAAA”.
* **HTTP** com status 2xx ou 3xx, corpo acima do tamanho mínimo e sem marcadores comuns de erro. Em caso de falha, especificamos se foi status inválido, resposta pequena, marcador de erro no HTML ou exceção de conexão.

**O domínio não está congelado ou com erro no carregamento?**  
Heurística aplicada:
* **Tamanho mínimo** do corpo da resposta (`MIN_BODY_BYTES`) para evitar páginas vazias ou congeladas.
* **Marcadores comuns de erro** no HTML, por exemplo: “error 5xx”, “service unavailable”, “bad gateway”, “account suspended”.  
Se detectado, o problema aparece no embed.

**Se o cliente usa Cloudflare, como detectar se o domínio não está apontando diretamente?**  
* Checamos se os **NS** são de Cloudflare.  
* Validamos se os IPs A e AAAA estão nas **faixas públicas** da Cloudflare.  
* Caso os NS sejam Cloudflare e os IPs não sejam, classificamos como **DNS Only expondo origin**, isto é, o domínio está apontando direto para o origin em vez de passar pelo proxy.

---

## Boas práticas e observações

* Manter `EXPECTED_IPS` atualizado, pois define o que é “apontando corretamente” sem Cloudflare.
* Em produção, preferir agendador do SO para execução periódica sem processos residentes.
* Com acesso ao servidor, é possível estender para descobrir domínios lendo `/home/sites/vhosts` (Apache e Nginx) e popular automaticamente `domains.yml`.
* O envio de mensagens OK está habilitado para visibilidade contínua. Caso a equipe prefira, isso pode ser tornado configurável.

---

## Troubleshooting rápido

* **Webhook não recebe mensagens**  
  Verifique a URL no `.env`. Teste com um POST simples.
* **Variáveis do `.env` não carregam**  
  Salve em UTF-8 sem BOM. O projeto tenta contornar, mas é melhor ajustar o arquivo.
* **DNS falha apenas para um host**  
  Confirme com `nslookup` para validar se é um problema real de resolução.
* **Muito volume de OK**  
  A política de envio pode ser alterada no código para enviar apenas erros ou mudanças de estado, se desejado.

---

## Scripts úteis

Executar uma vez:

```bash
python -m monitor
```

Executar em loop para testes:

```bash
python -m monitor --interval 300
```

Instalar ou atualizar dependências:

```bash
pip install -r requirements.txt
```
