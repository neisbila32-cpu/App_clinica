# Copyright (c) 2026 Neis Bila de Alencar. Todos os direitos reservados.
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
import json
import shutil
import sys
import platform
import re
from datetime import datetime
from fpdf import FPDF
from PIL import Image


def get_base_path():
    """Retorna o diretório de recursos da aplicação.

    Em executável PyInstaller (--onedir), os arquivos embutidos via
    datas=[] ficam em sys._MEIPASS (pasta _internal); caso contrário,
    o diretório do próprio script.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_writable_path(filename):
    """Retorna um caminho gravável para arquivos como o banco de dados.

    No executável, copia o arquivo embutido (_MEIPASS) para ao lado do
    .exe na primeira execução, permitindo escrita sem tocar no bundle.
    """
    if getattr(sys, 'frozen', False):
        base_exe = os.path.dirname(sys.executable)
        destino = os.path.join(base_exe, filename)
        if not os.path.exists(destino):
            embutido = os.path.join(get_base_path(), filename)
            if os.path.exists(embutido):
                try:
                    shutil.copy2(embutido, destino)
                except OSError:
                    return embutido
        return destino
    return os.path.join(get_base_path(), filename)


ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("green")

class AppClinica(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema de Gestão Clínica")
        self.geometry("950x750")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.configurar_banco_dados()

        self.paciente_atual_id = None
        self.paciente_atual_nome = None
        self.paciente_atual_nasc = None
        self.paciente_atual_sexo = None
        self.exames_selecionados_lista = []
        self.opcoes_exames = []
        self.resultados_lancados = {}  # {id_exame: (valor, status)} preenchido no modal
        
        self.tmb_atual = ""
        self.vet_atual = ""

        # --- MENU LATERAL ---
        self.menu_lateral = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1b5e20")
        self.menu_lateral.grid(row=0, column=0, sticky="nsew")
        self.menu_lateral.grid_rowconfigure(4, weight=1)

        self.label_menu = ctk.CTkLabel(self.menu_lateral, text="Menu", font=ctk.CTkFont(size=24, weight="bold"), text_color="#ffffff")
        self.label_menu.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_pacientes = ctk.CTkButton(self.menu_lateral, text="Pacientes", command=self.tela_pacientes, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=16, weight="bold"))
        self.btn_pacientes.grid(row=1, column=0, padx=20, pady=10)

        self.btn_consultas = ctk.CTkButton(self.menu_lateral, text="Nova Consulta", command=self.tela_consultas, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=16, weight="bold"))
        self.btn_consultas.grid(row=2, column=0, padx=20, pady=10)

        self.btn_exames = ctk.CTkButton(self.menu_lateral, text="Catálogo de Exames", command=self.tela_exames, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=16, weight="bold"))
        self.btn_exames.grid(row=3, column=0, padx=20, pady=10)

        # Rodapé fixado na parte inferior do menu lateral
        self.label_copyright = ctk.CTkLabel(
            self.menu_lateral,
            text="© 2026 Neis Bila de Alencar. Todos os direitos reservados.",
            font=ctk.CTkFont(size=10),
            text_color="#ffffff",
            justify="left",
            wraplength=170,
        )
        self.label_copyright.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="sw")

        # --- ÁREA PRINCIPAL ---
        self.area_principal = ctk.CTkFrame(self, corner_radius=10, fg_color="#F0F7F4")
        self.area_principal.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.tela_inicial()

    def configurar_banco_dados(self):
        conexao = sqlite3.connect(get_writable_path('clinica.db'))
        cursor = conexao.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Consultas (
            id_consulta INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER,
            data_consulta TEXT,
            anamnese TEXT,
            peso TEXT,
            altura TEXT,
            gordura TEXT,
            conduta TEXT
        )
        ''')
        
        cursor.execute("PRAGMA table_info(Consultas)")
        colunas = [col[1] for col in cursor.fetchall()]
        if 'tmb' not in colunas:
            cursor.execute("ALTER TABLE Consultas ADD COLUMN tmb TEXT")
            cursor.execute("ALTER TABLE Consultas ADD COLUMN vet TEXT")
            cursor.execute("ALTER TABLE Consultas ADD COLUMN naf TEXT")
            cursor.execute("ALTER TABLE Consultas ADD COLUMN metodo_tmb TEXT")
        if 'analise_exames' not in colunas:
            cursor.execute("ALTER TABLE Consultas ADD COLUMN analise_exames TEXT")

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Exames_Solicitados (
            id_solicitacao INTEGER PRIMARY KEY AUTOINCREMENT,
            id_consulta INTEGER,
            id_exame TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Arquivos_Paciente (
            id_arquivo INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER,
            nome_arquivo TEXT,
            caminho_arquivo TEXT,
            data_upload TEXT
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
            exame_sugerido TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Resultados_Exames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_consulta INTEGER,
            id_exame TEXT,
            valor REAL,
            status TEXT
        )
        ''')

        cursor.execute("SELECT COUNT(*) FROM Exames_Catalogo")
        if cursor.fetchone()[0] == 0:
            exames_basicos = [
                ('EXM-GLICEMIA-DE-JEJUM', 'GLICEMIA DE JEJUM'),
                ('EXM-HOMA-IR', 'HOMA IR'),
                ('EXM-HBA1C', 'HBA1C'),
                ('EXM-TOTG-2H', 'TOTG 2H'),
                ('EXM-COLESTEROL-TOTAL', 'COLESTEROL TOTAL'),
                ('EXM-HDL-COLESTEROL', 'HDL COLESTEROL'),
                ('EXM-LDL-COLESTEROL', 'LDL COLESTEROL'),
                ('EXM-TRIGLICERIDEOS', 'TRIGLICERIDEOS'),
                ('EXM-FERRO-SERICO', 'FERRO SERICO'),
                ('EXM-FERRITINA-SERICA', 'FERRITINA SERICA'),
                ('EXM-SATURACAO-DE-TRANSFERRINA', 'SATURACAO DE TRANSFERRINA'),
                ('EXM-TIBC', 'TIBC'),
                ('EXM-B12-SERICA', 'B12 SERICA'),
                ('EXM-ACIDO-METILMALONICO', 'ACIDO METILMALONICO'),
                ('EXM-HOMOCISTEINA-SERICA', 'HOMOCISTEINA SERICA')
            ]
            cursor.executemany("INSERT OR IGNORE INTO Exames_Catalogo (id_exame, nome_amigavel) VALUES (?, ?)", exames_basicos)
        
        cursor.execute('''
            INSERT INTO Regras_Complementares (exame_gatilho, exame_sugerido)
            SELECT 'EXM-GLICEMIA-DE-JEJUM', 'EXM-HOMA-IR'
            WHERE NOT EXISTS (SELECT 1 FROM Regras_Complementares WHERE exame_gatilho = 'EXM-GLICEMIA-DE-JEJUM')
        ''')
        conexao.commit()
        conexao.close()

    def limpar_area_principal(self):
        for widget in self.area_principal.winfo_children():
            widget.destroy()

    def tela_inicial(self):
        self.limpar_area_principal()

        caminho_imagem = os.path.join(get_base_path(), "welcome_nutrilab.png")
        self.imagem_bem_vindo_pil = Image.open(caminho_imagem)
        self._tamanho_imagem_bem_vindo = self.imagem_bem_vindo_pil.size
        self.imagem_bem_vindo = ctk.CTkImage(
            light_image=self.imagem_bem_vindo_pil,
            dark_image=self.imagem_bem_vindo_pil,
            size=self._tamanho_imagem_bem_vindo
        )

        self.label_bem_vindo = ctk.CTkLabel(self.area_principal, text="", image=self.imagem_bem_vindo, fg_color="#F0F7F4")
        self.label_bem_vindo.pack(fill="both", expand=True, padx=60, pady=40)
        self.label_bem_vindo.bind("<Configure>", self._redimensionar_imagem_bem_vindo)

    def _redimensionar_imagem_bem_vindo(self, event):
        largura_orig, altura_orig = self.imagem_bem_vindo_pil.size
        largura_disp = self.area_principal.winfo_width() - 120
        altura_disp = self.area_principal.winfo_height() - 80
        if largura_disp > 1 and altura_disp > 1:
            fator = min(largura_disp / largura_orig, altura_disp / altura_orig)
            novo_w = int(largura_orig * fator)
            novo_h = int(altura_orig * fator)
            if novo_w > 1 and novo_h > 1 and (novo_w, novo_h) != self._tamanho_imagem_bem_vindo:
                self._tamanho_imagem_bem_vindo = (novo_w, novo_h)
                self.imagem_bem_vindo = ctk.CTkImage(
                    light_image=self.imagem_bem_vindo_pil,
                    dark_image=self.imagem_bem_vindo_pil,
                    size=(novo_w, novo_h)
                )
                self.label_bem_vindo.configure(image=self.imagem_bem_vindo)

    # --- MÓDULO DE PACIENTES ---
    def tela_pacientes(self):
        self.limpar_area_principal()

        ctk.CTkLabel(self.area_principal, text="Gestão de Pacientes", font=ctk.CTkFont(size=24, weight="bold"), text_color="#1b5e20").pack(pady=(20, 10))
        self.tabview = ctk.CTkTabview(self.area_principal, fg_color="#e8f5e9",
                                      segmented_button_selected_color="#2e7d32", segmented_button_selected_hover_color="#1b5e20",
                                      segmented_button_unselected_color="#558b2f", segmented_button_unselected_hover_color="#689f38",
                                      segmented_button_font=ctk.CTkFont(size=15, weight="bold"),
                                      text_color="#ffffff", text_color_disabled="#d5e8d7")
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)
        aba_cadastro = self.tabview.add("Novo Cadastro")
        aba_lista = self.tabview.add("Pacientes Cadastrados")

        self.entry_nome = ctk.CTkEntry(aba_cadastro, placeholder_text="Nome Completo", width=300, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", placeholder_text_color="#7a9e7e", border_color="#a5d6a7")
        self.entry_nome.pack(pady=10)
        self.entry_nasc = ctk.CTkEntry(aba_cadastro, placeholder_text="Data de Nascimento (DD/MM/AAAA)", width=300, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", placeholder_text_color="#7a9e7e", border_color="#a5d6a7")
        self.entry_nasc.pack(pady=10)
        self.combo_sexo = ctk.CTkComboBox(aba_cadastro, values=["Feminino", "Masculino"], width=300, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", button_color="#4caf50", button_hover_color="#388e3c", dropdown_fg_color="#ffffff", dropdown_hover_color="#c8e6c9", dropdown_text_color="#1b5e20")
        self.combo_sexo.set("Feminino")
        self.combo_sexo.pack(pady=10)
        ctk.CTkButton(aba_cadastro, text="Salvar Cadastro", command=self.salvar_paciente, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        self.lbl_mensagem = ctk.CTkLabel(aba_cadastro, text="", text_color="#2e7d32", font=ctk.CTkFont(size=15))
        self.lbl_mensagem.pack()

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#ffffff", foreground="#1b5e20", rowheight=34, fieldbackground="#ffffff", borderwidth=0, font=("Segoe UI", 14))
        style.map('Treeview', background=[('selected', '#4caf50')], foreground=[('selected', '#ffffff')])
        style.configure("Treeview.Heading", background="#4caf50", foreground="#ffffff", relief="flat", font=("Segoe UI", 14, "bold"))
        style.map("Treeview.Heading", background=[('active', '#388e3c')])
        
        tree_frame = ctk.CTkFrame(aba_lista, fg_color="#e8f5e9")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Nome", "Nascimento", "Sexo"), show="headings", style="Treeview")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("Nascimento", text="Nascimento")
        self.tree.heading("Sexo", text="Sexo")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Nome", width=300)
        self.tree.column("Nascimento", width=120, anchor="center")
        self.tree.column("Sexo", width=100, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self.abrir_perfil_paciente)
        self.carregar_tabela_pacientes()

        # Botão de exclusão debajo de la tabla (acción destructiva em vermelho)
        ctk.CTkButton(
            aba_lista,
            text="🗑️ Excluir Paciente",
            fg_color="#c62828",
            hover_color="#b71c1c",
            text_color="#ffffff",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.eliminar_paciente,
        ).pack(fill="x", padx=10, pady=10)

    def salvar_paciente(self):
        nome = self.entry_nome.get()
        nasc = self.entry_nasc.get()
        sexo = self.combo_sexo.get()
        if nome.strip() == "":
            self.lbl_mensagem.configure(text="Erro: O nome é obrigatório.", text_color="#c62828")
            return
        conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
        cursor = conexao.cursor()
        cursor.execute('INSERT INTO Pacientes (nome, data_nascimento, sexo) VALUES (?, ?, ?)', (nome, nasc, sexo))
        conexao.commit()
        conexao.close()
        self.entry_nome.delete(0, 'end')
        self.entry_nasc.delete(0, 'end')
        self.carregar_tabela_pacientes()
        self.tabview.set("Pacientes Cadastrados")

    def carregar_tabela_pacientes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
        cursor = conexao.cursor()
        cursor.execute("SELECT id_paciente, nome, data_nascimento, sexo FROM Pacientes")
        linhas = cursor.fetchall()
        conexao.close()
        for linha in linhas:
            self.tree.insert("", "end", values=linha)

    def eliminar_paciente(self):
        """Elimina definitivamente el paciente seleccionado en la tabla."""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Excluir Paciente", "Selecione um paciente na tabela para excluir.")
            return

        valores = self.tree.item(seleccion[0])['values']
        id_paciente = valores[0]
        nome_paciente = valores[1]

        confirmar = messagebox.askyesno(
            "Confirmar Exclusão",
            f"⚠️ Esta ação eliminará DEFINITIVAMENTE o paciente:\n\n"
            f"{nome_paciente} (ID: {id_paciente})\n\n"
            f"Deseja continuar?",
        )
        if not confirmar:
            return

        conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM Pacientes WHERE id_paciente = ?", (id_paciente,))
        conexao.commit()
        conexao.close()

        self.carregar_tabela_pacientes()

    # --- PERFIL DO PACIENTE ---
    def abrir_perfil_paciente(self, event):
        selecao = self.tree.selection()
        if not selecao: return
        valores = self.tree.item(selecao[0])['values']
        self.paciente_atual_id, self.paciente_atual_nome, nasc, sexo = valores
        self.paciente_atual_nasc = nasc
        self.paciente_atual_sexo = sexo
        
        self.limpar_area_principal()
        ctk.CTkButton(self.area_principal, text="← Voltar", width=80, fg_color="#c8e6c9", hover_color="#a5d6a7", text_color="#1b5e20", border_width=1, border_color="#4caf50", font=ctk.CTkFont(size=15), command=self.tela_pacientes).pack(anchor="nw", pady=10, padx=10)
        ctk.CTkLabel(self.area_principal, text=f"Perfil Clínico: {self.paciente_atual_nome}", font=ctk.CTkFont(size=26, weight="bold"), text_color="#1b5e20").pack(pady=(0, 5))
        ctk.CTkLabel(self.area_principal, text=f"ID: {self.paciente_atual_id}  |  Nascimento: {nasc}  |  Sexo: {sexo}", font=ctk.CTkFont(size=17), text_color="#2f3e33").pack(pady=5)

        tabview_perfil = ctk.CTkTabview(self.area_principal, fg_color="#e8f5e9",
                                        segmented_button_selected_color="#2e7d32", segmented_button_selected_hover_color="#1b5e20",
                                        segmented_button_unselected_color="#558b2f", segmented_button_unselected_hover_color="#689f38",
                                        segmented_button_font=ctk.CTkFont(size=15, weight="bold"),
                                        text_color="#ffffff", text_color_disabled="#d5e8d7")
        tabview_perfil.pack(padx=20, pady=10, fill="both", expand=True)
        
        aba_hist = tabview_perfil.add("Histórico de Consultas")
        aba_exm = tabview_perfil.add("Exames e Arquivos")
        
        ctk.CTkButton(aba_hist, text="Iniciar Nova Consulta", command=self.tela_consultas, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        scroll_hist = ctk.CTkScrollableFrame(aba_hist, fg_color="transparent")
        scroll_hist.pack(fill="both", expand=True, padx=10, pady=10)

        conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
        cursor = conexao.cursor()
        cursor.execute('''
            SELECT id_consulta, data_consulta, anamnese, peso, altura, gordura, conduta, tmb, vet, naf, metodo_tmb, analise_exames
            FROM Consultas
            WHERE id_paciente = ?
            ORDER BY id_consulta DESC
        ''', (self.paciente_atual_id,))
        consultas = cursor.fetchall()

        if not consultas:
            ctk.CTkLabel(scroll_hist, text="Nenhuma consulta registada ainda.", text_color="#556b58", font=ctk.CTkFont(size=15)).pack(pady=20)
        else:
            for consulta in consultas:
                id_cons, data_cons, anamnese, peso, altura, gordura, conduta, tmb, vet, naf, metodo, analise_exames = consulta

                card = ctk.CTkFrame(scroll_hist, corner_radius=8, fg_color="#ffffff", border_width=1, border_color="#c8e6c9")
                card.pack(fill="x", pady=10, ipady=10)

                ctk.CTkLabel(card, text=f"📅 Data: {data_cons}", font=ctk.CTkFont(weight="bold", size=19), text_color="#1b5e20").pack(anchor="w", padx=15, pady=(10, 5))

                if anamnese:
                    ctk.CTkLabel(card, text=f"Anamnese: {anamnese}", justify="left", wraplength=700, font=ctk.CTkFont(size=15)).pack(anchor="w", padx=15, pady=2)

                antro_texto = []
                if peso: antro_texto.append(f"Peso: {peso}kg")
                if altura: antro_texto.append(f"Altura: {altura}m")
                if gordura: antro_texto.append(f"Gordura: {gordura}%")
                if tmb and vet:
                    antro_texto.append(f"TMB: {float(tmb):.2f} kcal ({metodo})")
                    antro_texto.append(f"VET: {float(vet):.2f} kcal (NAF: {naf})")

                if antro_texto:
                    ctk.CTkLabel(card, text=f"Antropometria e Gasto:\n" + "\n".join(antro_texto), justify="left", font=ctk.CTkFont(size=15)).pack(anchor="w", padx=15, pady=2)

                if conduta:
                    ctk.CTkLabel(card, text=f"Conduta: {conduta}", justify="left", wraplength=700, font=ctk.CTkFont(size=15)).pack(anchor="w", padx=15, pady=2)

                if analise_exames:
                    ctk.CTkLabel(card, text=f"Análise e Valores de Referência: {analise_exames}", justify="left", wraplength=700, font=ctk.CTkFont(size=15)).pack(anchor="w", padx=15, pady=2)

                cursor.execute('''
                    SELECT E.nome_amigavel
                    FROM Exames_Solicitados S
                    JOIN Exames_Catalogo E ON S.id_exame = E.id_exame
                    WHERE S.id_consulta = ?
                ''', (id_cons,))
                exames = cursor.fetchall()

                exames_str = ""
                if exames:
                    ctk.CTkLabel(card, text="Exames Solicitados:", font=ctk.CTkFont(weight="bold", size=16), text_color="#1b5e20").pack(anchor="w", padx=15, pady=(5,0))
                    exames_str = ", ".join([ex[0] for ex in exames])
                    ctk.CTkLabel(card, text=exames_str, justify="left", wraplength=700, text_color="#00695c", font=ctk.CTkFont(size=15)).pack(anchor="w", padx=15, pady=(0, 10))
                
                ctk.CTkButton(card, text="Gerar PDF", width=120, fg_color="#558b2f", hover_color="#33691e", text_color="#ffffff", font=ctk.CTkFont(size=15, weight="bold"), 
                              command=lambda c=consulta, e=exames_str: self.gerar_pdf_evolucao(c, e)).pack(anchor="e", padx=15, pady=10)

        ctk.CTkButton(aba_exm, text="Anexar Documento / Imagem", command=self.anexar_arquivo_paciente, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=10)
        self.scroll_arquivos = ctk.CTkScrollableFrame(aba_exm, fg_color="transparent")
        self.scroll_arquivos.pack(fill="both", expand=True, padx=10, pady=10)
        self.carregar_lista_arquivos()
        conexao.close()

    def gerar_pdf_evolucao(self, consulta_dados, exames_str):
        try:
            # ------------------------------------------------------------------
            # 1) Desempacotamento seguro da tupla da consulta.
            #    O SELECT traz 12 colunas (incluindo analise_exames), então
            #    precisamos receber todas — e tolerar tuplas maiores/menores
            #    caso o schema evolua.
            # ------------------------------------------------------------------
            esperado = (
                "id_consulta", "data_consulta", "anamnese", "peso", "altura",
                "gordura", "conduta", "tmb", "vet", "naf", "metodo_tmb",
                "analise_exames",
            )
            if not consulta_dados or len(consulta_dados) < len(esperado):
                raise ValueError(
                    f"Tupla de consulta inválida (esperado {len(esperado)} "
                    f"campos, recebi {len(consulta_dados) if consulta_dados else 0})."
                )
            id_cons = consulta_dados[0]
            data_cons = consulta_dados[1] or ""
            anamnese = consulta_dados[2] or ""
            peso = consulta_dados[3]
            altura = consulta_dados[4]
            gordura = consulta_dados[5]
            conduta = consulta_dados[6] or ""
            tmb = consulta_dados[7]
            vet = consulta_dados[8]
            naf = consulta_dados[9]
            metodo = consulta_dados[10] or ""
            analise_exames = consulta_dados[11] or ""

            # ------------------------------------------------------------------
            # 2) Conexão única para ler analise_exames (fallback) e resultados.
            # ------------------------------------------------------------------
            conexao_pdf = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
            cursor_pdf = conexao_pdf.cursor()

            if not analise_exames:
                cursor_pdf.execute(
                    "SELECT analise_exames FROM Consultas WHERE id_consulta = ?",
                    (id_cons,),
                )
                resultado_analise = cursor_pdf.fetchone()
                analise_exames = (resultado_analise[0] or "") if resultado_analise else ""

            # Resultados efetivamente lançados para esta consulta
            cursor_pdf.execute('''
                SELECT E.nome_amigavel, R.valor, R.status
                FROM Resultados_Exames R
                JOIN Exames_Catalogo E ON R.id_exame = E.id_exame
                WHERE R.id_consulta = ?
                ORDER BY E.nome_amigavel
            ''', (id_cons,))
            resultados_rows = cursor_pdf.fetchall() or []

            # Data de nascimento e sexo do paciente (para idade e IMC no relatório)
            data_nasc_paciente = ""
            sexo_paciente = ""
            cursor_pdf.execute('''
                SELECT P.data_nascimento, P.sexo
                FROM Consultas C
                JOIN Pacientes P ON C.id_paciente = P.id_paciente
                WHERE C.id_consulta = ?
            ''', (id_cons,))
            linha_paciente_pdf = cursor_pdf.fetchone()
            if linha_paciente_pdf:
                data_nasc_paciente = linha_paciente_pdf[0] or ""
                sexo_paciente = linha_paciente_pdf[1] or ""
            conexao_pdf.close()

            # ------------------------------------------------------------------
            # 3) Helpers de texto seguros (sempre string, nunca None).
            # ------------------------------------------------------------------
            def formatar_texto(texto):
                if texto is None:
                    return ""
                return str(texto).encode('latin-1', 'replace').decode('latin-1')

            def formatar_valor(v):
                if v is None or v == "":
                    return "—"
                try:
                    return f"{float(v):.2f}".rstrip('0').rstrip('.')
                except (TypeError, ValueError):
                    return str(v)

            def rotulo_status_pdf(status):
                """Reduz rótulos técnicos (ex.: '170–285 µmol/L (faixa normal)')
                à classificação simples exibida na coluna Status do PDF.

                Quando o texto entre parênteses traz a classificação
                (ex.: 'faixa normal'), devolve 'Normal'/'Baixo'/'Alto';
                rótulos que já trazem a classificação própria
                (ex.: 'Resistência grave (>4,0)') seguem impressos intactos.
                """
                texto = (status or "").strip()
                if not texto:
                    return ""
                dentro = re.search(r"\(([^)]+)\)", texto)
                if dentro:
                    conteudo = dentro.group(1).lower()
                    if re.search(r"\b(normal|adequado)\b", conteudo):
                        return "Normal"
                    if re.search(r"\bbaixo\b", conteudo):
                        return "Baixo"
                    if re.search(r"\balto\b", conteudo):
                        return "Alto"
                return texto

            # ------------------------------------------------------------------
            # 4) Construção do PDF
            # ------------------------------------------------------------------
            pdf = FPDF()
            pdf.add_page()

            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, formatar_texto("Relatório de Consulta Nutricional"), ln=True, align='C')
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, formatar_texto(f"Paciente: {self.paciente_atual_nome or ''}"), ln=True)
            pdf.cell(0, 8, formatar_texto(f"Data de Atendimento: {data_cons}"), ln=True)
            pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
            pdf.ln(10)

            if anamnese:
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, formatar_texto("Anamnese e Queixas:"), ln=True)
                pdf.set_font("Arial", '', 11)
                pdf.multi_cell(0, 6, formatar_texto(anamnese))
                pdf.ln(5)

            antro_texto = []
            if peso not in (None, ""):
                antro_texto.append(f"Peso: {peso}kg")
            if altura not in (None, ""):
                antro_texto.append(f"Altura: {altura}m")
            if gordura not in (None, ""):
                antro_texto.append(f"Gordura: {gordura}%")
            if tmb not in (None, "") and vet not in (None, ""):
                try:
                    tmb_f = float(tmb)
                    vet_f = float(vet)
                    antro_texto.append(
                        f"TMB: {tmb_f:.2f} kcal ({metodo}) | "
                        f"VET: {vet_f:.2f} kcal (NAF: {naf or '-'})"
                    )
                except (TypeError, ValueError):
                    antro_texto.append(
                        f"TMB: {tmb} kcal ({metodo}) | "
                        f"VET: {vet} kcal (NAF: {naf or '-'})"
                    )

            # IMC calculado com classificação oficial por faixa etária
            imc_pdf = None
            try:
                peso_f = float(str(peso).replace(',', '.'))
                altura_f = float(str(altura).replace(',', '.'))
                if peso_f > 0 and altura_f > 0:
                    imc_pdf = peso_f / (altura_f ** 2)
            except (TypeError, ValueError, ZeroDivisionError):
                imc_pdf = None
            if imc_pdf is not None:
                idade_pdf = self._calcular_idade_por_nascimento(data_nasc_paciente)
                classificacao_imc = self._classificar_imc(imc_pdf, idade_pdf)
                idade_txt = f"{idade_pdf} anos" if idade_pdf is not None else "idade não informada"
                antro_texto.append(
                    f"IMC: {imc_pdf:.1f} kg/m² - {classificacao_imc} (idade: {idade_txt})"
                )

            if antro_texto:
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, formatar_texto("Dados Antropométricos e Gasto Energético:"), ln=True)
                pdf.set_font("Arial", '', 11)
                for linha in antro_texto:
                    pdf.cell(0, 6, formatar_texto(linha), ln=True)
                pdf.ln(5)

            if conduta:
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, formatar_texto("Conduta Dietoterápica / Prescrição:"), ln=True)
                pdf.set_font("Arial", '', 11)
                pdf.multi_cell(0, 6, formatar_texto(conduta))
                pdf.ln(5)

            if exames_str:
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, formatar_texto("Exames e Marcadores Solicitados:"), ln=True)
                pdf.set_font("Arial", '', 11)
                pdf.multi_cell(0, 6, formatar_texto(exames_str))
                pdf.ln(5)

            # Tabela de resultados lançados (se houver)
            if resultados_rows:
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, formatar_texto("Resultados Laboratoriais Lançados:"), ln=True)
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(90, 6, formatar_texto("Exame"), border=1)
                pdf.cell(45, 6, formatar_texto("Valor"), border=1)
                pdf.cell(45, 6, formatar_texto("Status"), border=1, ln=True)
                pdf.set_font("Arial", '', 10)
                for nome_exame, valor, status in resultados_rows:
                    pdf.cell(90, 6, formatar_texto(nome_exame or ""), border=1)
                    pdf.cell(45, 6, formatar_texto(formatar_valor(valor)), border=1)
                    pdf.cell(45, 6, formatar_texto(rotulo_status_pdf(status)), border=1, ln=True)
                pdf.ln(5)

            # Índices metabólicos calculados (pares clínicos presentes na consulta)
            valores_resultados = {}
            for nome_exame, valor, _status in resultados_rows:
                try:
                    valores_resultados[str(nome_exame or '').upper()] = float(str(valor).replace(',', '.'))
                except (TypeError, ValueError):
                    continue
            indices_pdf = self._calcular_indices_para_pdf(valores_resultados)
            if indices_pdf:
                if pdf.get_y() > 240:
                    pdf.add_page()
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, formatar_texto("Índices Metabólicos Calculados:"), ln=True)
                pdf.set_font("Arial", '', 11)
                for linha_indice in indices_pdf:
                    pdf.multi_cell(0, 6, formatar_texto(linha_indice))
                pdf.ln(5)

            # ------------------------------------------------------------------
            # 5) Persistência
            # ------------------------------------------------------------------
            base_dir = get_writable_path("arquivos_pacientes")
            os.makedirs(base_dir, exist_ok=True)
            pasta_paciente = os.path.join(
                base_dir, f"paciente_{self.paciente_atual_id}"
            )
            os.makedirs(pasta_paciente, exist_ok=True)

            data_slug = (data_cons or "sem_data").replace('/', '-').replace(':', 'h').replace(' ', '_')
            nome_arquivo = f"Conduta_{data_slug}.pdf"
            caminho_pdf = os.path.join(pasta_paciente, nome_arquivo)

            pdf.output(caminho_pdf)
            self.abrir_arquivo_externo(caminho_pdf)

        except Exception as exc:
            import traceback
            print(f"[ERRO] Falha ao gerar PDF da consulta {consulta_dados if consulta_dados else '?'}: {exc}")
            traceback.print_exc()
            try:
                messagebox.showerror(
                    "Erro ao gerar PDF",
                    f"Não foi possível gerar o PDF.\n\n{exc}\n\n"
                    f"Detalhes foram impressos no terminal."
                )
            except Exception:
                pass

    def anexar_arquivo_paciente(self):
        caminho_origem = filedialog.askopenfilename(title="Selecione o Exame", filetypes=[("Documentos e Imagens", "*.pdf *.png *.jpg *.jpeg *.doc *.docx")])
        if not caminho_origem: return
        base_dir = get_base_path()
        pasta_paciente = os.path.join(base_dir, "arquivos_pacientes", f"paciente_{self.paciente_atual_id}")
        os.makedirs(pasta_paciente, exist_ok=True)
        nome_arquivo = os.path.basename(caminho_origem)
        caminho_destino = os.path.join(pasta_paciente, nome_arquivo)
        try:
            shutil.copy2(caminho_origem, caminho_destino)
            conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
            cursor = conexao.cursor()
            cursor.execute('INSERT INTO Arquivos_Paciente (id_paciente, nome_arquivo, caminho_arquivo, data_upload) VALUES (?, ?, ?, ?)', 
                           (self.paciente_atual_id, nome_arquivo, caminho_destino, datetime.now().strftime("%d/%m/%Y %H:%M")))
            conexao.commit()
            conexao.close()
            self.carregar_lista_arquivos()
        except Exception as e:
            print(f"Erro: {e}")

    def carregar_lista_arquivos(self):
        for widget in self.scroll_arquivos.winfo_children(): widget.destroy()
        conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
        cursor = conexao.cursor()
        cursor.execute('SELECT nome_arquivo, caminho_arquivo, data_upload FROM Arquivos_Paciente WHERE id_paciente = ? ORDER BY id_arquivo DESC', (self.paciente_atual_id,))
        arquivos = cursor.fetchall()
        conexao.close()
        for nome, caminho, data in arquivos:
            card = ctk.CTkFrame(self.scroll_arquivos, corner_radius=8, fg_color="#ffffff", border_width=1, border_color="#c8e6c9")
            card.pack(fill="x", pady=5, ipady=5)
            ctk.CTkLabel(card, text=f"📄 {nome}", font=ctk.CTkFont(size=15)).pack(side="left", padx=(15, 5))
            ctk.CTkButton(card, text="Abrir", width=60, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=14), command=lambda c=caminho: self.abrir_arquivo_externo(c)).pack(side="right", padx=15)

    def abrir_arquivo_externo(self, caminho):
        try:
            if platform.system() == 'Windows': os.startfile(caminho)
            elif platform.system() == 'Darwin': os.system(f'open "{caminho}"')
            else: os.system(f'xdg-open "{caminho}"')
        except Exception as e:
            pass

    # --- MÓDULO DE CONSULTAS ---
    def tela_consultas(self):
        self.limpar_area_principal()
        
        if not self.paciente_atual_id:
            ctk.CTkLabel(self.area_principal, text="Nenhum paciente selecionado.", font=ctk.CTkFont(size=18)).pack(pady=50)
            return

        self.exames_selecionados_lista = []
        self.resultados_lancados = {}
        self.tmb_atual = ""
        self.vet_atual = ""

        # Cache dos dados do paciente atual (para cálculo de idade e IMC)
        self.paciente_atual_nasc = ""
        self.paciente_atual_sexo = ""
        try:
            conexao_pac = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
            cursor_pac = conexao_pac.cursor()
            cursor_pac.execute('SELECT data_nascimento, sexo FROM Pacientes WHERE id_paciente = ?', (self.paciente_atual_id,))
            linha_pac = cursor_pac.fetchone()
            if linha_pac:
                self.paciente_atual_nasc = linha_pac[0] or ""
                self.paciente_atual_sexo = linha_pac[1] or ""
            conexao_pac.close()
        except Exception as e:
            print(f"[AVISO] Não foi possível carregar nascimento do paciente: {e}")

        scroll_frame = ctk.CTkScrollableFrame(self.area_principal, corner_radius=10, fg_color="#f1f8ea")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(scroll_frame, text=f"Atendimento: {self.paciente_atual_nome}", font=ctk.CTkFont(size=26, weight="bold"), text_color="#1b5e20").pack(pady=10)

        frame_anamnese = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        frame_anamnese.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(frame_anamnese, text="Anamnese e Evolução", font=ctk.CTkFont(weight="bold", size=17), text_color="#1b5e20").pack(side="left")
        ctk.CTkButton(frame_anamnese, text="Importar Sintomas", width=120, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.abrir_modal_padroes("anamnese")).pack(side="right")
        self.txt_anamnese = ctk.CTkTextbox(scroll_frame, width=600, height=100, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", border_width=1, border_color="#a5d6a7")
        self.txt_anamnese.pack(padx=20, pady=5)

        ctk.CTkLabel(scroll_frame, text="Antropometria e Composição Corporal", font=ctk.CTkFont(weight="bold", size=17), text_color="#1b5e20").pack(anchor="w", padx=20, pady=(15, 0))
        frame_antro = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        frame_antro.pack(fill="x", padx=20, pady=5)
        self.entry_peso = ctk.CTkEntry(frame_antro, placeholder_text="Peso (kg)", width=150, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", placeholder_text_color="#7a9e7e", border_color="#a5d6a7")
        self.entry_peso.grid(row=0, column=0, padx=(0, 10))
        self.entry_altura = ctk.CTkEntry(frame_antro, placeholder_text="Altura (m)", width=150, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", placeholder_text_color="#7a9e7e", border_color="#a5d6a7")
        self.entry_altura.grid(row=0, column=1, padx=10)
        self.entry_gordura = ctk.CTkEntry(frame_antro, placeholder_text="% Gordura", width=150, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", placeholder_text_color="#7a9e7e", border_color="#a5d6a7")
        self.entry_gordura.grid(row=0, column=2, padx=10)
        self.entry_peso.bind('<KeyRelease>', self._calcular_imc_dinamico)
        self.entry_altura.bind('<KeyRelease>', self._calcular_imc_dinamico)
        self.lbl_imc = ctk.CTkLabel(frame_antro, text="IMC: -- kg/m²", font=ctk.CTkFont(size=15, weight="bold"), text_color="#556b58")
        self.lbl_imc.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

        frame_calculo = ctk.CTkFrame(scroll_frame, fg_color="#eaf8ec", corner_radius=8, border_width=1, border_color="#a5d6a7")
        frame_calculo.pack(fill="x", padx=20, pady=10, ipady=5)
        linha_metodos = ctk.CTkFrame(frame_calculo, fg_color="transparent")
        linha_metodos.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(linha_metodos, text="Metodologia TMB:", font=ctk.CTkFont(size=15), text_color="#1b5e20").pack(side="left", padx=(0, 10))
        self.combo_metodo_tmb = ctk.CTkComboBox(linha_metodos, values=["Harris-Benedict (1919)", "Mifflin-St Jeor (1990)", "Cunningham (1980)"], width=200, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", button_color="#4caf50", button_hover_color="#388e3c", dropdown_fg_color="#ffffff", dropdown_hover_color="#c8e6c9", dropdown_text_color="#1b5e20", command=self.atualizar_justificativa_metodologica)
        self.combo_metodo_tmb.set("Mifflin-St Jeor (1990)")
        self.combo_metodo_tmb.pack(side="left", padx=10)
        self.entry_naf = ctk.CTkEntry(linha_metodos, placeholder_text="Fator NAF (ex: 1.55)", width=130, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", placeholder_text_color="#7a9e7e", border_color="#a5d6a7")
        self.entry_naf.pack(side="left", padx=10)
        ctk.CTkButton(linha_metodos, text="Calcular", width=100, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=15, weight="bold"), command=self.calcular_metabolismo).pack(side="right")

        self.lbl_justificativa = ctk.CTkLabel(frame_calculo, text="Justificativa: Mifflin; St Jeor (1990) apresenta maior precisão para adultos saudáveis contemporâneos com sobrepeso ou obesidade, baseando-se no peso total.", text_color="#556b58", font=ctk.CTkFont(size=15), justify="left", wraplength=600)
        self.lbl_justificativa.pack(anchor="w", padx=10, pady=5)
        self.lbl_resultado_metabolismo = ctk.CTkLabel(frame_calculo, text="Insira os dados acima para calcular a Taxa Metabólica Basal e o VET.", font=ctk.CTkFont(size=17, weight="bold"), text_color="#1b5e20")
        self.lbl_resultado_metabolismo.pack(pady=10)

        frame_conduta = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        frame_conduta.pack(fill="x", padx=20, pady=(15, 0))
        ctk.CTkLabel(frame_conduta, text="Conduta Dietoterápica", font=ctk.CTkFont(weight="bold", size=17), text_color="#1b5e20").pack(side="left")
        ctk.CTkButton(frame_conduta, text="Importar Padrão", width=120, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.abrir_modal_padroes("conduta")).pack(side="right")
        self.txt_conduta = ctk.CTkTextbox(scroll_frame, width=600, height=100, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", border_width=1, border_color="#a5d6a7")
        self.txt_conduta.pack(padx=20, pady=5)

        ctk.CTkLabel(scroll_frame, text="Solicitação de Exames", font=ctk.CTkFont(weight="bold", size=17), text_color="#1b5e20").pack(anchor="w", padx=20, pady=(15, 0))
        frame_exames = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        frame_exames.pack(fill="x", padx=20, pady=5)

        conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
        cursor = conexao.cursor()
        cursor.execute("SELECT id_exame, nome_amigavel FROM Exames_Catalogo")
        self.catalogo_exames_dict = {f"{linha[1]} ({linha[0]})": linha[0] for linha in cursor.fetchall()}
        conexao.close()
        
        self.opcoes_exames = list(self.catalogo_exames_dict.keys())

        self.exame_escolhido = None
        self.btn_select_exame = ctk.CTkButton(
            frame_exames,
            text="Seleccionar exame...  ▼",
            width=400,
            fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._abrir_select_exame)
        self.btn_select_exame.grid(row=0, column=0, padx=(0, 10))

        ctk.CTkButton(frame_exames, text="Adicionar à Solicitação", command=self.adicionar_exame, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=1)

        frame_analise_exames = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        frame_analise_exames.pack(fill="x", padx=20, pady=(15, 0))
        ctk.CTkLabel(frame_analise_exames, text="Análise e Valores de Referência", font=ctk.CTkFont(weight="bold", size=17), text_color="#1b5e20").pack(side="left")
        ctk.CTkButton(frame_analise_exames, text="Importar Referências", width=160, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.abrir_modal_padroes("exames")).pack(side="right")
        self.txt_analise_exames = ctk.CTkTextbox(scroll_frame, width=600, height=100, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", border_width=1, border_color="#a5d6a7")
        self.txt_analise_exames.pack(padx=20, pady=5)

        self.frame_lista_exames = ctk.CTkFrame(scroll_frame, fg_color="#ffffff", border_width=1, border_color="#c8e6c9")
        self.frame_lista_exames.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(scroll_frame, text="Lançar Resultados", fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=16, weight="bold"),
                      command=self.abrir_modal_resultados).pack(pady=(0, 10))
        
        self.frame_sugestoes = ctk.CTkFrame(scroll_frame, fg_color="#2e7d32", border_width=1, border_color="#4caf50")
        self.frame_sugestoes.pack(fill="x", padx=20, pady=10)
        self.frame_sugestoes.pack_forget()

        self.btn_salvar_evolucao = ctk.CTkButton(scroll_frame, text="Salvar Evolução", fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=18, weight="bold"), height=44, command=self.salvar_consulta)
        self.btn_salvar_evolucao.pack(pady=(30, 10))
        
        self.lbl_msg_consulta = ctk.CTkLabel(scroll_frame, text="", text_color="#2e7d32", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_msg_consulta.pack(pady=5)

    def atualizar_justificativa_metodologica(self, escolha):
        if escolha == "Cunningham (1980)":
            texto = "Justificativa: Cunningham (1980) baseia-se na Massa Livre de Gordura (MLG), sendo o modelo com maior precisão para indivíduos fisicamente ativos e desportistas, prevenindo superestimação."
        elif escolha == "Harris-Benedict (1919)":
            texto = "Justificativa: Harris; Benedict (1919) tende a superestimar o gasto basal em 5% a 15% na população moderna. O uso deve ser cauteloso e acompanhado de anamnese criteriosa."
        elif escolha == "Mifflin-St Jeor (1990)":
            texto = "Justificativa: Mifflin; St Jeor (1990) apresenta maior precisão para adultos saudáveis contemporâneos com sobrepeso ou obesidade, baseando-se no peso total."
        self.lbl_justificativa.configure(text=texto)

    def calcular_metabolismo(self):
        try:
            peso_str = self.entry_peso.get().replace(',', '.')
            altura_str = self.entry_altura.get().replace(',', '.')
            if not peso_str or not altura_str:
                self.lbl_resultado_metabolismo.configure(text="Erro: Preencha Peso e Altura primeiro.", text_color="#c62828")
                return
            peso = float(peso_str)
            altura_cm = float(altura_str) * 100.0
            nasc_date = datetime.strptime(self.paciente_atual_nasc, "%d/%m/%Y")
            hoje = datetime.now()
            idade = hoje.year - nasc_date.year - ((hoje.month, hoje.day) < (nasc_date.month, nasc_date.day))
            metodo = self.combo_metodo_tmb.get()
            sexo = self.paciente_atual_sexo.lower()
            tmb = 0.0
            
            if metodo == "Harris-Benedict (1919)":
                if "fem" in sexo: tmb = 655.0955 + (9.5634 * peso) + (1.8496 * altura_cm) - (4.6756 * idade)
                else: tmb = 66.4730 + (13.7516 * peso) + (5.0033 * altura_cm) - (6.7550 * idade)
            elif metodo == "Mifflin-St Jeor (1990)":
                if "fem" in sexo: tmb = (10.0 * peso) + (6.25 * altura_cm) - (5.0 * idade) - 161.0
                else: tmb = (10.0 * peso) + (6.25 * altura_cm) - (5.0 * idade) + 5.0
            elif metodo == "Cunningham (1980)":
                gordura_str = self.entry_gordura.get().replace(',', '.')
                if not gordura_str:
                    self.lbl_resultado_metabolismo.configure(text="Erro: O método de Cunningham exige o % de Gordura.", text_color="#c62828")
                    return
                gordura = float(gordura_str)
                massa_livre_gordura = peso * (1.0 - (gordura / 100.0))
                tmb = 500.0 + (22.0 * massa_livre_gordura)
            
            naf_str = self.entry_naf.get().replace(',', '.')
            self.tmb_atual = str(tmb)
            if naf_str:
                vet = tmb * float(naf_str)
                self.vet_atual = str(vet)
                self.lbl_resultado_metabolismo.configure(text=f"TMB: {tmb:.2f} kcal  |  VET: {vet:.2f} kcal", text_color="#00a859")
            else:
                self.vet_atual = ""
                self.lbl_resultado_metabolismo.configure(text=f"TMB: {tmb:.2f} kcal  |  (Insira o NAF para calcular VET)", text_color="#2e7d32")
        except ValueError:
            self.lbl_resultado_metabolismo.configure(text="Erro de formatação: Insira apenas números válidos.", text_color="#c62828")
        except Exception:
            self.lbl_resultado_metabolismo.configure(text=f"Erro no cálculo.", text_color="#c62828")

    def abrir_modal_padroes(self, alvo):
        modal = ctk.CTkToplevel(self)
        modal.geometry("500x400")
        modal.attributes("-topmost", True)
        tabview_modal = ctk.CTkTabview(modal, fg_color="#e8f5e9",
                                segmented_button_selected_color="#2e7d32", segmented_button_selected_hover_color="#1b5e20",
                                segmented_button_unselected_color="#558b2f", segmented_button_unselected_hover_color="#689f38",
                                segmented_button_font=ctk.CTkFont(size=15, weight="bold"),
                                text_color="#ffffff", text_color_disabled="#d5e8d7")
        tabview_modal.pack(padx=10, pady=10, fill="both", expand=True)
        if alvo == "conduta":
            modal.title("Importar Condutas e Prescrições")
            aba_condutas = tabview_modal.add("Condutas")
            aba_prescricoes = tabview_modal.add("Prescrições")
            self.listar_arquivos_diretorio("condutas_internas", aba_condutas, self.txt_conduta)
            self.listar_arquivos_diretorio("prescricoes_internas", aba_prescricoes, self.txt_conduta)
        elif alvo == "anamnese":
            modal.title("Importar Sintomas Clínicos")
            aba_sintomas = tabview_modal.add("Sintomas")
            self.listar_arquivos_diretorio("sintomas_internos", aba_sintomas, self.txt_anamnese)
        elif alvo == "exames":
            modal.title("Importar Análise e Valores de Referência de Exames")
            aba_exames_ref = tabview_modal.add("Exames")
            self.listar_arquivos_diretorio("exames_internos", aba_exames_ref, self.txt_analise_exames)

    @staticmethod
    def _normalizar_token(texto):
        """Remove prefixo EXM-, espaços, hífens, underscores e converte para minúsculas."""
        if not texto:
            return ""
        t = str(texto)
        if t.upper().startswith("EXM-"):
            t = t[4:]
        return re.sub(r'[\s\-_]+', '', t).lower()

    @staticmethod
    def _coerce_float(valor):
        """Converte para float quando o valor é numérico; devolve None caso contrário."""
        if isinstance(valor, bool):
            return None
        if isinstance(valor, (int, float)):
            return float(valor)
        if isinstance(valor, str):
            s = valor.strip().replace(',', '.')
            try:
                return float(s)
            except ValueError:
                return None
        return None

    @staticmethod
    def _parse_num(texto):
        """Extrai o primeiro número de uma string, aceitando vírgula decimal."""
        if not isinstance(texto, str):
            return None
        m = re.search(r'\d+(?:[.,]\d+)?', texto.replace(',', '.'))
        if not m:
            return None
        try:
            return float(m.group(0))
        except ValueError:
            return None

    def _extrair_refs_por_regex(self, texto):
        """Fallback: extrai (ref_min, ref_max) de texto livre usando regex."""
        if not isinstance(texto, str) or not texto:
            return (None, None)
        t = texto.lower()

        # Faixa: 'NUM a NUM', 'NUM - NUM', 'NUM até NUM', 'entre NUM e NUM'
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:a|até|-|–|—)\s*(\d+(?:[.,]\d+)?)', t)
        if m:
            return (self._parse_num(m.group(1)), self._parse_num(m.group(2)))

        m = re.search(r'entre\s*(\d+(?:[.,]\d+)?)\s*(?:e|a|até)\s*(\d+(?:[.,]\d+)?)', t)
        if m:
            return (self._parse_num(m.group(1)), self._parse_num(m.group(2)))

        # Limite superior: '< NUM', '≤ NUM', 'inferior a NUM'
        m = re.search(r'(?:<\s*|≤\s*|inferior\s*a\s*)(\d+(?:[.,]\d+)?)', t)
        if m:
            return (None, self._parse_num(m.group(1)))

        # Limite inferior: '> NUM', '≥ NUM', 'superior a NUM'
        m = re.search(r'(?:>\s*|≥\s*|superior\s*a\s*)(\d+(?:[.,]\d+)?)', t)
        if m:
            return (self._parse_num(m.group(1)), None)

        return (None, None)

    def _procurar_arquivo_exame(self, id_exame):
        """Devolve o caminho absoluto do ficheiro JSON do exame, ou None."""
        base_dir = get_base_path()
        pasta = os.path.join(base_dir, "exames_internos")
        if not os.path.isdir(pasta):
            return None

        alvo = self._normalizar_token(id_exame)
        if not alvo:
            return None

        try:
            for nome in os.listdir(pasta):
                if not nome.lower().endswith(('.json', '.jsonux')):
                    continue
                stem = os.path.splitext(nome)[0]
                if self._normalizar_token(stem) == alvo:
                    return os.path.join(pasta, nome)
        except OSError:
            return None
        return None

    def _carregar_refs_exame(self, id_exame):
        """Localiza o ficheiro JSON do exame e devolve (ref_min, ref_max).

        Estratégia:
          1. Localiza o arquivo (ver _procurar_arquivo_exame).
          2. Tenta ler 'ref_min' e 'ref_max' explícitos do JSON.
          3. Se ausentes, aplica fallback por regex sobre os campos textuais.
        Devolve sempre (ref_min, ref_max) com floats ou None.
        """
        caminho = self._procurar_arquivo_exame(id_exame)
        if not caminho:
            return (None, None)

        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
        except OSError:
            return (None, None)

        try:
            dados = json.loads(conteudo)
        except json.JSONDecodeError:
            dados = None

        # 1) Chaves explícitas
        ref_min = ref_max = None
        if isinstance(dados, dict):
            if 'ref_min' in dados or 'ref_max' in dados:
                ref_min = self._coerce_float(dados.get('ref_min'))
                ref_max = self._coerce_float(dados.get('ref_max'))
                return (ref_min, ref_max)

        # 2) Fallback por regex sobre todo o texto do ficheiro
        return self._extrair_refs_por_regex(conteudo)

    def _carregar_bandas_exame(self, id_exame):
        """Lê as faixas personalizadas ('bandas') do JSON, normalizadas como lista de dicts:
        {'valor_max': float|None, 'inclusivo': bool, 'rotulo': str}, ou None se não houverem.

        Cada banda representa um intervalo semiaberto/fechado até 'valor_max'
        (inclusivo=True -> valor ≤ valor_max; inclusivo=False -> valor < valor_max).
        A última banda com 'valor_max' nulo cobre todo o resto acima.
        """
        caminho = self._procurar_arquivo_exame(id_exame)
        if not caminho:
            return None
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
        except OSError:
            return None
        try:
            dados = json.loads(conteudo)
        except json.JSONDecodeError:
            return None
        if not isinstance(dados, dict) or not isinstance(dados.get('bandas'), list):
            return None

        lista = []
        for b in dados['bandas'] if isinstance(dados.get('bandas'), list) else []:
            if not isinstance(b, dict):
                continue
            lista.append({
                'valor_max': self._coerce_float(b.get('valor_max')),
                'inclusivo': bool(b.get('inclusivo', True)),
                'rotulo': (b.get('rotulo') or b.get('rotulo_tecnico') or b.get('classificacao_simplificada') or 'Sem referência'),
            })
        return lista or None

    def _classificar_valor(self, valor, ref_min=None, ref_max=None, bandas=None):
        """Devolve rótulo clínico (faixa personalizada) ou 'Baixo'/'Normal'/'Alto'/'Sem referência'.

        Se 'bandas' (faixas personalizadas do JSON) estiverem disponíveis, usa-as primeiro —
        cada banda usa 'valor_max' (teto do intervalo) e rótulo textual próprio (ex.:
        'Hipoglicemia', 'Risco de pré-diabetes', 'Desejável' etc.), permitindo laudos
        personalizados em vez de forçar apenas Alto/Baixo/Normal.
        """
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            return "Sem referência"

        # 1ª via: faixas personalizadas do JSON
        if bandas:
            for banda in bandas:
                valor_max = banda.get('valor_max')
                rotulo = banda.get('rotulo') or "Sem referência"
                if valor_max is None:
                    return rotulo
                if banda.get('inclusivo', True):
                    if valor <= valor_max:
                        return rotulo
                else:
                    if valor < valor_max:
                        return rotulo
            return "Sem referência"

        # 2ª via (fallback histórico): ref_min / ref_max
        try:
            ref_min_f = float(ref_min) if ref_min is not None else None
        except (TypeError, ValueError):
            ref_min_f = None
        try:
            ref_max_f = float(ref_max) if ref_max is not None else None
        except (TypeError, ValueError):
            ref_max_f = None

        if ref_min_f is None and ref_max_f is None:
            return "Sem referência"
        if ref_min_f is not None and valor < ref_min_f:
            return "Baixo"
        if ref_max_f is not None and valor > ref_max_f:
            return "Alto"
        return "Normal"

    def _cor_status(self, status):
        """Escolhe a cor da label conforme o rótulo clínico do laudo."""
        s = (status or "").lower()
        if "sem referência" in s:
            return "#556b58"
        if any(k in s for k in ("normal", "desejável", "desejav", "adequado", "ótimo", "otimo", "protetor", "proteção")):
            return "#2e7d32"
        if any(k in s for k in ("limítrofe", "limitrofe", "risco", "pré-diabetes", "pré-diabete", "indica")):
            return "#ef6c00"
        return "#c62828"

    def _avaliar_entry_resultado(self, entry, lbl_status, id_exame):
        """Callback do <KeyRelease>: lê o valor, classifica e atualiza a label."""
        texto = entry.get().strip().replace(',', '.')
        if not texto:
            lbl_status.configure(text="")
            return
        try:
            valor = float(texto)
        except ValueError:
            lbl_status.configure(text="Valor inválido", text_color="#ef6c00")
            return
        ref_min, ref_max = self._carregar_refs_exame(id_exame)
        bandas = self._carregar_bandas_exame(id_exame)
        status = self._classificar_valor(valor, ref_min, ref_max, bandas)
        lbl_status.configure(text=status, text_color=self._cor_status(status))

    def _recalcular_indices_dinamicos(self):
        """Recalcula e atualiza os índices metabólicos dinâmicos na tela de resultados.

        Verifica se os pares de exames necessários estão presentes e preenchidos
        na tela atual (self._entries_resultados). Se sim, mostra/atualiza eles;
        se faltam, oculta os labels correspondentes.
        """
        try:
            entries = getattr(self, '_entries_resultados', {})
            if not entries:
                return

            # DEBUG: verifica as chaves (id_exame) atuais na interface
            print(f"[DEBUG calculo] Chaves ativas na interface: {list(entries.keys())}")

            def _buscar_valor(*possibles):
                """Busca flexible: prueba IDs exactos y luego substring en las keys reales."""
                # 1) Intentar IDs exactos directamente
                for pid in possibles:
                    par = entries.get(pid)
                    if par:
                        entry = par[0]
                        texto = entry.get().strip().replace(',', '.')
                        if texto:
                            try:
                                return float(texto)
                            except ValueError:
                                pass
                # 2) Fallback: substring flexible sobre todas las keys reales
                keys_upper = {k.upper(): k for k in entries.keys()}
                for needle in possibles:
                    nu = (needle or '').upper()
                    for ku, kv in keys_upper.items():
                        if nu in ku or ku in nu:
                            par = entries.get(kv)
                            if par:
                                entry = par[0]
                                texto = entry.get().strip().replace(',', '.')
                                if texto:
                                    try:
                                        return float(texto)
                                    except ValueError:
                                        pass
                return None

            # --- 1. Índice de De Ritis (TGO / TGP) ---
            tgo = _buscar_valor("EXM-AST-TGO", "EXM-TGO", "EXM-AST", "AST", "TGO")
            tgp = _buscar_valor("EXM-ALT-TGP", "EXM-TGP", "EXM-ALT", "ALT", "TGP")
            self._atualizar_label_indice(
                "de_ritis", tgo, tgp, tgo / tgp if (tgo and tgp) else None,
                self._interpretar_de_ritis,
                "Uprota Índice de De Ritis (TGO/TGP): {valor:.2f} | {interp}",
                "TGO (AST) e TGP (ALT) preenchidos para calcular o índice de De Ritis. Limpe um para ocultar.",
            )

            # --- 2. Relação TG / HDL ---
            tg  = _buscar_valor("EXM-TRIGLICERIDEOS", "TRIGLICERIDEOS", "TG", "TRIGLICERIDES")
            hdl = _buscar_valor("EXM-HDL-COLESTEROL", "HDL-COLESTEROL", "HDL")
            self._atualizar_label_indice(
                "tg_hdl", tg, hdl, tg / hdl if (tg and hdl) else None,
                self._interpretar_tg_hdl,
                "Uprota Relação TG/HDL: {valor:.2f} | {interp}",
                "Triglicerídeos e HDL preenchidos para calcular a relação TG/HDL. Limpe um para ocultar.",
            )

            # --- 3. Fração Aterogênica (Não-HDL / Total) ---
            total = _buscar_valor("EXM-COLESTEROL-TOTAL", "COLESTEROL-TOTAL", "COLESTEROLTOTAL", "Colesterol Total")
            hdl2  = _buscar_valor("EXM-HDL-COLESTEROL", "HDL-COLESTEROL", "HDL", "HDL-COLESTEROL")
            nao_hdl_pct = ((total - hdl2) / total * 100) if (total and hdl2) else None
            self._atualizar_label_indice(
                "fracao_atero", total, hdl2, nao_hdl_pct,
                self._interpretar_fracao_atero,
                "Uprota Fração Aterogênica (Não-HDL/Total): {valor:.1f}% | {interp}",
                "Colesterol Total e HDL preenchidos para calcular a fração aterogênica. Limpe um para ocultar.",
            )

            # --- 4. Razão Apo B / Apo A-1 ---
            apo_b = _buscar_valor("EXM-APOLIPOPROTEINA-B", "APOLIPOPROTEINA-B", "EXM-APO-B", "APO-B", "Apo B", "APOLIPOPROTEINA B")
            apo_a = _buscar_valor("EXM-APO-A1", "APO-A1", "Apo A-1", "APOLIPOPROTEINA A-1")
            self._atualizar_label_indice(
                "apo_b_apo_a", apo_b, apo_a, apo_b / apo_a if (apo_b and apo_a) else None,
                lambda v: self._interpretar_apo_ratio(v),
                "Uprota Razão Apo B / Apo A-1: {valor:.2f} | {interp}",
                "Apolipoproteína B e A-1 preenchidas para calcular a razão. Limpe uma para ocultar.",
            )
        except Exception as e:
            print(f"[ERRO CRÍTICO CALCULADORA]: {e}")

    def _atualizar_label_indice(self, chave, val_a, val_b, valor_calc, interp_fn, fmt_str, empty_msg):
        """Mostra/oculta/atualiza un label dinámico de índice en pantalla."""
        if val_a is None or val_b is None or valor_calc is None:
            self._limpar_label_indice(chave)
            return
        try:
            valor = float(valor_calc)
        except (TypeError, ValueError):
            self._limpar_label_indice(chave)
            return
        interp = interp_fn(valor)
        texto = fmt_str.format(valor=valor, interp=interp)
        label = self._labels_calculo.get(chave)
        if label is None:
            label = ctk.CTkLabel(self._frame_indices, text=texto, font=ctk.CTkFont(size=14, weight="bold"),
                                 text_color="#1565c0", justify="left")
            label.pack(anchor="w", pady=(6, 2))
            self._labels_calculo[chave] = label
        else:
            label.configure(text=texto)

    def _limpar_label_indice(self, chave):
        """Remove un label dinámico cuando el par deja de estar completo."""
        label = self._labels_calculo.pop(chave, None)
        if label and label.winfo_exists():
            label.destroy()

    @staticmethod
    def _interpretar_de_ritis(valor):
        if valor < 1.0:
            return "Agressão hepatocelular inicial ou esteatose hepática."
        elif valor <= 2.0:
            return "Evolução para fibrose/cirrose hepática crônica."
        else:
            return "Achado altamente específico para hepatite alcoólica."

    @staticmethod
    def _interpretar_tg_hdl(valor):
        if valor > 2.5:
            return "Dislipidemia aterogênica / forte resistência à insulina / síndrome metabólica."
        else:
            return "Dentro do esperado."

    @staticmethod
    def _interpretar_fracao_atero(valor):
        if valor < 30:
            return "Baixa porcentagem de colesterol aterogênico."
        elif valor < 50:
            return "Intermediária."
        else:
            return "Alta porcentagem aterogênica — maior risco cardiovascular."

    @staticmethod
    def _interpretar_apo_ratio(valor):
        return "Consulte a tabela de Wallach (Homens: 0.4 ↓ risco / 1.6 ↑ risco; Mulheres: 0.3 ↓ risco / 1.5 ↑ risco)."

    def abrir_modal_resultados(self):
        if not self.exames_selecionados_lista:
            ctk.CTkLabel(self.area_principal, text="")  # noop (mantém referência)
            # Mensagem simples via lbl_msg_consulta se existir
            if hasattr(self, 'lbl_msg_consulta') and self.lbl_msg_consulta.winfo_exists():
                self.lbl_msg_consulta.configure(text="Adicione exames à solicitação antes de lançar resultados.", text_color="#ef6c00")
            return

        modal = ctk.CTkToplevel(self)
        modal.geometry("600x500")
        modal.title("Lançar Resultados Laboratoriais")
        modal.attributes("-topmost", True)

        ctk.CTkLabel(modal, text="Lançamento de Resultados", font=ctk.CTkFont(size=20, weight="bold"), text_color="#1b5e20").pack(pady=(10, 5))

        scroll = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Contêiner para os labels dinâmicos de índices metabólicos
        self._labels_calculo = {}
        self._frame_indices = ctk.CTkFrame(scroll, fg_color="transparent")
        self._frame_indices.pack(fill="x", pady=(0, 8))

        # Cache id_exame -> nome_amigavel para reusar labels
        conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
        cursor = conexao.cursor()
        cursor.execute("SELECT id_exame, nome_amigavel FROM Exames_Catalogo")
        mapa_nomes = {row[0]: row[1] for row in cursor.fetchall()}
        conexao.close()

        self._entries_resultados = {}

        for id_exame in self.exames_selecionados_lista:
            linha = ctk.CTkFrame(scroll, fg_color="#ffffff", corner_radius=6, border_width=1, border_color="#c8e6c9")
            linha.pack(fill="x", pady=4, padx=4, ipady=4)

            nome = mapa_nomes.get(id_exame, id_exame)
            ctk.CTkLabel(linha, text=nome, width=200, anchor="w", font=ctk.CTkFont(size=15)).pack(side="left", padx=(10, 5), pady=6)

            entry = ctk.CTkEntry(linha, placeholder_text="Resultado", width=140, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", placeholder_text_color="#7a9e7e", border_color="#a5d6a7")
            entry.pack(side="left", padx=5, pady=6)

            lbl_status = ctk.CTkLabel(linha, text="", width=120, anchor="w", font=ctk.CTkFont(size=15))
            lbl_status.pack(side="left", padx=5, pady=6)

            self._entries_resultados[id_exame] = (entry, lbl_status)

            # Gatilho de status individual: actualiza ao perder o foco (FocusOut)
            entry.bind('<FocusOut>', lambda e, ent=entry, lbl=lbl_status, ex=id_exame: self._avaliar_entry_resultado(ent, lbl, ex))

            # Pré-preencher se já houver resultado lançado anteriormente
            if id_exame in self.resultados_lancados:
                valor_anterior, _ = self.resultados_lancados[id_exame]
                entry.insert(0, str(valor_anterior))
                self._avaliar_entry_resultado(entry, lbl_status, id_exame)

        # --- Botão manual para calcular os índices metabólicos ---
        ctk.CTkButton(
            scroll,
            text="Calcular Índices Clínicos",
            fg_color="#1565c0",
            hover_color="#0d47a9",
            text_color="#ffffff",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._recalcular_indices_dinamicos
        ).pack(pady=(8, 4), fill="x")

        # --- Container onde os labels dinâmicos de índices aparecerão ---
        self._frame_indices.pack(side="bottom", fill="x", pady=(0, 8))

        def salvar_e_fechar():
            self.resultados_lancados = {}
            for id_exame, (entry, lbl_status) in self._entries_resultados.items():
                texto = entry.get().strip().replace(',', '.')
                if not texto:
                    continue
                try:
                    valor = float(texto)
                except ValueError:
                    continue
                ref_min, ref_max = self._carregar_refs_exame(id_exame)
                bandas = self._carregar_bandas_exame(id_exame)
                status = self._classificar_valor(valor, ref_min, ref_max, bandas)
                self.resultados_lancados[id_exame] = (valor, status)
            # Limpa os labels dinâmicos ao fechar o modal
            self._labels_calculo = {}
            modal.destroy()

        ctk.CTkButton(modal, text="Salvar", fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=16, weight="bold"), command=salvar_e_fechar).pack(pady=(0, 10))

    def listar_arquivos_diretorio(self, diretorio, frame_aba, caixa_texto):
        scroll = ctk.CTkScrollableFrame(frame_aba, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        base_dir = get_base_path()
        caminho_dir = os.path.join(base_dir, diretorio)
        if not os.path.exists(caminho_dir):
            ctk.CTkLabel(scroll, text=f"Pasta '{diretorio}' não encontrada.", font=ctk.CTkFont(size=15)).pack(pady=10)
            return
        arquivos_encontrados = [os.path.join(root, f) for root, dirs, files in os.walk(caminho_dir) for f in files if f.lower().endswith(('.jsonux', '.json'))]
        if not arquivos_encontrados:
            ctk.CTkLabel(scroll, text="A pasta está vazia.", font=ctk.CTkFont(size=15)).pack(pady=10)
            return
        for caminho_completo in arquivos_encontrados:
            nome_arquivo = os.path.basename(caminho_completo)
            nome_amigavel = nome_arquivo.replace('.jsonux', '').replace('.json', '').replace('_', ' ')
            btn = ctk.CTkButton(scroll, text=nome_amigavel, anchor="w", fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=14), command=lambda c=caminho_completo, t=caixa_texto: self.inserir_texto_padrao(c, t))
            btn.pack(fill="x", pady=2, padx=5)

    def inserir_texto_padrao(self, caminho_completo, caixa_texto):
        try:
            with open(caminho_completo, 'r', encoding='utf-8', errors='ignore') as f:
                conteudo = f.read()
                try:
                    dados_json = json.loads(conteudo)
                    def formatar_dict_para_texto(dicionario):
                        linhas = []
                        if isinstance(dicionario, dict):
                            for chave, valor in dicionario.items():
                                if chave.lower() == "id": continue
                                chave_legivel = str(chave).replace("_", " ").capitalize()
                                if isinstance(valor, list):
                                    linhas.append(f"• {chave_legivel}:")
                                    for item in valor: linhas.append(f"  - {item}")
                                elif isinstance(valor, dict):
                                    linhas.append(f"• {chave_legivel}:")
                                else:
                                    linhas.append(f"• {chave_legivel}: {valor}")
                        return "\n".join(linhas)
                    conteudo = formatar_dict_para_texto(dados_json)
                except json.JSONDecodeError: pass
            texto_atual = caixa_texto.get("1.0", "end-1c")
            if texto_atual.strip(): caixa_texto.insert("end", "\n\n" + conteudo)
            else: caixa_texto.insert("end", conteudo)
        except Exception as e: print(f"Erro: {e}")

    def _abrir_select_exame(self):
        """Abre una janela de selección con scroll fluido (CTkScrollableFrame)."""
        modal = ctk.CTkToplevel(self)
        modal.geometry("380x420")
        modal.title("Selecionar Exame")
        modal.attributes("-topmost", True)
        modal.configure(fg_color="#e8f5e9")

        ctk.CTkLabel(modal, text="Selecione un exame do catálogo:", font=ctk.CTkFont(size=15, weight="bold"), text_color="#1b5e20").pack(pady=(10, 5))

        self.entry_filtro_exames = ctk.CTkEntry(modal, placeholder_text="Filtrar por nombre...", font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", placeholder_text_color="#7a9e7e", border_color="#a5d6a7")
        self.entry_filtro_exames.pack(fill="x", padx=15, pady=5)
        self.entry_filtro_exames.bind("<KeyRelease>", lambda e: self._preencher_lista_exames())

        self.scroll_lista_exames = ctk.CTkScrollableFrame(modal, width=340, height=300, fg_color="#f1f8ea", corner_radius=6)
        self.scroll_lista_exames.pack(fill="both", expand=True, padx=15, pady=10)

        self._preencher_lista_exames()

    def _preencher_lista_exames(self):
        """Reconstruye los botones del scroll según el filtro escrito."""
        for widget in self.scroll_lista_exames.winfo_children():
            widget.destroy()
        texto = self.entry_filtro_exames.get().strip().lower()
        opciones = [o for o in self.opcoes_exames if texto in o.lower()] if texto else self.opcoes_exames
        if not opciones:
            ctk.CTkLabel(self.scroll_lista_exames, text="Nenhum exame encontrado.", font=ctk.CTkFont(size=14), text_color="#556b58").pack(pady=20)
            return
        for opcion in opciones:
            ctk.CTkButton(self.scroll_lista_exames, text=opcion, anchor="w", fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=14), command=lambda o=opcion: self._seleccionar_exame(o)).pack(fill="x", padx=5, pady=2)

    def _seleccionar_exame(self, opcion):
        """Guarda la elección y cierra la ventana del selector."""
        self.exame_escolhido = opcion
        self.btn_select_exame.configure(text=opcion)
        try:
            self.scroll_lista_exames.winfo_toplevel().destroy()
        except Exception:
            pass

    def adicionar_exame(self, id_forcado=None, nome_forcado=None):
        if id_forcado and nome_forcado:
            id_exame = id_forcado
            nome_amigavel = nome_forcado
        else:
            escolha = self.exame_escolhido
            if not escolha or escolha == "Nenhum exame encontrado...": return
            id_exame = self.catalogo_exames_dict.get(escolha)
            if not id_exame: return
            nome_amigavel = escolha.split(" (")[0]
        if id_exame in self.exames_selecionados_lista: return
        self.exames_selecionados_lista.append(id_exame)
        ctk.CTkLabel(self.frame_lista_exames, text=f"• {nome_amigavel}", font=ctk.CTkFont(size=15), text_color="#1b5e20").pack(anchor="w", padx=10, pady=2)
        self.exame_escolhido = None
        self.btn_select_exame.configure(text="Seleccionar exame...  ▼")
        self.verificar_regras_inteligentes(id_exame)

    def verificar_regras_inteligentes(self, id_gatilho):
        conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
        cursor = conexao.cursor()
        cursor.execute('''SELECT E.id_exame, E.nome_amigavel FROM Regras_Complementares R
                          JOIN Exames_Catalogo E ON R.exame_sugerido = E.id_exame
                          WHERE R.exame_gatilho = ?''', (id_gatilho,))
        sugestoes = cursor.fetchall()
        conexao.close()
        for sug_id, sug_nome in sugestoes:
            if sug_id not in self.exames_selecionados_lista: self.exibir_sugestao(sug_id, sug_nome)

    def exibir_sugestao(self, sug_id, sug_nome):
        self.frame_sugestoes.pack(fill="x", padx=20, pady=10)
        container = ctk.CTkFrame(self.frame_sugestoes, fg_color="transparent")
        container.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(container, text=f"💡 Sugestão: O exame '{sug_nome}' é complementar à sua solicitação.", text_color="#ffffff", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkButton(container, text="Adicionar", width=80, fg_color="#a5d6a7", hover_color="#81c784", text_color="#1b5e20", font=ctk.CTkFont(size=14, weight="bold"), command=lambda: [self.adicionar_exame(sug_id, sug_nome), container.destroy()]).pack(side="right")

    def _calcular_idade_por_nascimento(self, data_nasc):
        """Calcula a idade exata (anos completos) a partir da data de nascimento."""
        if not data_nasc:
            return None
        texto = str(data_nasc).strip()
        for formato in ('%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d'):
            try:
                nascimento = datetime.strptime(texto, formato).date()
                hoje = datetime.now().date()
                return hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
            except ValueError:
                continue
        return None

    @staticmethod
    def _classificar_imc(imc, idade):
        """Classifica o IMC conforme a faixa etária.

        Idoso (>= 60 anos): < 22.0 Baixo peso | 22.0-27.0 Eutrofia | > 27.0 Sobrepeso
        Adulto (< 60 anos): réguas clássicas da OMS (18.5/25/30/35/40).
        Sem idade informada, aplica-se a régua de adulto (fallback documentado).
        """
        if idade is None:
            idade = 30  # fallback: régua de adulto quando não há data de nascimento
        if idade >= 60:
            if imc < 22.0:
                return "Baixo peso"
            if imc <= 27.0:
                return "Eutrofia"
            return "Sobrepeso"
        if imc < 18.5:
            return "Baixo peso"
        if imc < 25.0:
            return "Eutrofia"
        if imc < 30.0:
            return "Sobrepeso"
        if imc < 35.0:
            return "Obesidade grau I"
        if imc < 40.0:
            return "Obesidade grau II"
        return "Obesidade grau III"

    def _calcular_imc_dinamico(self, *args):
        """Gatilho <KeyRelease> dos entries de Peso/Altura: calcula IMC em tempo real."""
        try:
            peso_str = self.entry_peso.get().strip().replace(',', '.')
            altura_str = self.entry_altura.get().strip().replace(',', '.')
            if not peso_str or not altura_str:
                self.lbl_imc.configure(text="IMC: -- kg/m²", text_color="#556b58")
                return
            peso = float(peso_str)
            altura = float(altura_str)
            if peso <= 0 or altura <= 0:
                raise ZeroDivisionError("peso/altura devem ser maiores que zero")
            imc = peso / (altura ** 2)
            idade = self._calcular_idade_por_nascimento(getattr(self, 'paciente_atual_nasc', ''))
            classificacao = self._classificar_imc(imc, idade)
            sufixo_idade = f" (≥60 anos - régua idoso)" if (idade is not None and idade >= 60) else ""
            self.lbl_imc.configure(
                text=f"IMC: {imc:.1f} kg/m² — {classificacao}{sufixo_idade}",
                text_color="#1b5e20"
            )
        except (ValueError, ZeroDivisionError):
            self.lbl_imc.configure(text="IMC: -- kg/m²", text_color="#556b58")
        except Exception as e:
            print(f"[ERRO CRÍTICO IMC]: {e}")
            self.lbl_imc.configure(text="IMC: -- kg/m²", text_color="#556b58")

    def _calcular_indices_para_pdf(self, valores):
        """Recebe {NOME_EXAME: valor} e retorna as linhas de laudo dos pares clínicos.

        Usa a mesma lógica matemática e os mesmos interpretadores da calculadora
        da tela de resultados (_interpretar_*), garantindo consistência.
        """
        def busca(*chaves):
            for alvo in chaves:
                for chave, valor in valores.items():
                    if alvo in chave:
                        return valor
            return None

        linhas = []
        try:
            # 1) Índice de De Ritis (TGO / TGP)
            tgo = busca("TGO", "AST")
            tgp = busca("TGP", "ALT")
            if tgo and tgp:
                relacao = tgo / tgp
                linhas.append(
                    f"* Índice de De Ritis (TGO/TGP): {relacao:.2f} - "
                    f"{self._interpretar_de_ritis(relacao).replace(chr(8212), '-')}"
                )
            # 2) Relação TG / HDL
            tg = busca("TRIGLIC")
            hdl = busca("HDL")
            if tg and hdl:
                relacao = tg / hdl
                linhas.append(
                    f"* Relação TG/HDL: {relacao:.2f} - "
                    f"{self._interpretar_tg_hdl(relacao).replace(chr(8212), '-')}"
                )
            # 3) Fração Aterogênica (Não-HDL / Total)
            colesterol_total = None
            for chave, valor in valores.items():
                if "COLESTEROL" in chave and "TOTAL" in chave:
                    colesterol_total = valor
                    break
            if colesterol_total and hdl:
                pct = (colesterol_total - hdl) / colesterol_total * 100
                linhas.append(
                    f"* Fração Aterogênica (Não-HDL/Total): {pct:.1f}% - "
                    f"{self._interpretar_fracao_atero(pct).replace(chr(8212), '-')}"
                )
            # 4) Razão Apo B / Apo A-1
            apo_b = busca("APOLIPOPROTEINA B", "APO B", "APO-B")
            apo_a = busca("APOLIPOPROTEINA A", "APO A", "APO-A1", "APO-A")
            if apo_b and apo_a:
                relacao = apo_b / apo_a
                linhas.append(
                    f"* Razão Apo B / Apo A-1: {relacao:.2f} - "
                    f"{self._interpretar_apo_ratio(relacao)}"
                )
        except ZeroDivisionError:
            pass
        except Exception as e:
            print(f"[ERRO CRÍTICO ÍNDICES PDF]: {e}")
        return linhas

    def salvar_consulta(self):
        if not self.paciente_atual_id: return
        anamnese = self.txt_anamnese.get("1.0", "end-1c")
        peso = self.entry_peso.get()
        altura = self.entry_altura.get()
        gordura = self.entry_gordura.get()
        naf = self.entry_naf.get()
        metodo = self.combo_metodo_tmb.get()
        conduta = self.txt_conduta.get("1.0", "end-1c")
        analise_exames = self.txt_analise_exames.get("1.0", "end-1c")

        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
        conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
        cursor = conexao.cursor()
        cursor.execute('''
            INSERT INTO Consultas (id_paciente, data_consulta, anamnese, peso, altura, gordura, conduta, tmb, vet, naf, metodo_tmb, analise_exames)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (self.paciente_atual_id, data_atual, anamnese, peso, altura, gordura, conduta, self.tmb_atual, self.vet_atual, naf, metodo, analise_exames))
        
        id_consulta = cursor.lastrowid
        for id_exame in self.exames_selecionados_lista:
            cursor.execute('INSERT INTO Exames_Solicitados (id_consulta, id_exame) VALUES (?, ?)', (id_consulta, id_exame))
        for id_exame, (valor, status) in self.resultados_lancados.items():
            cursor.execute(
                'INSERT INTO Resultados_Exames (id_consulta, id_exame, valor, status) VALUES (?, ?, ?, ?)',
                (id_consulta, id_exame, valor, status)
            )

        conexao.commit()
        conexao.close()
        self.lbl_msg_consulta.configure(text="Evolução salva com sucesso!")
        self.btn_salvar_evolucao.configure(state="disabled")

    # --- MÓDULO DE EXAMES E REGRAS ---
    def tela_exames(self):
        self.limpar_area_principal()
        
        titulo = ctk.CTkLabel(self.area_principal, text="Catálogo e Regras de Exames", font=ctk.CTkFont(size=24, weight="bold"), text_color="#1b5e20")
        titulo.pack(pady=(20, 10))

        tabview_exames = ctk.CTkTabview(self.area_principal, fg_color="#e8f5e9",
                                        segmented_button_selected_color="#2e7d32", segmented_button_selected_hover_color="#1b5e20",
                                        segmented_button_unselected_color="#558b2f", segmented_button_unselected_hover_color="#689f38",
                                        segmented_button_font=ctk.CTkFont(size=15, weight="bold"),
                                        text_color="#ffffff", text_color_disabled="#d5e8d7")
        tabview_exames.pack(padx=20, pady=10, fill="both", expand=True)

        aba_lista = tabview_exames.add("Lista de Exames")
        aba_regras = tabview_exames.add("Regras Inteligentes")

        # --- ABA 1: LISTA DE EXAMES ---
        frame_add = ctk.CTkFrame(aba_lista, fg_color="transparent")
        frame_add.pack(fill="x", pady=10)
        
        self.entry_id_exame = ctk.CTkEntry(frame_add, placeholder_text="ID (ex: EXM-FERRO)", width=200, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", placeholder_text_color="#7a9e7e", border_color="#a5d6a7")
        self.entry_id_exame.pack(side="left", padx=5)
        
        self.entry_nome_exame = ctk.CTkEntry(frame_add, placeholder_text="Nome do Exame (ex: FERRO SÉRICO)", width=300, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", placeholder_text_color="#7a9e7e", border_color="#a5d6a7")
        self.entry_nome_exame.pack(side="left", padx=5)
        
        ctk.CTkButton(frame_add, text="Adicionar", width=100, fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=15, weight="bold"), command=self.salvar_novo_exame).pack(side="left", padx=10)
        
        self.lbl_msg_exame = ctk.CTkLabel(aba_lista, text="", text_color="#2e7d32", font=ctk.CTkFont(size=15))
        self.lbl_msg_exame.pack()

        style = ttk.Style()
        style.configure("Treeview", background="#ffffff", foreground="#1b5e20", rowheight=34, fieldbackground="#ffffff", borderwidth=0, font=("Segoe UI", 14))
        style.map('Treeview', background=[('selected', '#4caf50')], foreground=[('selected', '#ffffff')])
        style.map("Treeview.Heading", background=[('active', '#388e3c')])
        
        tree_frame = ctk.CTkFrame(aba_lista, fg_color="#e8f5e9")
        tree_frame.pack(fill="both", expand=True, pady=10)

        self.tree_exames = ttk.Treeview(tree_frame, columns=("ID", "Nome"), show="headings", style="Treeview")
        self.tree_exames.heading("ID", text="ID do Exame")
        self.tree_exames.heading("Nome", text="Nome Amigável")
        self.tree_exames.column("ID", width=200, anchor="center")
        self.tree_exames.column("Nome", width=400)
        self.tree_exames.pack(side="left", fill="both", expand=True)
        
        scroll_exm = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_exames.yview)
        self.tree_exames.configure(yscrollcommand=scroll_exm.set)
        scroll_exm.pack(side="right", fill="y")
        
        self.carregar_tabela_exames()

        # --- ABA 2: REGRAS INTELIGENTES ---
        ctk.CTkLabel(aba_regras, text="Selecione um exame GATILHO que, quando solicitado, sugerirá o exame COMPLEMENTAR automaticamente.", wraplength=600, font=ctk.CTkFont(size=15), text_color="#2f3e33").pack(pady=10)
        
        frame_regras = ctk.CTkFrame(aba_regras, fg_color="transparent")
        frame_regras.pack(pady=20)
        
        conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
        cursor = conexao.cursor()
        cursor.execute("SELECT id_exame, nome_amigavel FROM Exames_Catalogo ORDER BY nome_amigavel")
        exames_banco = cursor.fetchall()
        conexao.close()
        
        self.lista_exames_regras = [f"{ex[1]} ({ex[0]})" for ex in exames_banco]
        if not self.lista_exames_regras:
            self.lista_exames_regras = ["Nenhum exame cadastrado"]
        
        ctk.CTkLabel(frame_regras, text="Quando solicitar:", font=ctk.CTkFont(size=15), text_color="#1b5e20").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.combo_gatilho = ctk.CTkComboBox(frame_regras, values=self.lista_exames_regras, width=300, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", button_color="#4caf50", button_hover_color="#388e3c", dropdown_fg_color="#ffffff", dropdown_hover_color="#c8e6c9", dropdown_text_color="#1b5e20")
        self.combo_gatilho.grid(row=0, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(frame_regras, text="Sugerir também:", font=ctk.CTkFont(size=15), text_color="#1b5e20").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.combo_sugerido = ctk.CTkComboBox(frame_regras, values=self.lista_exames_regras, width=300, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", button_color="#4caf50", button_hover_color="#388e3c", dropdown_fg_color="#ffffff", dropdown_hover_color="#c8e6c9", dropdown_text_color="#1b5e20")
        self.combo_sugerido.grid(row=1, column=1, padx=10, pady=5)
        
        ctk.CTkButton(frame_regras, text="Criar Regra de Sugestão", fg_color="#4caf50", hover_color="#388e3c", text_color="#ffffff", font=ctk.CTkFont(size=15, weight="bold"), command=self.salvar_nova_regra).grid(row=2, column=0, columnspan=2, pady=20)
        
        self.lbl_msg_regra = ctk.CTkLabel(aba_regras, text="", text_color="#2e7d32", font=ctk.CTkFont(size=15))
        self.lbl_msg_regra.pack()

    def carregar_tabela_exames(self):
        for item in self.tree_exames.get_children():
            self.tree_exames.delete(item)
        conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
        cursor = conexao.cursor()
        cursor.execute("SELECT id_exame, nome_amigavel FROM Exames_Catalogo ORDER BY nome_amigavel")
        linhas = cursor.fetchall()
        conexao.close()
        for linha in linhas:
            self.tree_exames.insert("", "end", values=linha)

    def salvar_novo_exame(self):
        id_exame = self.entry_id_exame.get().strip().upper()
        nome = self.entry_nome_exame.get().strip().upper()
        
        if not id_exame or not nome:
            self.lbl_msg_exame.configure(text="Preencha o ID e o Nome.", text_color="#c62828")
            return
            
        try:
            conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
            cursor = conexao.cursor()
            cursor.execute("INSERT INTO Exames_Catalogo (id_exame, nome_amigavel) VALUES (?, ?)", (id_exame, nome))
            conexao.commit()
            conexao.close()
            
            self.entry_id_exame.delete(0, 'end')
            self.entry_nome_exame.delete(0, 'end')
            self.lbl_msg_exame.configure(text="Exame adicionado com sucesso!", text_color="#2e7d32")
            self.carregar_tabela_exames()
        except sqlite3.IntegrityError:
            self.lbl_msg_exame.configure(text="Erro: Este ID já existe no banco de dados.", text_color="#c62828")

    def salvar_nova_regra(self):
        gatilho_full = self.combo_gatilho.get()
        sugerido_full = self.combo_sugerido.get()
        
        if not gatilho_full or not sugerido_full or gatilho_full == "Nenhum exame cadastrado":
            return
            
        # Extrai os IDs de dentro dos parênteses
        id_gatilho = gatilho_full.split("(")[-1].replace(")", "").strip()
        id_sugerido = sugerido_full.split("(")[-1].replace(")", "").strip()
        
        if id_gatilho == id_sugerido:
            self.lbl_msg_regra.configure(text="Erro: O gatilho e a sugestão não podem ser o mesmo exame.", text_color="#c62828")
            return
            
        conexao = sqlite3.connect(os.path.join(get_base_path(), 'clinica.db'))
        cursor = conexao.cursor()
        
        # Verifica se a regra já existe
        cursor.execute("SELECT 1 FROM Regras_Complementares WHERE exame_gatilho = ? AND exame_sugerido = ?", (id_gatilho, id_sugerido))
        if cursor.fetchone():
            self.lbl_msg_regra.configure(text="Esta regra já existe no sistema.", text_color="#ef6c00")
            conexao.close()
            return
            
        cursor.execute("INSERT INTO Regras_Complementares (exame_gatilho, exame_sugerido) VALUES (?, ?)", (id_gatilho, id_sugerido))
        conexao.commit()
        conexao.close()
        
        self.lbl_msg_regra.configure(text="Regra criada com sucesso! O alerta já está ativo nas consultas.", text_color="#2e7d32")

if __name__ == "__main__":
    app = AppClinica()
    app.mainloop()
