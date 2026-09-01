-- ============================================================
-- ExamFlow — criação das tabelas
-- Rode este script no SSMS com o banco ExamFlow selecionado
-- ============================================================

USE ExamFlow;
GO

-- Usuário do sistema (só a responsável)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'usuarios')
BEGIN
    CREATE TABLE usuarios (
        id          INT IDENTITY(1,1) PRIMARY KEY,
        nome        NVARCHAR(120)  NOT NULL,
        login       NVARCHAR(80)   NOT NULL UNIQUE,
        senha_hash  NVARCHAR(255)  NOT NULL,
        email       NVARCHAR(180)  NULL,
        ativo       BIT            NOT NULL DEFAULT 1,
        criado_em   DATETIME       NOT NULL DEFAULT GETDATE()
    );
END
GO

-- Funcionários (vêm do PDF do TransNet)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'funcionarios')
BEGIN
    CREATE TABLE funcionarios (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        matricula       NVARCHAR(20)   NOT NULL UNIQUE,
        empresa         NVARCHAR(10)   NOT NULL DEFAULT '001',
        nome            NVARCHAR(200)  NOT NULL,
        data_admissao   DATE           NOT NULL,
        cargo           NVARCHAR(150)  NOT NULL,
        celular         NVARCHAR(20)   NULL,   -- só dígitos
        celular_raw     NVARCHAR(40)   NULL,   -- como veio no PDF
        ativo           BIT            NOT NULL DEFAULT 1,  -- 0 = saiu
        criado_em       DATETIME       NOT NULL DEFAULT GETDATE(),
        atualizado_em   DATETIME       NOT NULL DEFAULT GETDATE()
    );
END
GO

-- Exames periódicos
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'exames')
BEGIN
    CREATE TABLE exames (
        id               INT IDENTITY(1,1) PRIMARY KEY,
        funcionario_id   INT            NOT NULL,
        tipo             NVARCHAR(40)   NOT NULL DEFAULT 'PERIODICO',
        data_prevista    DATE           NULL,
        data_agendada    DATE           NULL,
        horario          TIME           NULL,
        local_exame      NVARCHAR(200)  NULL,
        status           NVARCHAR(20)   NOT NULL DEFAULT 'PENDENTE',
        -- PENDENTE | AGENDADO | REALIZADO | CANCELADO
        observacao       NVARCHAR(MAX)  NULL,
        criado_em        DATETIME       NOT NULL DEFAULT GETDATE(),
        CONSTRAINT FK_exames_funcionario
            FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
    );
END
GO

-- Histórico de importações do PDF
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'importacoes')
BEGIN
    CREATE TABLE importacoes (
        id               INT IDENTITY(1,1) PRIMARY KEY,
        nome_arquivo     NVARCHAR(255)  NOT NULL,
        data_importacao  DATETIME       NOT NULL DEFAULT GETDATE(),
        total            INT            NOT NULL DEFAULT 0,
        novos            INT            NOT NULL DEFAULT 0,
        alterados        INT            NOT NULL DEFAULT 0,
        ausentes         INT            NOT NULL DEFAULT 0
    );
END
GO

PRINT 'Tabelas do ExamFlow criadas/verificadas com sucesso.';
