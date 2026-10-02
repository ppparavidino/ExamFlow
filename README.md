ExamFlow

Aplicação web para apoiar o controle de exames periódicos de funcionários. O sistema importa cadastros a partir de relatórios PDF do TransNet, mostra exames pendentes, permite registrar agendamentos e gera documentos de convocação e relatórios.

> **Dados pessoais:** os PDFs importados podem conter nomes, matrículas e telefones de funcionários. Use apenas dados autorizados e não versione relatórios reais no Git.

## Funcionalidades

- Importação e prévia de alterações de funcionários a partir de PDF.
- Consulta de exames pendentes e agendados.
- Registro, confirmação, cancelamento e atualização de observações de agendamentos.
- Geração de PDF de convocação e relatório dos exames agendados.
- Criação de links de mensagem para WhatsApp.
- Login com verificação de senha usando bcrypt.

## Tecnologias

- Python, FastAPI e Uvicorn
- SQL Server Express, acessado por `pyodbc`
- HTML, CSS e JavaScript
- `pdfplumber` para leitura de PDFs e `reportlab` para geração de relatórios

## Requisitos

- Windows
- Python 3.10 ou superior
- SQL Server Express e SQL Server Management Studio (SSMS)
- ODBC Driver 18 for SQL Server

## Configuração

### 1. Crie o banco e as tabelas

No SSMS, execute:

```sql
CREATE DATABASE ExamFlow;
```

Selecione o banco `ExamFlow` e execute [`database/criar_tabelas.sql`](database/criar_tabelas.sql).

### 2. Configure o servidor SQL

Por padrão, a aplicação conecta a `.\SQLEXPRESS`, usa autenticação integrada do Windows e o banco `ExamFlow`. Para usar outro servidor, defina a variável de ambiente antes de iniciar a API:

```powershell
$env:EXAMFLOW_DB_SERVER = ".\SQLEXPRESS"
```

O usuário do Windows que executa a API precisa ter acesso ao banco. O nome do servidor pode variar conforme a instalação local.

### 3. Instale as dependências

Na pasta do projeto, crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Inicie a aplicação

Para desenvolvimento, rode a API na pasta do projeto:

```powershell
uvicorn backend.main:app --reload
```

A API e a interface estarão disponíveis em:

- Interface: <http://127.0.0.1:8000/frontend/index.html>
- Verificação da API: <http://127.0.0.1:8000/>
- Verificação da conexão com o banco: <http://127.0.0.1:8000/teste-banco>

Também é possível iniciar pelo `start_examflow.bat`, que executa a API na porta `8001` e requer as dependências instaladas em `.venv`.

## Login

A tabela `usuarios` armazena o hash bcrypt da senha. O script SQL cria a tabela, mas não cria um usuário inicial; é necessário cadastrar um usuário antes de entrar. A função para gerar hash está em `backend/auth.py`.

## Rotas da API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Estado básico da API |
| `GET` | `/teste-banco` | Testa a conexão com SQL Server |
| `POST` | `/login` | Valida login e senha |
| `POST` | `/parse-pdf` | Lê um PDF e retorna uma amostra de funcionários |
| `POST` | `/importacao/preview` | Compara um PDF com o cadastro atual |
| `POST` | `/importacao/confirmar` | Aplica a importação do PDF |
| `GET` | `/exames/pendentes?ano=AAAA&mes=MM` | Lista exames pendentes do mês |
| `POST` | `/exames/agendar` | Cria um agendamento |
| `GET` | `/exames/agendados` | Lista agendamentos paginados |
| `PUT` | `/exames/{id}/cancelar` | Cancela um exame |
| `PUT` | `/exames/{id}/confirmar` | Confirma um agendamento |
| `PUT` | `/exames/{id}/observacao` | Atualiza a observação |
| `GET` | `/exames/{id}/pdf` | Gera PDF de convocação |
| `GET` | `/exames/relatorio-pdf` | Gera relatório de exames |

## Segurança

O login está implementado, mas atualmente as demais rotas da API não exigem autenticação. Execute o sistema apenas em ambiente controlado até que a autorização seja aplicada a todas as rotas. Não exponha a API diretamente à internet.

PDFs, planilhas, arquivos `.env`, ambientes virtuais e arquivos compilados estão ignorados pelo Git. Antes de compartilhar dados de teste, confirme que não contêm informações reais de funcionários.

## Estrutura do projeto

```text
backend/       API, acesso ao banco, importação, regras e geração de PDFs
database/     script SQL para criação das tabelas
frontend/     páginas e JavaScript da interface
requirements.txt
start_examflow.bat
