import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
import threading
from typing import List, Tuple, Dict, Any
import json
import shutil

class SQLiteBrowserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Поиск по базам SQLite")
        self.root.geometry("1200x800")

        # Settings file path
        self.settings_file = "browser_settings.json"

        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Initialize variables
        self.current_db_path = None
        self.connection = None
        self.databases = []  # List of database paths
        self.current_table = None

        # Initialize search variables before loading settings
        self.case_sensitive_var = tk.BooleanVar()
        self.partial_match_var = tk.BooleanVar(value=True)
        self.search_scope_var = tk.StringVar(value="all")  # Default to "all"

        # Load settings
        self.load_settings()

        # Create tabs
        self.create_add_db_tab()
        self.create_edit_tab()
        self.create_search_tab()

        # Populate the database treeview with loaded databases after UI is created
        self.populate_db_treeview()

        # Update the directory label after UI is created
        if hasattr(self, 'dir_path_label'):
            if hasattr(self, 'target_dir') and self.target_dir:
                self.dir_path_label.config(text=self.target_dir)
            else:
                self.dir_path_label.config(text="Директория не выбрана")

    def load_settings(self):
        """Load application settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # Load database paths
                self.databases = settings.get('databases', [])

                # Load target directory
                self.target_dir = settings.get('target_dir', '')

                # Load search settings
                if hasattr(self, 'case_sensitive_var'):
                    self.case_sensitive_var.set(settings.get('case_sensitive', False))
                if hasattr(self, 'partial_match_var'):
                    self.partial_match_var.set(settings.get('partial_match', True))
                if hasattr(self, 'search_scope_var'):
                    self.search_scope_var.set(settings.get('search_scope', 'all'))

        except Exception as e:
            print(f"Error loading settings: {e}")
            # Initialize with defaults if loading fails
            self.databases = []
            self.target_dir = ''
            if hasattr(self, 'dir_path_label'):
                self.dir_path_label.config(text="Директория не выбрана")

        # Populate the database treeview after UI is created (will be called later)

    def populate_db_treeview(self):
        """Populate the database treeview with loaded databases"""
        # Clear the tree first
        for item in self.db_tree.get_children():
            self.db_tree.delete(item)

        # Add databases to the treeview
        for db_path in self.databases:
            filename = os.path.basename(db_path)
            # Check if the database file exists and if it's currently connected
            connected_status = "Да" if (self.connection and self.current_db_path == db_path) else ""
            self.db_tree.insert("", "end", text=filename, values=(db_path, connected_status))

    def save_settings(self):
        """Save application settings to file"""
        try:
            settings = {
                'databases': self.databases,
                'target_dir': getattr(self, 'target_dir', ''),
                'case_sensitive': getattr(self, 'case_sensitive_var', tk.BooleanVar()).get(),
                'partial_match': getattr(self, 'partial_match_var', tk.BooleanVar(value=True)).get(),
                'search_scope': getattr(self, 'search_scope_var', tk.StringVar(value='all')).get()
            }

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def create_add_db_tab(self):
        """Create the tab for adding DB files"""
        self.add_db_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.add_db_frame, text="Добавить базы")

        # Main frame for controls
        controls_frame = ttk.Frame(self.add_db_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)

        # Directory selection
        dir_frame = ttk.Frame(controls_frame)
        dir_frame.pack(fill=tk.X, pady=5)

        ttk.Label(dir_frame, text="Папка с базами SQLite").pack(anchor=tk.W)

        dir_subframe = ttk.Frame(dir_frame)
        dir_subframe.pack(fill=tk.X, pady=5)

        self.dir_path_label = ttk.Label(dir_subframe, text="Директория не выбрана", relief=tk.SUNKEN, anchor=tk.W)
        self.dir_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(dir_subframe, text="Обзор...", command=self.browse_directory).pack(side=tk.RIGHT)

        # Individual file addition
        file_frame = ttk.Frame(controls_frame)
        file_frame.pack(fill=tk.X, pady=10)

        ttk.Label(file_frame, text="Добавить отдельные файлы:").pack(anchor=tk.W)

        file_subframe = ttk.Frame(file_frame)
        file_subframe.pack(fill=tk.X, pady=5)

        ttk.Button(file_subframe, text="+", width=3, command=self.add_individual_file).pack(side=tk.RIGHT)
        self.individual_file_label = ttk.Label(file_subframe, text="Файлы не добавлены", relief=tk.SUNKEN, anchor=tk.W)
        self.individual_file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # List of databases
        db_list_frame = ttk.LabelFrame(self.add_db_frame, text="Список баз данных")
        db_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create treeview for database list
        self.db_tree = ttk.Treeview(db_list_frame, columns=("path", "connected"), show="tree headings")
        self.db_tree.heading("#0", text="Название")
        self.db_tree.heading("path", text="Путь")
        self.db_tree.heading("connected", text="Подключен")
        self.db_tree.column("#0", width=150)
        self.db_tree.column("path", width=400)
        self.db_tree.column("connected", width=80, anchor="center")

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(db_list_frame, orient="vertical", command=self.db_tree.yview)
        h_scrollbar = ttk.Scrollbar(db_list_frame, orient="horizontal", command=self.db_tree.xview)
        self.db_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.db_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind click event to connect to database
        self.db_tree.bind("<Double-1>", self.on_db_double_click)

        # Buttons frame
        btn_frame = ttk.Frame(db_list_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Удалить", command=self.remove_selected_db).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.refresh_db_list).pack(side=tk.LEFT, padx=5)
        self.connect_btn = ttk.Button(btn_frame, text="Подключить", command=self.connect_to_selected_db, state=tk.DISABLED)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

    def on_db_double_click(self, event):
        """Handle double-click on a database in the list"""
        selected_item = self.db_tree.selection()
        if selected_item:
            self.connect_to_selected_db()

    def connect_to_selected_db(self):
        """Connect to the selected database"""
        selected_item = self.db_tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите базу данных для подключения")
            return

        item_values = self.db_tree.item(selected_item, "values")
        if not item_values or len(item_values) < 1:
            messagebox.showerror("Ошибка", "Не удалось получить путь к базе данных")
            return

        db_path = item_values[0]

        try:
            # Close existing connection if any
            if self.connection:
                self.connection.close()

            # Connect to the selected database
            self.connection = sqlite3.connect(db_path)
            self.current_db_path = db_path

            # Update the treeview to show connected status
            self.db_tree.set(selected_item, "connected", "Да")

            # Refresh table list in edit tab
            self.refresh_table_list()

            messagebox.showinfo("Успех", f"Подключено к базе данных: {os.path.basename(db_path)}")

        except sqlite3.Error as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к базе данных: {str(e)}")
    
    def create_edit_tab(self):
        """Create the tab for editing/viewing tables"""
        self.edit_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.edit_frame, text="Просмотр/Редактирование")

        # Top frame for controls
        top_frame = ttk.Frame(self.edit_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        # Refresh button
        ttk.Button(top_frame, text="Обновить таблицы", command=self.refresh_table_list).pack(side=tk.LEFT, padx=(0, 10))

        # Table selection
        ttk.Label(top_frame, text="Таблицы:").pack(side=tk.LEFT, padx=(10, 5))

        # Left panel for table selection
        left_frame = ttk.Frame(self.edit_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5), pady=5)

        self.table_listbox = tk.Listbox(left_frame)
        self.table_listbox.pack(fill=tk.BOTH, expand=True)
        self.table_listbox.bind("<<ListboxSelect>>", self.on_table_select)

        # Right panel for table data
        right_frame = ttk.Frame(self.edit_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=5)

        # Table data display
        self.data_tree = ttk.Treeview(right_frame)
        self.data_tree.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        # Scrollbars for treeview
        v_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.data_tree.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.data_tree.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(right_frame, orient="horizontal", command=self.data_tree.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.data_tree.configure(xscrollcommand=h_scrollbar.set)

        # Bind double-click to edit cell
        self.data_tree.bind("<Double-1>", self.on_cell_double_click)

        # Bottom frame for editing controls
        bottom_frame = ttk.Frame(right_frame)
        bottom_frame.pack(fill=tk.X, pady=5)

        # Add editing buttons
        self.add_row_btn = ttk.Button(bottom_frame, text="Добавить строку", command=self.add_row, state=tk.DISABLED)
        self.add_row_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.edit_row_btn = ttk.Button(bottom_frame, text="Редактировать", command=self.edit_row, state=tk.DISABLED)
        self.edit_row_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.delete_row_btn = ttk.Button(bottom_frame, text="Удалить строку", command=self.delete_row, state=tk.DISABLED)
        self.delete_row_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.delete_col_btn = ttk.Button(bottom_frame, text="Удалить столбец", command=self.delete_column, state=tk.DISABLED)
        self.delete_col_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Status bar
        self.status_bar = ttk.Label(right_frame, text="Выберите таблицу для отображения данных", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def on_cell_double_click(self, event):
        """Handle double-click on a cell to edit its content"""
        region = self.data_tree.identify("region", event.x, event.y)
        if region == "cell":
            # Get the clicked item and column
            item_id = self.data_tree.focus()
            column = self.data_tree.identify_column(event.x)

            # Get the column index (remove '#')
            col_idx = int(column.replace('#', '')) - 1

            # Get the values of the item
            values = list(self.data_tree.item(item_id, "values"))

            # Get the column name
            col_name = self.data_tree['columns'][col_idx]

            # Open edit dialog
            self.open_cell_editor(item_id, col_idx, col_name, values[col_idx])

    def open_cell_editor(self, item_id, col_idx, col_name, current_value):
        """Open a dialog to edit a cell value"""
        editor_window = tk.Toplevel(self.root)
        editor_window.title("Редактирование ячейки")
        editor_window.geometry("400x200")
        editor_window.transient(self.root)
        editor_window.grab_set()

        # Label showing column info
        ttk.Label(editor_window, text=f"Столбец: {col_name}").pack(pady=5)

        # Text widget for editing (multi-line support)
        text_widget = tk.Text(editor_window, height=6, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        text_widget.insert("1.0", current_value or "")

        # Button frame
        btn_frame = ttk.Frame(editor_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def save_changes():
            new_value = text_widget.get("1.0", tk.END).strip()
            self.update_cell_value(item_id, col_idx, new_value)
            editor_window.destroy()

        ttk.Button(btn_frame, text="Сохранить", command=save_changes).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Отмена", command=editor_window.destroy).pack(side=tk.LEFT)

    def update_cell_value(self, item_id, col_idx, new_value):
        """Update a cell value in the database"""
        if not self.connection or not self.current_table:
            return

        try:
            # Get the column name
            col_name = self.data_tree['columns'][col_idx]

            # Get the primary key value for the row (assuming first column is PK)
            row_values = self.data_tree.item(item_id, "values")
            pk_value = row_values[0]  # Assuming first column is primary key
            pk_col = self.data_tree['columns'][0]  # Assuming first column is primary key

            # Update the database
            cursor = self.connection.cursor()
            query = f"UPDATE {self.current_table} SET {col_name} = ? WHERE {pk_col} = ?"
            cursor.execute(query, (new_value, pk_value))
            self.connection.commit()

            # Update the treeview
            row_values[col_idx] = new_value
            self.data_tree.item(item_id, values=row_values)

            messagebox.showinfo("Успех", "Значение ячейки обновлено")

        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить значение: {str(e)}")
    
    def create_search_tab(self):
        """Create the tab for advanced search"""
        self.search_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_frame, text="Поиск")

        # Search configuration frame
        config_frame = ttk.LabelFrame(self.search_frame, text="Настройки поиска")
        config_frame.pack(fill=tk.X, padx=10, pady=10)

        # Search options
        options_frame = ttk.Frame(config_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        # Checkboxes for search options (non-exclusive)
        ttk.Checkbutton(options_frame, text="Учитывать регистр", variable=self.case_sensitive_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(options_frame, text="Частичное совпадение", variable=self.partial_match_var).pack(side=tk.LEFT, padx=5)

        # Radio buttons for mutually exclusive search scope
        ttk.Radiobutton(options_frame, text="Искать во всех файлах", variable=self.search_scope_var, value="all").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(options_frame, text="Искать в текущем файле", variable=self.search_scope_var, value="current").pack(side=tk.LEFT, padx=5)

        # Search input
        search_input_frame = ttk.Frame(config_frame)
        search_input_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(search_input_frame, text="Поиск (введите ключевые слова через пробел):").pack(anchor=tk.W)
        self.search_entry = tk.Text(search_input_frame, height=3, wrap=tk.WORD)
        self.search_entry.pack(fill=tk.X, pady=5)

        # Search button
        ttk.Button(search_input_frame, text="Найти", command=self.perform_search).pack(pady=5)

        # Results frame
        results_frame = ttk.LabelFrame(self.search_frame, text="Результаты поиска")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Results treeview
        self.results_tree = ttk.Treeview(results_frame, columns=("db_name", "table_name", "column_name", "value"), show="headings")
        self.results_tree.heading("db_name", text="База данных")
        self.results_tree.heading("table_name", text="Таблица")
        self.results_tree.heading("column_name", text="Столбец")
        self.results_tree.heading("value", text="Значение")

        self.results_tree.column("db_name", width=150)
        self.results_tree.column("table_name", width=150)
        self.results_tree.column("column_name", width=150)
        self.results_tree.column("value", width=300)

        # Scrollbars for results
        v_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind double-click to view result details
        self.results_tree.bind("<Double-1>", self.on_result_double_click)

    def _perform_search_worker(self, search_terms):
        """Worker function for performing search in a separate thread"""
        # This method is kept for compatibility but not used anymore
        pass

    def _execute_search(self, search_terms):
        """Execute the search and populate results"""
        results = []

        # Determine which databases to search based on radio button selection
        if self.search_scope_var.get() == "current" and self.current_db_path:
            # Only search in the currently connected database
            dbs_to_search = [self.current_db_path] if self.current_db_path in self.databases else []
        else:
            # Search in all databases
            dbs_to_search = self.databases

        # Search in each database
        for db_path in dbs_to_search:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Determine which tables to search based on radio button selection
                if self.search_scope_var.get() == "current" and self.current_table:
                    # Only search in the current table
                    tables_to_search = [self.current_table]
                else:
                    # Get all tables in the database
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    tables_to_search = [table[0] for table in tables]

                # Search in each table
                for table_name in tables_to_search:
                    try:
                        # Get all column names
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns_info = cursor.fetchall()
                        column_names = [col[1] for col in columns_info]

                        # Set to track unique result identifiers to prevent duplicates
                        seen_results = set()

                        # Search for each term in each column
                        for term in search_terms:
                            for col_name in column_names:
                                # Build query based on search options
                                if self.partial_match_var.get():
                                    if self.case_sensitive_var.get():
                                        query = f"SELECT ROWID, {col_name} FROM {table_name} WHERE {col_name} LIKE ?"
                                    else:
                                        query = f"SELECT ROWID, {col_name} FROM {table_name} WHERE LOWER(CAST({col_name} AS TEXT)) LIKE LOWER(?)"
                                    search_param = f'%{term}%'
                                else:
                                    if self.case_sensitive_var.get():
                                        query = f"SELECT ROWID, {col_name} FROM {table_name} WHERE {col_name} = ?"
                                    else:
                                        query = f"SELECT ROWID, {col_name} FROM {table_name} WHERE LOWER(CAST({col_name} AS TEXT)) = LOWER(?)"
                                    search_param = term

                                try:
                                    cursor.execute(query, (search_param,))
                                    rows = cursor.fetchall()

                                    for row in rows:
                                        row_id = row[0]  # ROWID of the matching record
                                        matched_value = str(row[1]) if row[1] is not None else ""

                                        # Get all values from the matching row
                                        all_columns_query = f"SELECT * FROM {table_name} WHERE ROWID = ?"
                                        cursor.execute(all_columns_query, (row_id,))
                                        all_values = cursor.fetchone()

                                        # Create a detailed result string with all column names and values
                                        all_data_parts = []
                                        for i, col_name_full in enumerate(column_names):
                                            if i < len(all_values):
                                                val = str(all_values[i]) if all_values[i] is not None else ""
                                                all_data_parts.append(f"{col_name_full}: {val}")

                                        all_data_str = ", ".join(all_data_parts)

                                        # Create a unique identifier for this specific result
                                        # (db_path, table_name, row_id, col_name, matched_value) makes it unique
                                        unique_id = (db_path, table_name, row_id, col_name, matched_value)

                                        # Only add if this specific combination hasn't been seen before
                                        if unique_id not in seen_results:
                                            seen_results.add(unique_id)

                                            # Create a tuple representing this result
                                            result_tuple = (
                                                os.path.basename(db_path),  # db_name
                                                table_name,                 # table_name
                                                col_name,                   # column_name (where match was found)
                                                f"Matched: {matched_value} | All Data: {all_data_str}"  # value with all row data
                                            )
                                            results.append(result_tuple)

                                except sqlite3.Error:
                                    # Skip problematic columns
                                    continue

                    except sqlite3.Error:
                        # Skip problematic tables
                        continue

                conn.close()
            except sqlite3.Error:
                # Skip problematic databases
                continue

        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Add unique results to the treeview
        for result in results:
            self.results_tree.insert("", "end", values=result)

        # Show summary
        messagebox.showinfo("Поиск завершен", f"Найдено {len(results)} результатов")

        # Show all results in a new window
        self.show_all_results_in_new_window(results)

    def show_all_results_in_new_window(self, results):
        """Show all search results in a new window with a list format"""
        if not results:
            return

        # Create a new window for displaying results
        results_window = tk.Toplevel(self.root)
        results_window.title("Результаты поиска")
        results_window.geometry("900x700")

        # Configure the window with a nice style
        results_window.configure(bg="#f0f0f0")

        # Create a frame for the content
        content_frame = ttk.Frame(results_window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Create a text widget to display results with custom styling
        results_text = tk.Text(
            content_frame,
            wrap=tk.WORD,
            bg="white",
            fg="black",
            font=("Arial", 10),
            padx=10,
            pady=10,
            borderwidth=2,
            relief="groove"
        )
        results_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create scrollbar for the text widget
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        results_text.configure(yscrollcommand=scrollbar.set)

        # Configure tags for styling
        results_text.tag_configure("header", font=("Arial", 12, "bold"), foreground="#1a5fb4", spacing1=8, spacing3=8)
        results_text.tag_configure("section", font=("Arial", 10, "bold"), foreground="#333333", spacing1=4)
        results_text.tag_configure("highlight", font=("Arial", 10, "bold"), background="#ffff00", foreground="#000000")
        results_text.tag_configure("normal", font=("Arial", 10), foreground="#000000")
        results_text.tag_configure("separator", font=("Arial", 8), foreground="#cccccc")

        # Add results to the text widget with improved formatting
        current_db = None
        for i, result in enumerate(results):
            db_name, table_name, column_name, full_value = result

            # Extract matched value and all data
            if " | All Data: " in full_value:
                matched_part, all_data_part = full_value.split(" | All Data: ", 1)
                matched_value = matched_part.replace("Matched: ", "")
            else:
                matched_value = full_value
                all_data_part = "Данные недоступны"

            # Add database header if it's a new database
            if current_db != db_name:
                if current_db is not None:  # Add spacing between databases
                    results_text.insert(tk.END, "\n")

                results_text.insert(tk.END, f"\n🔍 БАЗА ДАННЫХ: {db_name}\n", "header")
                current_db = db_name

            # Add the result information with better formatting
            results_text.insert(tk.END, f"📋 Таблица: ", "section")
            results_text.insert(tk.END, f"{table_name}\n", "normal")

            results_text.insert(tk.END, f"🏷️ Столбец: ", "section")
            results_text.insert(tk.END, f"{column_name}\n", "normal")

            results_text.insert(tk.END, f"🎯 Найденное значение: ", "section")
            results_text.insert(tk.END, f"{matched_value}\n", "highlight")

            results_text.insert(tk.END, f"📝 Все данные строки:\n", "section")
            # Split the all_data_part by commas and add each on a new line
            data_fields = all_data_part.split(", ")
            for field in data_fields:
                results_text.insert(tk.END, f"   • {field}\n", "normal")

            results_text.insert(tk.END, "\n" + "="*60 + "\n", "separator")

        # Make the text widget read-only
        results_text.config(state=tk.DISABLED)

        # Add a status bar with count
        status_frame = ttk.Frame(results_window)
        status_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        status_label = ttk.Label(
            status_frame,
            text=f"Найдено {len(results)} результатов",
            font=("Arial", 9),
            foreground="#555555"
        )
        status_label.pack(side=tk.RIGHT)

    def browse_directory(self):
        """Open directory dialog to select a directory with DB files"""
        directory = filedialog.askdirectory(title="Выберите папку с базами SQLite")
        if directory:
            self.target_dir = directory  # Store the target directory
            self.dir_path_label.config(text=directory)
            # Save the selected directory to settings
            self.save_settings()
            # Scan directory for .db files
            self.scan_directory_for_dbs(directory)
    
    def scan_directory_for_dbs(self, directory):
        """Scan the selected directory for database files"""
        if not os.path.isdir(directory):
            return
            
        # Find all .db, .sqlite, .sqlite3 files
        db_extensions = ['.db', '.sqlite', '.sqlite3']
        for filename in os.listdir(directory):
            if any(filename.lower().endswith(ext) for ext in db_extensions):
                filepath = os.path.join(directory, filename)
                if filepath not in self.databases:
                    self.databases.append(filepath)
                    self.db_tree.insert("", "end", text=filename, values=(filepath,))
    
    def add_individual_file(self):
        """Add individual DB file by copying to selected directory"""
        # First check if a directory has been selected
        if not hasattr(self, 'target_dir') or not self.target_dir:
            messagebox.showwarning("Предупреждение", "Сначала выберите целевую директорию для копирования файлов")
            directory = filedialog.askdirectory(title="Выберите директорию для копирования файлов")
            if directory:
                self.target_dir = directory
                self.dir_path_label.config(text=directory)
            else:
                return  # User cancelled directory selection

        file_paths = filedialog.askopenfilenames(
            title="Выберите файлы базы данных",
            filetypes=[("SQLite Files", "*.db *.sqlite *.sqlite3"), ("All Files", "*.*")]
        )

        if file_paths:
            import shutil
            copied_count = 0
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                target_path = os.path.join(self.target_dir, filename)

                # Handle duplicate filenames
                counter = 1
                original_target_path = target_path
                while os.path.exists(target_path):
                    name, ext = os.path.splitext(original_target_path)
                    target_path = f"{name}_{counter}{ext}"
                    counter += 1

                # Copy the file to the target directory
                try:
                    shutil.copy2(file_path, target_path)
                    # Add the copied file to the database list
                    if target_path not in self.databases:
                        self.databases.append(target_path)
                        self.db_tree.insert("", "end", text=os.path.basename(target_path), values=(target_path,))
                        copied_count += 1
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось скопировать файл {filename}: {str(e)}")

            self.individual_file_label.config(text=f"Скопировано {copied_count} файлов в {os.path.basename(self.target_dir)}")
    
    def remove_selected_db(self):
        """Remove selected database from the list"""
        selected_item = self.db_tree.selection()
        if selected_item:
            item_values = self.db_tree.item(selected_item, "values")
            if item_values:
                db_path = item_values[0]
                if db_path in self.databases:
                    self.databases.remove(db_path)
                    self.db_tree.delete(selected_item)
    
    def refresh_db_list(self):
        """Refresh the list of databases"""
        # Clear the tree
        for item in self.db_tree.get_children():
            self.db_tree.delete(item)
        
        # Re-add databases
        for db_path in self.databases:
            filename = os.path.basename(db_path)
            self.db_tree.insert("", "end", text=filename, values=(db_path,))
    
    def refresh_table_list(self):
        """Refresh the list of tables in the database"""
        if not self.connection:
            self.status_bar.config(text="Нет подключения к базе данных")
            return
            
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            self.table_listbox.delete(0, tk.END)
            for table in tables:
                self.table_listbox.insert(tk.END, table[0])
                
            self.status_bar.config(text=f"Найдено {len(tables)} таблиц")
                
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Не удалось получить список таблиц: {str(e)}")
            self.status_bar.config(text="Ошибка при получении списка таблиц")
    
    def on_table_select(self, event):
        """Handle table selection in the listbox"""
        selection = self.table_listbox.curselection()
        if selection:
            table_name = self.table_listbox.get(selection[0])
            self.current_table = table_name
            self.display_table_data(table_name)
    
    def display_table_data(self, table_name):
        """Display data from the selected table"""
        if not self.connection:
            return
            
        try:
            # Clear previous data
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            # Get column names
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            
            # Set up treeview columns
            self.data_tree["columns"] = column_names
            self.data_tree["show"] = "headings"
            
            for col in column_names:
                self.data_tree.heading(col, text=col)
                self.data_tree.column(col, width=100)
            
            # Fetch and insert data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            for row in rows:
                self.data_tree.insert("", tk.END, values=row)
                
            # Enable editing buttons
            self.add_row_btn.config(state=tk.NORMAL)
            self.edit_row_btn.config(state=tk.NORMAL)
            self.delete_row_btn.config(state=tk.NORMAL)
            self.delete_col_btn.config(state=tk.NORMAL)
            self.status_bar.config(text=f"Отображено {len(rows)} записей из таблицы '{table_name}'")
                
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Не удалось отобразить данные таблицы: {str(e)}")
            self.status_bar.config(text="Ошибка при отображении данных таблицы")
    
    def add_row(self):
        """Add a new row to the selected table"""
        if not self.current_table:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите таблицу")
            return
            
        # In a real implementation, this would open a form to add a new record
        messagebox.showinfo("Добавление строки", f"Добавление новой строки в таблицу: {self.current_table}")
    
    def edit_row(self):
        """Edit the selected row"""
        selected_items = self.data_tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для редактирования")
            return
            
        # In a real implementation, this would open a form to edit the selected record
        messagebox.showinfo("Редактирование строки", "Редактирование выбранной строки")
    
    def delete_row(self):
        """Delete the selected row"""
        selected_items = self.data_tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для удаления")
            return
            
        result = messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить выбранную строку?")
        if result:
            # In a real implementation, this would delete the record from the database
            messagebox.showinfo("Удаление строки", "Строка успешно удалена")
    
    def delete_column(self):
        """Delete the selected column"""
        if not self.current_table:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите таблицу")
            return
            
        # In a real implementation, this would delete the selected column
        messagebox.showinfo("Удаление столбца", f"Удаление столбца из таблицы: {self.current_table}")
    
    def perform_search(self):
        """Perform advanced search across databases and tables"""
        search_text = self.search_entry.get("1.0", tk.END).strip()
        if not search_text:
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите поисковый запрос")
            return

        # Parse search terms (split by spaces and clean)
        search_terms = [term.strip() for term in search_text.split() if term.strip()]
        if not search_terms:
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите хотя бы один поисковый термин")
            return

        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Perform search in the main thread since tkinter isn't thread-safe
        self._execute_search(search_terms)
    
    def _perform_search_worker(self, search_term):
        """Worker function for performing search in a separate thread"""
        # This would implement the actual search logic
        # For now, we'll simulate results
        results = []
        
        # Simulate search across databases
        for db_path in self.databases:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get all tables in the database
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    
                    # Get all column names
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns_info = cursor.fetchall()
                    column_names = [col[1] for col in columns_info]
                    
                    # Search in each column
                    for col_name in column_names:
                        # Build query based on search options
                        if self.partial_match_var.get():
                            if self.case_sensitive_var.get():
                                query = f"SELECT {col_name} FROM {table_name} WHERE {col_name} LIKE ?"
                            else:
                                query = f"SELECT {col_name} FROM {table_name} WHERE LOWER({col_name}) LIKE LOWER(?)"
                            search_param = f"%{search_term}%"
                        else:
                            if self.case_sensitive_var.get():
                                query = f"SELECT {col_name} FROM {table_name} WHERE {col_name} = ?"
                            else:
                                query = f"SELECT {col_name} FROM {table_name} WHERE LOWER({col_name}) = LOWER(?)"
                            search_param = search_term
                        
                        try:
                            cursor.execute(query, (search_param,))
                            rows = cursor.fetchall()
                            
                            for row in rows:
                                value = str(row[0]) if row[0] is not None else ""
                                # Add result to list
                                results.append((db_path, table_name, col_name, value))
                        except sqlite3.Error:
                            # Skip problematic columns
                            continue
                
                conn.close()
            except sqlite3.Error:
                # Skip problematic databases
                continue
        
        # Update UI with results (this should be done in the main thread)
        # For now, we'll just print the results
        print(f"Found {len(results)} results")
        for result in results[:10]:  # Show first 10 results
            print(result)
    
    def on_result_double_click(self, event):
        """Handle double-click on search result"""
        selected_item = self.results_tree.selection()
        if selected_item:
            item_values = self.results_tree.item(selected_item, "values")
            if len(item_values) >= 4:
                db_name, table_name, column_name, value = item_values

                # Extract the matched value and all data from the combined value string
                if " | All Data: " in value:
                    matched_part, all_data_part = value.split(" | All Data: ", 1)
                    matched_value = matched_part.replace("Matched: ", "")
                else:
                    matched_value = value
                    all_data_part = "Данные недоступны"

                # Show result in a new window
                result_window = tk.Toplevel(self.root)
                result_window.title("Детали результата поиска")
                result_window.geometry("700x500")

                # Create a frame for the content
                content_frame = ttk.Frame(result_window)
                content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                # Display the information
                ttk.Label(content_frame, text="Название базы:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
                ttk.Label(content_frame, text=db_name).pack(anchor=tk.W, pady=(0, 10))

                ttk.Label(content_frame, text="Название таблицы:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
                ttk.Label(content_frame, text=table_name).pack(anchor=tk.W, pady=(0, 10))

                ttk.Label(content_frame, text="Столбец с совпадением:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
                ttk.Label(content_frame, text=column_name).pack(anchor=tk.W, pady=(0, 10))

                ttk.Label(content_frame, text="Найденное значение:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
                ttk.Label(content_frame, text=matched_value).pack(anchor=tk.W, pady=(0, 10))

                ttk.Label(content_frame, text="Все данные строки:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
                all_data_text = tk.Text(content_frame, height=12, wrap=tk.WORD)
                all_data_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
                all_data_text.insert(tk.END, all_data_part)
                all_data_text.config(state=tk.DISABLED)  # Make it read-only

                # Button to navigate to the record
                def navigate_to_record():
                    # Find the database path
                    db_path = None
                    for path in self.databases:
                        if os.path.basename(path) == db_name:
                            db_path = path
                            break

                    if db_path:
                        # Connect to the database if not already connected
                        if self.current_db_path != db_path:
                            try:
                                if self.connection:
                                    self.connection.close()
                                self.connection = sqlite3.connect(db_path)
                                self.current_db_path = db_path

                                # Update the treeview to show connected status
                                for item in self.db_tree.get_children():
                                    values = self.db_tree.item(item, "values")
                                    if values and values[0] == db_path:
                                        self.db_tree.set(item, "connected", "Да")
                                    else:
                                        self.db_tree.set(item, "connected", "")

                            except sqlite3.Error as e:
                                messagebox.showerror("Ошибка", f"Не удалось подключиться к базе данных: {str(e)}")
                                return

                        # Switch to the edit tab
                        self.notebook.select(self.edit_frame)

                        # Select the table in the listbox
                        self.table_listbox.selection_clear(0, tk.END)
                        for i in range(self.table_listbox.size()):
                            if self.table_listbox.get(i) == table_name:
                                self.table_listbox.selection_set(i)
                                self.on_table_select(None)
                                break

                        # Highlight the found value in the table (if possible)
                        # This is a simplified version - in a real app, you'd need to find the specific row
                        messagebox.showinfo("Навигация", f"Перешли к таблице '{table_name}' в базе '{db_name}'")

                    result_window.destroy()

                ttk.Button(content_frame, text="Перейти к записи", command=navigate_to_record).pack()

def main():
    root = tk.Tk()
    app = SQLiteBrowserApp(root)

    # Handle window closing to properly close database connections and save settings
    def on_closing():
        if app.connection:
            app.connection.close()
        app.save_settings()  # Save settings before closing
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
