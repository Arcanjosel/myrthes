from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem
from kivy.core.window import Window
from kivy.utils import platform
import sqlite3
import os
from datetime import datetime
import customtkinter as ctk
import tkinter.messagebox as messagebox
import subprocess

class MainScreen(MDScreen):
    pass

class SistemaLojaApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()
        self.dialog = None
        
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Dark"
        return MainScreen()
    
    def on_start(self):
        """Chamado quando o aplicativo inicia"""
        self.carregar_dados()
        
    def carregar_dados(self):
        """Carrega os dados iniciais"""
        self.carregar_clientes()
        self.carregar_produtos()
        self.carregar_pedidos()
    
    def carregar_clientes(self):
        """Carrega lista de clientes"""
        lista = self.root.ids.lista_clientes
        lista.clear_widgets()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome FROM clientes ORDER BY nome')
            for cliente in cursor.fetchall():
                lista.add_widget(OneLineListItem(
                    text=cliente[0],
                    on_release=lambda x, c=cliente[0]: self.mostrar_detalhes_cliente(c)
                ))
    
    def carregar_produtos(self):
        """Carrega lista de produtos"""
        lista = self.root.ids.lista_produtos
        lista.clear_widgets()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome, preco FROM produtos ORDER BY nome')
            for produto in cursor.fetchall():
                lista.add_widget(OneLineListItem(
                    text=f"{produto[0]} - R$ {produto[1]:.2f}",
                    on_release=lambda x, p=produto[0]: self.mostrar_detalhes_produto(p)
                ))
    
    def carregar_pedidos(self):
        """Carrega lista de pedidos"""
        lista = self.root.ids.lista_pedidos
        lista.clear_widgets()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, cliente_nome, total, status 
                FROM pedidos 
                ORDER BY data DESC
            ''')
            for pedido in cursor.fetchall():
                lista.add_widget(OneLineListItem(
                    text=f"Pedido #{pedido[0]} - {pedido[1]} - R$ {pedido[2]:.2f} ({pedido[3]})",
                    on_release=lambda x, p=pedido[0]: self.mostrar_detalhes_pedido(p)
                ))
    
    def mostrar_notificacao(self, titulo, mensagem):
        """Mostra notificação nativa"""
        if platform == 'android':
            from plyer import notification
            notification.notify(
                title=titulo,
                message=mensagem,
                app_icon=None,
                timeout=10
            )
        else:
            if not self.dialog:
                self.dialog = MDDialog(
                    title=titulo,
                    text=mensagem,
                    buttons=[
                        MDRaisedButton(
                            text="OK",
                            on_release=lambda x: self.dialog.dismiss()
                        )
                    ]
                )
            self.dialog.open()

    def abrir_janela_debug(self):
        """Abre a janela de debug do sistema"""
        # Criar janela de debug
        janela_debug = ctk.CTkToplevel(self.janela)
        janela_debug.title("🛠️ Menu de Debug")
        janela_debug.geometry("400x500")
        
        # Centralizar janela
        largura = janela_debug.winfo_screenwidth()
        altura = janela_debug.winfo_screenheight()
        x = (largura - 400) // 2
        y = (altura - 500) // 2
        janela_debug.geometry(f"400x500+{x}+{y}")
        
        # Frame principal
        frame_principal = ctk.CTkFrame(janela_debug)
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(
            frame_principal,
            text="Menu de Debug",
            font=("OpenSans", 20, "bold")
        ).pack(pady=(20, 30))
        
        # Frame para botões
        frame_botoes = ctk.CTkFrame(frame_principal)
        frame_botoes.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Botões de teste
        botoes = [
            ("🔔 Testar Notificações", self.testar_notificacao),
            ("🗃️ Resetar Banco de Dados", self.resetar_banco_dados),
            ("🧹 Limpar Todos os Pedidos", self.deletar_todos_os_pedidos),
            ("📊 Ver Estatísticas", self.ver_estatisticas),
            ("💾 Backup do Banco", self.fazer_backup),
            ("🔄 Atualizar Datas", self.atualizar_formato_datas)
        ]
        
        for texto, comando in botoes:
            btn = ctk.CTkButton(
                frame_botoes,
                text=texto,
                command=comando,
                width=300,
                height=40,
                font=("OpenSans", 14)
            )
            btn.pack(pady=10)
        
        # Versão do sistema
        ctk.CTkLabel(
            frame_principal,
            text="Versão do Sistema: 1.0.0",
            font=("OpenSans", 12)
        ).pack(side="bottom", pady=20)

    def resetar_banco_dados(self):
        """Reseta o banco de dados para o estado inicial"""
        if messagebox.askyesno(
            "⚠️ Confirmação",
            "Tem certeza que deseja resetar o banco de dados?\nTodos os dados serão perdidos!"
        ):
            try:
                # Fazer backup antes de resetar
                self.fazer_backup()
                
                # Deletar banco atual
                if os.path.exists(self.db.db_path):
                    os.remove(self.db.db_path)
                
                # Recriar banco
                self.criar_banco_dados()
                
                # Recarregar dados
                self.carregar_pedidos()
                self.atualizar_lista_clientes()
                self.atualizar_lista_produtos()
                
                messagebox.showinfo(
                    "Sucesso",
                    "Banco de dados resetado com sucesso!\nUm backup foi criado antes da operação."
                )
            except Exception as e:
                messagebox.showerror(
                    "Erro",
                    f"Erro ao resetar banco de dados: {str(e)}"
                )

    def ver_estatisticas(self):
        """Mostra estatísticas do sistema"""
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Buscar estatísticas
            stats = {
                "Total de Clientes": cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0],
                "Total de Produtos": cursor.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
                "Total de Pedidos": cursor.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
                "Pedidos Pendentes": cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status='pendente'").fetchone()[0],
                "Valor Total de Pedidos": cursor.execute("SELECT SUM(total) FROM pedidos").fetchone()[0] or 0,
                "Média por Pedido": cursor.execute("SELECT AVG(total) FROM pedidos").fetchone()[0] or 0
            }
            
            # Criar janela de estatísticas
            janela_stats = ctk.CTkToplevel(self.janela)
            janela_stats.title("📊 Estatísticas do Sistema")
            janela_stats.geometry("400x400")
            
            # Frame principal
            frame = ctk.CTkFrame(janela_stats)
            frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Título
            ctk.CTkLabel(
                frame,
                text="Estatísticas do Sistema",
                font=("OpenSans", 18, "bold")
            ).pack(pady=(20, 30))
            
            # Mostrar estatísticas
            for titulo, valor in stats.items():
                frame_linha = ctk.CTkFrame(frame, fg_color="transparent")
                frame_linha.pack(fill="x", pady=5)
                
                ctk.CTkLabel(
                    frame_linha,
                    text=f"{titulo}:",
                    font=("OpenSans", 14, "bold"),
                    width=200
                ).pack(side="left")
                
                valor_formatado = f"R$ {valor:.2f}" if "Valor" in titulo or "Média" in titulo else valor
                ctk.CTkLabel(
                    frame_linha,
                    text=str(valor_formatado),
                    font=("OpenSans", 14)
                ).pack(side="right")

    def fazer_backup(self):
        """Realiza backup do banco de dados"""
        try:
            # Criar pasta de backup se não existir
            if not os.path.exists("backup"):
                os.makedirs("backup")
            
            # Nome do arquivo de backup com data e hora
            data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup/sistema_loja_{data_hora}.db"
            
            # Copiar arquivo do banco
            import shutil
            shutil.copy2(self.db.db_path, backup_path)
            
            messagebox.showinfo(
                "Sucesso",
                f"Backup realizado com sucesso!\nArquivo: {backup_path}"
            )
            return True
        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Erro ao realizar backup: {str(e)}"
            )
            return False

    def abrir_formulario_cliente(self):
        """Abre o formulário para cadastro de novo cliente"""
        # Criar janela do formulário
        janela_form = ctk.CTkToplevel(self.janela)
        janela_form.title("Novo Cliente")
        janela_form.geometry("500x400")
        
        # Centralizar janela
        largura = janela_form.winfo_screenwidth()
        altura = janela_form.winfo_screenheight()
        x = (largura - 500) // 2
        y = (altura - 400) // 2
        janela_form.geometry(f"500x400+{x}+{y}")
        
        # Frame principal com padding e cantos arredondados
        frame_principal = ctk.CTkFrame(janela_form, corner_radius=15)
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(
            frame_principal,
            text="Cadastro de Cliente",
            font=("OpenSans", 20, "bold")
        ).pack(pady=(20, 30))
        
        # Frame para os campos
        frame_campos = ctk.CTkFrame(frame_principal, fg_color="transparent")
        frame_campos.pack(fill="both", expand=True, padx=30)
        
        # Campos do formulário
        campos = {
            "Nome": "",
            "Telefone": "",
            "Endereço": ""
        }
        
        entries = {}
        for label, valor in campos.items():
            frame_campo = ctk.CTkFrame(frame_campos, fg_color="transparent")
            frame_campo.pack(fill="x", pady=10)
            
            ctk.CTkLabel(
                frame_campo,
                text=f"{label}:",
                font=("OpenSans", 14),
                width=100
            ).pack(side="left")
            
            entry = ctk.CTkEntry(
                frame_campo,
                placeholder_text=f"Digite o {label.lower()}...",
                width=300,
                height=35
            )
            entry.pack(side="left", padx=(10, 0))
            entry.insert(0, valor)
            entries[label.lower()] = entry
        
        # Frame para botões
        frame_botoes = ctk.CTkFrame(frame_principal, fg_color="transparent")
        frame_botoes.pack(fill="x", pady=30)
        
        def salvar_cliente():
            """Função interna para salvar o cliente"""
            nome = entries["nome"].get().strip()
            telefone = entries["telefone"].get().strip()
            endereco = entries["endereço"].get().strip()
            
            if not nome:
                messagebox.showerror("Erro", "O nome do cliente é obrigatório!")
                return
            
            try:
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO clientes (nome, telefone, endereco, data_cadastro)
                        VALUES (?, ?, ?, datetime('now', 'localtime'))
                    ''', (nome, telefone, endereco))
                    conn.commit()
                    
                    messagebox.showinfo("Sucesso", "Cliente cadastrado com sucesso!")
                    self.atualizar_lista_clientes()
                    janela_form.destroy()
                    
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Cliente já cadastrado!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao cadastrar cliente: {str(e)}")
        
        # Botões
        ctk.CTkButton(
            frame_botoes,
            text="Cancelar",
            command=janela_form.destroy,
            width=100,
            height=35,
            fg_color="#FF5555",
            hover_color="#FF0000"
        ).pack(side="left", padx=30)
        
        ctk.CTkButton(
            frame_botoes,
            text="Salvar",
            command=salvar_cliente,
            width=100,
            height=35,
            fg_color="#4CAF50",
            hover_color="#45A049"
        ).pack(side="right", padx=30)

    def abrir_formulario_pedido(self):
        """Abre o formulário para criar novo pedido"""
        # Criar janela do formulário
        janela_form = ctk.CTkToplevel(self.janela)
        janela_form.title("Novo Pedido")
        janela_form.geometry("800x600")
        
        # Centralizar janela
        largura = janela_form.winfo_screenwidth()
        altura = janela_form.winfo_screenheight()
        x = (largura - 800) // 2
        y = (altura - 600) // 2
        janela_form.geometry(f"800x600+{x}+{y}")
        
        # Frame principal
        frame_principal = ctk.CTkFrame(janela_form)
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(
            frame_principal,
            text="Novo Pedido",
            font=("OpenSans", 20, "bold")
        ).pack(pady=(20, 30))
        
        # Frame superior para cliente e data
        frame_superior = ctk.CTkFrame(frame_principal)
        frame_superior.pack(fill="x", padx=20, pady=(0, 20))
        
        # Seleção de cliente
        frame_cliente = ctk.CTkFrame(frame_superior, fg_color="transparent")
        frame_cliente.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            frame_cliente,
            text="Cliente:",
            font=("OpenSans", 14)
        ).pack(side="left", padx=(0, 10))
        
        # Buscar lista de clientes
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome FROM clientes ORDER BY nome')
            clientes = ["Selecione um cliente..."] + [row[0] for row in cursor.fetchall()]
        
        janela_form.combo_clientes = ctk.CTkOptionMenu(
            frame_cliente,
            values=clientes,
            width=300,
            height=35
        )
        janela_form.combo_clientes.pack(side="left")
        janela_form.combo_clientes.set("Selecione um cliente...")
        
        # Data de entrega
        frame_data = ctk.CTkFrame(frame_superior, fg_color="transparent")
        frame_data.pack(side="right", padx=(20, 0))
        
        ctk.CTkLabel(
            frame_data,
            text="Data de Entrega:",
            font=("OpenSans", 14)
        ).pack(side="left", padx=(0, 10))
        
        janela_form.entry_data_entrega = ctk.CTkEntry(
            frame_data,
            width=150,
            height=35,
            placeholder_text="dd/mm/aaaa"
        )
        janela_form.entry_data_entrega.pack(side="left")
        
        # Botão calendário
        btn_calendario = ctk.CTkButton(
            frame_data,
            text="📅",
            width=35,
            height=35,
            command=lambda: self.mostrar_calendario(janela_form.entry_data_entrega)
        )
        btn_calendario.pack(side="left", padx=(5, 0))
        
        # Frame para adicionar produtos
        frame_produtos = ctk.CTkFrame(frame_principal)
        frame_produtos.pack(fill="x", padx=20, pady=(0, 20))
        
        # Seleção de produto
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome FROM produtos ORDER BY nome')
            produtos = ["Selecione um produto..."] + [row[0] for row in cursor.fetchall()]
        
        janela_form.combo_produtos = ctk.CTkOptionMenu(
            frame_produtos,
            values=produtos,
            width=300,
            height=35
        )
        janela_form.combo_produtos.pack(side="left", padx=(0, 10))
        janela_form.combo_produtos.set("Selecione um produto...")
        
        # Quantidade
        ctk.CTkLabel(
            frame_produtos,
            text="Qtd:",
            font=("OpenSans", 14)
        ).pack(side="left", padx=(10, 5))
        
        janela_form.entry_quantidade = ctk.CTkEntry(
            frame_produtos,
            width=70,
            height=35
        )
        janela_form.entry_quantidade.pack(side="left")
        janela_form.entry_quantidade.insert(0, "1")
        
        # Botão adicionar
        btn_adicionar = ctk.CTkButton(
            frame_produtos,
            text="➕ Adicionar",
            width=100,
            height=35,
            command=lambda: self.adicionar_ao_pedido(janela_form)
        )
        btn_adicionar.pack(side="right")
        
        # Lista de itens
        frame_lista = ctk.CTkFrame(frame_principal)
        frame_lista.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Criar Treeview para itens
        colunas = ("Produto", "Quantidade", "Valor Unit.", "Total")
        janela_form.lista_itens = ttk.Treeview(
            frame_lista,
            columns=colunas,
            show="headings",
            height=10
        )
        
        # Configurar colunas
        for coluna in colunas:
            janela_form.lista_itens.heading(coluna, text=coluna)
            janela_form.lista_itens.column(coluna, width=150)
        
        janela_form.lista_itens.pack(fill="both", expand=True, pady=10)
        
        # Frame inferior
        frame_inferior = ctk.CTkFrame(frame_principal, fg_color="transparent")
        frame_inferior.pack(fill="x", padx=20)
        
        # Total
        janela_form.label_total = ctk.CTkLabel(
            frame_inferior,
            text="Total: R$ 0,00",
            font=("OpenSans", 16, "bold")
        )
        janela_form.label_total.pack(side="left")
        
        # Botões
        frame_botoes = ctk.CTkFrame(frame_inferior, fg_color="transparent")
        frame_botoes.pack(side="right")
        
        btn_cancelar = ctk.CTkButton(
            frame_botoes,
            text="Cancelar",
            width=100,
            height=35,
            fg_color="#FF5555",
            hover_color="#FF0000",
            command=janela_form.destroy
        )
        btn_cancelar.pack(side="left", padx=5)
        
        btn_finalizar = ctk.CTkButton(
            frame_botoes,
            text="Finalizar Pedido",
            width=150,
            height=35,
            fg_color="#4CAF50",
            hover_color="#45A049",
            command=lambda: self.finalizar_pedido(janela_form)
        )
        btn_finalizar.pack(side="left", padx=5)

    def editar_cliente(self, nome):
        """Abre formulário para editar cliente existente"""
        # Buscar dados do cliente
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM clientes WHERE nome = ?', (nome,))
            cliente = cursor.fetchone()
            
            if not cliente:
                messagebox.showerror("Erro", "Cliente não encontrado!")
                return
        
        # Criar janela do formulário
        janela_form = ctk.CTkToplevel(self.janela)
        janela_form.title("Editar Cliente")
        janela_form.geometry("500x400")
        
        # Centralizar janela
        largura = janela_form.winfo_screenwidth()
        altura = janela_form.winfo_screenheight()
        x = (largura - 500) // 2
        y = (altura - 400) // 2
        janela_form.geometry(f"500x400+{x}+{y}")
        
        # Frame principal
        frame_principal = ctk.CTkFrame(janela_form)
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(
            frame_principal,
            text="Editar Cliente",
            font=("OpenSans", 20, "bold")
        ).pack(pady=(20, 30))
        
        # Frame para campos
        frame_campos = ctk.CTkFrame(frame_principal, fg_color="transparent")
        frame_campos.pack(fill="both", expand=True, padx=30)
        
        # Campos do formulário
        campos = {
            "Nome": cliente[1],
            "Telefone": cliente[2] or "",
            "Endereço": cliente[3] or ""
        }
        
        entries = {}
        for label, valor in campos.items():
            frame_campo = ctk.CTkFrame(frame_campos, fg_color="transparent")
            frame_campo.pack(fill="x", pady=10)
            
            ctk.CTkLabel(
                frame_campo,
                text=f"{label}:",
                font=("OpenSans", 14),
                width=100
            ).pack(side="left")
            
            entry = ctk.CTkEntry(
                frame_campo,
                width=300,
                height=35
            )
            entry.pack(side="left", padx=(10, 0))
            entry.insert(0, valor)
            entries[label.lower()] = entry
        
        def salvar_alteracoes():
            """Função interna para salvar alterações"""
            novo_nome = entries["nome"].get().strip()
            telefone = entries["telefone"].get().strip()
            endereco = entries["endereço"].get().strip()
            
            if not novo_nome:
                messagebox.showerror("Erro", "O nome do cliente é obrigatório!")
                return
            
            try:
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    if novo_nome != nome:
                        # Verificar se novo nome já existe
                        cursor.execute('SELECT id FROM clientes WHERE nome = ?', (novo_nome,))
                        if cursor.fetchone():
                            messagebox.showerror("Erro", "Já existe um cliente com este nome!")
                            return
                    
                    cursor.execute('''
                        UPDATE clientes 
                        SET nome = ?, telefone = ?, endereco = ?
                        WHERE nome = ?
                    ''', (novo_nome, telefone, endereco, nome))
                    conn.commit()
                    
                    messagebox.showinfo("Sucesso", "Cliente atualizado com sucesso!")
                    self.atualizar_lista_clientes()
                    janela_form.destroy()
                    
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao atualizar cliente: {str(e)}")
        
        # Frame para botões
        frame_botoes = ctk.CTkFrame(frame_principal, fg_color="transparent")
        frame_botoes.pack(fill="x", pady=30)
        
        # Botões
        ctk.CTkButton(
            frame_botoes,
            text="Cancelar",
            command=janela_form.destroy,
            width=100,
            height=35,
            fg_color="#FF5555",
            hover_color="#FF0000"
        ).pack(side="left", padx=30)
        
        ctk.CTkButton(
            frame_botoes,
            text="Salvar",
            command=salvar_alteracoes,
            width=100,
            height=35,
            fg_color="#4CAF50",
            hover_color="#45A049"
        ).pack(side="right", padx=30)

    def editar_pedido(self):
        """Abre formulário para editar pedido selecionado"""
        selecionado = self.lista_historico.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um pedido para editar!")
            return
        
        pedido_id = self.lista_historico.item(selecionado[0])["values"][0]
        
        # Buscar dados do pedido
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.cliente_nome, p.data_entrega, p.status, p.total
                FROM pedidos p
                WHERE p.id = ?
            ''', (pedido_id,))
            pedido = cursor.fetchone()
            
            if not pedido:
                messagebox.showerror("Erro", "Pedido não encontrado!")
                return
            
            # Buscar itens do pedido
            cursor.execute('''
                SELECT produto, quantidade, preco_unitario, total
                FROM itens_pedido
                WHERE pedido_id = ?
            ''', (pedido_id,))
            itens = cursor.fetchall()
        
        # Criar janela de edição
        janela_form = ctk.CTkToplevel(self.janela)
        janela_form.title(f"Editar Pedido #{pedido_id}")
        janela_form.geometry("800x600")
        
        # Centralizar janela
        largura = janela_form.winfo_screenwidth()
        altura = janela_form.winfo_screenheight()
        x = (largura - 800) // 2
        y = (altura - 600) // 2
        janela_form.geometry(f"800x600+{x}+{y}")
        
        # Frame principal
        frame_principal = ctk.CTkFrame(janela_form)
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(
            frame_principal,
            text=f"Editar Pedido #{pedido_id}",
            font=("OpenSans", 20, "bold")
        ).pack(pady=(20, 30))
        
        # Frame superior
        frame_superior = ctk.CTkFrame(frame_principal)
        frame_superior.pack(fill="x", padx=20, pady=(0, 20))
        
        # Cliente (somente leitura)
        frame_cliente = ctk.CTkFrame(frame_superior, fg_color="transparent")
        frame_cliente.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            frame_cliente,
            text="Cliente:",
            font=("OpenSans", 14)
        ).pack(side="left", padx=(0, 10))
        
        entry_cliente = ctk.CTkEntry(
            frame_cliente,
            width=300,
            height=35,
            state="readonly"
        )
        entry_cliente.pack(side="left")
        entry_cliente.insert(0, pedido[0])
        
        # Data de entrega
        frame_data = ctk.CTkFrame(frame_superior, fg_color="transparent")
        frame_data.pack(side="right", padx=(20, 0))
        
        ctk.CTkLabel(
            frame_data,
            text="Data de Entrega:",
            font=("OpenSans", 14)
        ).pack(side="left", padx=(0, 10))
        
        entry_data = ctk.CTkEntry(
            frame_data,
            width=150,
            height=35
        )
        entry_data.pack(side="left")
        entry_data.insert(0, datetime.strptime(pedido[1], '%Y-%m-%d').strftime('%d/%m/%Y'))
        
        # Status do pedido
        frame_status = ctk.CTkFrame(frame_principal, fg_color="transparent")
        frame_status.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            frame_status,
            text="Status:",
            font=("OpenSans", 14)
        ).pack(side="left", padx=(0, 10))
        
        combo_status = ctk.CTkOptionMenu(
            frame_status,
            values=["pendente", "entregue", "cancelado"],
            width=200,
            height=35
        )
        combo_status.pack(side="left")
        combo_status.set(pedido[2])
        
        # Lista de itens
        frame_lista = ctk.CTkFrame(frame_principal)
        frame_lista.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        lista_itens = ttk.Treeview(
            frame_lista,
            columns=("Produto", "Quantidade", "Preço Unit.", "Total"),
            show="headings",
            height=10
        )
        
        lista_itens.heading("Produto", text="Produto")
        lista_itens.heading("Quantidade", text="Quantidade")
        lista_itens.heading("Preço Unit.", text="Preço Unit.")
        lista_itens.heading("Total", text="Total")
        
        lista_itens.column("Produto", width=250)
        lista_itens.column("Quantidade", width=100)
        lista_itens.column("Preço Unit.", width=100)
        lista_itens.column("Total", width=100)
        
        for item in itens:
            lista_itens.insert("", "end", values=(
                item[0],
                item[1],
                f"R$ {item[2]:.2f}",
                f"R$ {item[3]:.2f}"
            ))
        
        lista_itens.pack(fill="both", expand=True, padx=5, pady=5)
        
        def salvar_alteracoes():
            """Função interna para salvar alterações do pedido"""
            try:
                nova_data = datetime.strptime(entry_data.get(), '%d/%m/%Y').strftime('%Y-%m-%d')
                novo_status = combo_status.get()
                
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE pedidos 
                        SET data_entrega = ?, status = ?
                        WHERE id = ?
                    ''', (nova_data, novo_status, pedido_id))
                    conn.commit()
                
                messagebox.showinfo("Sucesso", "Pedido atualizado com sucesso!")
                self.carregar_pedidos()
                janela_form.destroy()
                
            except ValueError:
                messagebox.showerror("Erro", "Data inválida! Use o formato dd/mm/aaaa")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao atualizar pedido: {str(e)}")
        
        # Frame para botões
        frame_botoes = ctk.CTkFrame(frame_principal, fg_color="transparent")
        frame_botoes.pack(fill="x", pady=20)
        
        # Botões
        ctk.CTkButton(
            frame_botoes,
            text="Cancelar",
            command=janela_form.destroy,
            width=100,
            height=35,
            fg_color="#FF5555",
            hover_color="#FF0000"
        ).pack(side="left", padx=30)
        
        ctk.CTkButton(
            frame_botoes,
            text="Salvar",
            command=salvar_alteracoes,
            width=100,
            height=35,
            fg_color="#4CAF50",
            hover_color="#45A049"
        ).pack(side="right", padx=30)

    def imprimir_comanda(self, pedido_id):
        """Gera e imprime a comanda do pedido"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar dados do pedido
                cursor.execute('''
                    SELECT p.cliente_nome, p.data, p.data_entrega, p.total, p.status
                    FROM pedidos p
                    WHERE p.id = ?
                ''', (pedido_id,))
                pedido = cursor.fetchone()
                
                # Buscar itens do pedido
                cursor.execute('''
                    SELECT produto, quantidade, preco_unitario, total
                    FROM itens_pedido
                    WHERE pedido_id = ?
                ''', (pedido_id,))
                itens = cursor.fetchall()
                
                if not pedido:
                    messagebox.showerror("Erro", "Pedido não encontrado!")
                    return
                
                # Criar arquivo temporário
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
                
                with open(temp_file.name, 'w', encoding='utf-8') as f:
                    # Cabeçalho
                    f.write("="*40 + "\n")
                    f.write("COMANDA DE PEDIDO".center(40) + "\n")
                    f.write("="*40 + "\n\n")
                    
                    # Dados do pedido
                    f.write(f"Pedido #: {pedido_id}\n")
                    f.write(f"Cliente: {pedido[0]}\n")
                    f.write(f"Data: {datetime.strptime(pedido[1], '%Y-%m-%d').strftime('%d/%m/%Y')}\n")
                    f.write(f"Entrega: {datetime.strptime(pedido[2], '%Y-%m-%d').strftime('%d/%m/%Y')}\n")
                    f.write(f"Status: {pedido[4]}\n")
                    f.write("-"*40 + "\n")
                    
                    # Itens
                    f.write("\nITENS DO PEDIDO:\n")
                    f.write("-"*40 + "\n")
                    for item in itens:
                        f.write(f"{item[0]}\n")
                        f.write(f"  {item[1]} x R$ {item[2]:.2f} = R$ {item[3]:.2f}\n")
                    
                    f.write("-"*40 + "\n")
                    f.write(f"Total: R$ {pedido[3]:.2f}\n")
                    f.write("="*40 + "\n")
                
                # Imprimir arquivo
                if platform == "win32":
                    os.startfile(temp_file.name, "print")
                else:
                    subprocess.run(['lpr', temp_file.name])
                
                messagebox.showinfo("Sucesso", "Comanda enviada para impressão!")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar comanda: {str(e)}")

    def atualizar_combos(self):
        """Atualiza os comboboxes de clientes e produtos"""
        # Atualizar combo de clientes
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Buscar clientes
            cursor.execute('SELECT nome FROM clientes ORDER BY nome')
            clientes = ["Selecione um cliente..."] + [row[0] for row in cursor.fetchall()]
            
            # Buscar produtos
            cursor.execute('SELECT nome FROM produtos ORDER BY nome')
            produtos = ["Selecione um produto..."] + [row[0] for row in cursor.fetchall()]
            
            # Atualizar combos em todas as janelas abertas
            for widget in self.janela.winfo_children():
                if isinstance(widget, ctk.CTkToplevel):
                    for child in widget.winfo_children():
                        if hasattr(child, 'combo_clientes'):
                            child.combo_clientes.configure(values=clientes)
                        if hasattr(child, 'combo_produtos'):
                            child.combo_produtos.configure(values=produtos)

    def filtrar_pedidos(self, event=None):
        """Filtra os pedidos conforme pesquisa e status"""
        termo = self.entry_pesquisa.get().lower()
        status_filtro = self.filtro_status.get().lower()
        
        # Limpar lista atual
        for item in self.lista_historico.get_children():
            self.lista_historico.delete(item)
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Construir query base
                query = '''
                    SELECT id, data, cliente_nome, data_entrega, status, total
                    FROM pedidos
                    WHERE 1=1
                '''
                params = []
                
                # Adicionar filtro de pesquisa
                if termo:
                    query += ' AND (cliente_nome LIKE ? OR id LIKE ?)'
                    params.extend([f'%{termo}%', f'%{termo}%'])
                
                # Adicionar filtro de status
                if status_filtro != "todos":
                    query += ' AND status = ?'
                    params.append(status_filtro)
                
                # Ordenar por data mais recente
                query += ' ORDER BY data DESC'
                
                cursor.execute(query, params)
                pedidos = cursor.fetchall()
                
                for pedido in pedidos:
                    # Formatar data
                    data = datetime.strptime(pedido[1], '%Y-%m-%d').strftime('%d/%m/%Y')
                    data_entrega = datetime.strptime(pedido[3], '%Y-%m-%d').strftime('%d/%m/%Y')
                    
                    self.lista_historico.insert("", "end", values=(
                        pedido[0],
                        data,
                        pedido[2],
                        data_entrega,
                        pedido[4].title(),
                        f"R$ {float(pedido[5]):.2f}"
                    ))
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao filtrar pedidos: {str(e)}")

    def deletar_todos_os_pedidos(self):
        """Remove todos os pedidos e reseta os IDs"""
        if not messagebox.askyesno(
            "Confirmação",
            "⚠️ ATENÇÃO! Esta ação irá remover TODOS os pedidos e resetar os IDs.\n\n" +
            "Tem certeza que deseja continuar?"
        ):
            return
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Remover todos os itens de pedidos
                cursor.execute('DELETE FROM itens_pedido')
                
                # Remover todos os pedidos
                cursor.execute('DELETE FROM pedidos')
                
                # Resetar sequência de IDs
                cursor.execute('DELETE FROM sqlite_sequence WHERE name="pedidos"')
                cursor.execute('DELETE FROM sqlite_sequence WHERE name="itens_pedido"')
                
                conn.commit()
                
                messagebox.showinfo(
                    "Sucesso",
                    "Todos os pedidos foram removidos e os IDs foram resetados!"
                )
                
                # Atualizar interface
                self.carregar_pedidos()
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao remover pedidos: {str(e)}")

    def criar_tooltip(self):
        """Cria o texto do tooltip para o botão de notificações"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar informações de entregas
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN date(data_entrega) < date('now') THEN 1 ELSE 0 END) as atrasados,
                        SUM(CASE WHEN date(data_entrega) = date('now') THEN 1 ELSE 0 END) as hoje,
                        SUM(CASE WHEN date(data_entrega) = date('now', '+1 day') THEN 1 ELSE 0 END) as amanha
                    FROM pedidos 
                    WHERE status = 'pendente'
                    AND data_entrega IS NOT NULL
                ''')
                
                result = cursor.fetchone()
                total = result[0] or 0
                atrasados = result[1] or 0
                hoje = result[2] or 0
                amanha = result[3] or 0
                
                # Construir texto do tooltip
                texto = "Status das Entregas:\n\n"
                
                if atrasados > 0:
                    texto += f"⚠️ {atrasados} entrega(s) atrasada(s)\n"
                if hoje > 0:
                    texto += f"📅 {hoje} entrega(s) para hoje\n"
                if amanha > 0:
                    texto += f"⏰ {amanha} entrega(s) para amanhã\n"
                if total == 0:
                    texto += "✓ Sem entregas pendentes"
                
                return texto
        
        except Exception as e:
            return f"Erro ao carregar informações: {str(e)}"

    def pulsar_botao_notificacao(self):
        """Faz o botão de notificações pulsar quando há entregas atrasadas"""
        cores = ["#FF0000", "#CC0000"]
        
        def alterar_cor(indice=0):
            if not hasattr(self, 'btn_notificacoes'):
                return
            
            self.btn_notificacoes.configure(fg_color=cores[indice])
            proximo_indice = (indice + 1) % 2
            
            # Continuar apenas se ainda houver entregas atrasadas
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM pedidos 
                    WHERE status = 'pendente'
                    AND date(data_entrega) < date('now')
                ''')
                atrasados = cursor.fetchone()[0]
                
                if atrasados > 0:
                    self.janela.after(500, lambda: alterar_cor(proximo_indice))
        
        alterar_cor()

    def verificar_entregas_periodicamente(self):
        """Verifica entregas periodicamente e atualiza notificações"""
        self.verificar_entregas()
        self.atualizar_botao_notificacoes()
        
        # Agendar próxima verificação (a cada 5 minutos)
        self.janela.after(300000, self.verificar_entregas_periodicamente)

class DatabaseManager:
    def __init__(self):
        if platform == 'android':
            from android.storage import app_storage_path
            db_dir = app_storage_path()
            self.db_path = os.path.join(db_dir, 'sistema_loja.db')
        else:
            self.db_path = 'sistema_loja.db'
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)

if __name__ == '__main__':
    if platform == 'android':
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE
        ])
    
    SistemaLojaApp().run()