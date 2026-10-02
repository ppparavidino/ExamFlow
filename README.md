# ExamFlow

Sistema interno simples para controle e convocação de exames periódicos.

Mesma estrutura do projeto **Suporte TI**.

## Estrutura

```
ExamFlow/
├── backend/
│   ├── database.py      ← conexão SQL Express (pyodbc)
│   ├── auth.py          ← hash de senha (bcrypt)
│   └── main.py          ← API FastAPI
├── frontend/
│   ├── index.html
│   └── style.css
├── database/
│   └── criar_tabelas.sql
└── requirements.txt
```

## Preparação

### 1. Criar o banco (SSMS)

```sql
CREATE DATABASE ExamFlow;
```

Depois rode o script:

```
database/criar_tabelas.sql
```

### 2. Dependências

```bash
cd ExamFlow
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Rodar

Na pasta raiz do ExamFlow:

```bash
uvicorn backend.main:app --reload
```

- API: http://127.0.0.1:8000
- Teste do banco: http://127.0.0.1:8000/teste-banco
- Front: http://127.0.0.1:8000/frontend/index.html

## Conexão

Arquivo `backend/database.py` (igual ao Suporte TI):

```python
SERVER = r".\SQLEXPRESS"
DATABASE = "ExamFlow"
DRIVER = "ODBC Driver 18 for SQL Server"
```

Defina `EXAMFLOW_DB_SERVER` no ambiente para usar outro servidor SQL sem
registrar o nome da máquina nos arquivos do projeto.

## Próximas etapas

1. Login da responsável
2. Parser do PDF + importação
3. Dashboard e exames do mês
4. Agendamento + WhatsApp + PDF
