import sqlite3
import os

def inicializar_banco():
    # Conecta (ou cria) o arquivo do banco de dados local
    conexao = sqlite3.connect('clinica.db')
    cursor = conexao.cursor()

    # Criando as tabelas principais
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Pacientes (
        id_paciente INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        data_nascimento TEXT,
        sexo TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Exames_Catalogo (
        id_exame TEXT PRIMARY KEY,
        nome_amigavel TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Regras_Complementares (
        id_regra INTEGER PRIMARY KEY AUTOINCREMENT,
        exame_gatilho TEXT,
        exame_sugerido TEXT,
        FOREIGN KEY(exame_gatilho) REFERENCES Exames_Catalogo(id_exame),
        FOREIGN KEY(exame_sugerido) REFERENCES Exames_Catalogo(id_exame)
    )
    ''')
    
    conexao.commit()
    return conexao

def importar_exames(conexao, pasta_exames):
    cursor = conexao.cursor()
    
    if not os.path.exists(pasta_exames):
        print(f"Erro: A pasta '{pasta_exames}' não foi encontrada no diretório.")
        return

    print("Importando catálogo de exames...")
    
    # Varre a pasta lendo os arquivos .jsonux
    for nome_arquivo in os.listdir(pasta_exames):
        if nome_arquivo.endswith('.jsonux'):
            # Limpa o nome do arquivo para usar como ID (ex: EXM-B12-SERICA)
            id_exame = nome_arquivo.replace('.jsonux', '')
            
            # Cria um nome mais amigável para aparecer na tela depois
            nome_amigavel = id_exame.replace('EXM-', '').replace('-', ' ')
            
            cursor.execute('''
            INSERT OR IGNORE INTO Exames_Catalogo (id_exame, nome_amigavel)
            VALUES (?, ?)
            ''', (id_exame, nome_amigavel))
            
    conexao.commit()
    print("Exames importados com sucesso!")

if __name__ == "__main__":
    banco = inicializar_banco()
    
    # Aponta para a pasta onde estão os arquivos de exames
    importar_exames(banco, 'exames_internos')
    
    banco.close()
    print("Setup concluído. O arquivo clinica.db está pronto.")