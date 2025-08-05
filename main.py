import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import struct
import random

# Dark theme colors
BG_COLOR = "#121212"  # Deeper black
FG_COLOR = "#e0e0e0"
ACCENT_COLOR = "#4a6fa5"
BUTTON_COLOR = "#2a2a2a"
TREE_COLOR = "#1e1e1e"
TREE_SEL_COLOR = "#3a5f8a"
ENTRY_COLOR = "#252525"

class ShortcutManager:
    __slots__ = ('filename', '_shortcuts', '_categories')
    
    def __init__(self, filename="shortcuts.bin"):
        self.filename = filename
        self._shortcuts = []
        self._categories = []
        
    def add_shortcut(self, shortcut, description, category):
        if category not in self._categories:
            self._categories.append(category)
        category_idx = self._categories.index(category)
        self._shortcuts.append((shortcut, description, category_idx))
    
    def get_shortcuts(self, category_filter=None):
        if category_filter is None:
            return [(s, d, self._categories[c]) for s, d, c in self._shortcuts]
        return [(s, d, cat) for s, d, idx in self._shortcuts 
                if (cat := self._categories[idx]) == category_filter]
    
    def get_all_categories(self):
        return self._categories.copy()
    
    def save_to_file(self):
        with open(self.filename, 'wb') as f:
            f.write(struct.pack('II', len(self._shortcuts), len(self._categories)))
            for cat in self._categories:
                encoded = cat.encode('utf-8')
                f.write(struct.pack('B', len(encoded)))
                f.write(encoded)
            for shortcut, desc, cat_idx in self._shortcuts:
                enc_short = shortcut.encode('utf-8')
                enc_desc = desc.encode('utf-8')
                f.write(struct.pack('B', len(enc_short)))
                f.write(enc_short)
                f.write(struct.pack('B', len(enc_desc)))
                f.write(enc_desc)
                f.write(struct.pack('I', cat_idx))
    
    def load_from_file(self):
        if not os.path.exists(self.filename):
            return
        with open(self.filename, 'rb') as f:
            num_shortcuts, num_categories = struct.unpack('II', f.read(8))
            categories = []
            for _ in range(num_categories):
                length = struct.unpack('B', f.read(1))[0]
                categories.append(f.read(length).decode('utf-8'))
            self._categories = categories
            shortcuts = []
            for _ in range(num_shortcuts):
                len_short = struct.unpack('B', f.read(1))[0]
                shortcut = f.read(len_short).decode('utf-8')
                len_desc = struct.unpack('B', f.read(1))[0]
                description = f.read(len_desc).decode('utf-8')
                cat_idx = struct.unpack('I', f.read(4))[0]
                shortcuts.append((shortcut, description, cat_idx))
            self._shortcuts = shortcuts

class KeysnapApp(tk.Tk):
    __slots__ = ('manager', 'notebook', 'list_frame', 'add_frame', 'quiz_frame')
    
    def __init__(self):
        super().__init__()
        self.title("Keysnap - Keyboard Shortcut Master")
        self.geometry("800x500")
        self.configure(bg=BG_COLOR)
        
        # Apply dark theme
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('.', background=BG_COLOR, foreground=FG_COLOR)
        style.configure('TFrame', background=BG_COLOR)
        style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR)
        style.configure('TButton', background=BUTTON_COLOR, foreground=FG_COLOR)
        style.configure('Treeview', background=TREE_COLOR, fieldbackground=TREE_COLOR, 
                        foreground=FG_COLOR, borderwidth=0)
        style.map('Treeview', background=[('selected', TREE_SEL_COLOR)])
        style.configure('Treeview.Heading', background=BUTTON_COLOR, 
                        foreground=FG_COLOR, relief='flat')
        style.configure('TCombobox', fieldbackground=ENTRY_COLOR, 
                        foreground=FG_COLOR, background=BG_COLOR)
        style.map('TCombobox', fieldbackground=[('readonly', ENTRY_COLOR)])
        style.configure('TNotebook', background=BG_COLOR)
        style.configure('TNotebook.Tab', background=BUTTON_COLOR, 
                        foreground=FG_COLOR, padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', ACCENT_COLOR)])
        style.configure('TEntry', fieldbackground=ENTRY_COLOR, 
                        foreground=FG_COLOR, insertbackground=FG_COLOR)
        
        self.manager = ShortcutManager()
        self.manager.load_from_file()
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.list_frame = ShortcutListFrame(self.notebook, self)
        self.add_frame = AddEditFrame(self.notebook, self)
        self.quiz_frame = QuizFrame(self.notebook, self)
        
        self.notebook.add(self.list_frame, text='Shortcut List')
        self.notebook.add(self.add_frame, text='Add Shortcut')
        self.notebook.add(self.quiz_frame, text='Learning Mode')
        
        self.list_frame.refresh_list()
        self.bind('<Control-q>', lambda e: self.destroy())

class ShortcutListFrame(ttk.Frame):
    __slots__ = ('app', 'tree', 'category_filter', 'filter_combo')
    
    def __init__(self, parent, app):
        super().__init__(parent, style='TFrame')
        self.app = app
        
        # Search UI
        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', padx=10, pady=(10, 0))
        
        search_label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side='left', padx=(0, 5))
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        search_entry.bind('<KeyRelease>', self.refresh_list)
        
        # Filter UI
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Filter by category:").pack(side='left')
        self.category_filter = tk.StringVar()
        self.filter_combo = ttk.Combobox(filter_frame, textvariable=self.category_filter, state='readonly')
        self.filter_combo.pack(side='left', padx=5, fill='x', expand=True)
        self.filter_combo.bind('<<ComboboxSelected>>', self.refresh_list)
        
        # Treeview
        self.tree = ttk.Treeview(self, columns=('Shortcut', 'Description', 'Category'), show='headings')
        self.tree.heading('Shortcut', text='Shortcut')
        self.tree.heading('Description', text='Description')
        self.tree.heading('Category', text='Category')
        self.tree.column('Shortcut', width=150)
        self.tree.column('Description', width=400)
        self.tree.column('Category', width=150)
        
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Context menu
        self.context_menu = tk.Menu(self, tearoff=0, bg=BUTTON_COLOR, fg=FG_COLOR)
        self.context_menu.add_command(label="Delete Shortcut", command=self.delete_selected)
        self.tree.bind('<Button-3>', self.show_context_menu)
        
        self.refresh_categories()
    
    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.tk_popup(event.x_root, event.y_root)
    
    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        values = item['values']
        if messagebox.askyesno("Confirm", f"Delete shortcut '{values[0]}'?"):
            for idx, (s, d, c) in enumerate(self.app.manager._shortcuts):
                cat = self.app.manager._categories[c]
                if s == values[0] and d == values[1] and cat == values[2]:
                    del self.app.manager._shortcuts[idx]
                    break
            self.app.manager.save_to_file()
            self.refresh_list()
    
    def refresh_categories(self):
        categories = ['All'] + self.app.manager.get_all_categories()
        self.filter_combo['values'] = categories
        if categories:
            self.category_filter.set('All')
    
    def refresh_list(self, event=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        filter_val = self.category_filter.get()
        category = None if filter_val == 'All' else filter_val
        search_term = self.search_var.get().lower()
        
        for shortcut, desc, cat in self.app.manager.get_shortcuts(category):
            if search_term in shortcut.lower() or search_term in desc.lower() or search_term in cat.lower():
                self.tree.insert('', 'end', values=(shortcut, desc, cat))

class AddEditFrame(ttk.Frame):
    __slots__ = ('app', 'shortcut_var', 'desc_var', 'category_var', 'category_combo')
    
    def __init__(self, parent, app):
        super().__init__(parent, style='TFrame')
        self.app = app
        
        form_frame = ttk.Frame(self)
        form_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(form_frame, text="Shortcut:").grid(row=0, column=0, sticky='w', pady=5)
        self.shortcut_var = tk.StringVar()
        shortcut_entry = ttk.Entry(form_frame, textvariable=self.shortcut_var, width=40)
        shortcut_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        ttk.Label(form_frame, text="Description:").grid(row=1, column=0, sticky='w', pady=5)
        self.desc_var = tk.StringVar()
        desc_entry = ttk.Entry(form_frame, textvariable=self.desc_var, width=40)
        desc_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        ttk.Label(form_frame, text="Category:").grid(row=2, column=0, sticky='w', pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form_frame, textvariable=self.category_var, width=37)
        self.category_combo.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        
        new_cat_btn = ttk.Button(form_frame, text="New Category", command=self.add_category)
        new_cat_btn.grid(row=2, column=2, padx=(5, 0))
        
        save_btn = ttk.Button(form_frame, text="Save Shortcut", command=self.save_shortcut)
        save_btn.grid(row=3, column=1, sticky='e', pady=15)
        
        form_frame.columnconfigure(1, weight=1)
        self.refresh_categories()
    
    def add_category(self):
        new_cat = simpledialog.askstring("New Category", "Enter new category name:", parent=self)
        if new_cat and new_cat.strip():
            self.category_var.set(new_cat.strip())
            self.refresh_categories()
    
    def refresh_categories(self):
        categories = self.app.manager.get_all_categories()
        self.category_combo['values'] = categories
    
    def save_shortcut(self):
        shortcut = self.shortcut_var.get().strip()
        desc = self.desc_var.get().strip()
        category = self.category_var.get().strip()
        
        if not shortcut or not desc or not category:
            messagebox.showwarning("Validation", "All fields are required!")
            return
        
        self.app.manager.add_shortcut(shortcut, desc, category)
        self.app.manager.save_to_file()
        
        self.shortcut_var.set('')
        self.desc_var.set('')
        self.category_var.set('')
        
        self.app.list_frame.refresh_categories()
        self.app.list_frame.refresh_list()
        self.app.quiz_frame.refresh_available()
        
        messagebox.showinfo("Success", "Shortcut saved successfully!")

class QuizFrame(ttk.Frame):
    __slots__ = ('app', 'question_var', 'score_var', 'buttons', 'current_question', 
                 'correct_answer', 'score', 'total_questions', 'accuracy_var')
    
    def __init__(self, parent, app):
        super().__init__(parent, style='TFrame')
        self.app = app
        self.score = 0
        self.total_questions = 0
        
        # Difficulty selector
        diff_frame = ttk.Frame(self)
        diff_frame.pack(fill='x', padx=20, pady=(10, 0))
        
        ttk.Label(diff_frame, text="Difficulty:").pack(side='left')
        self.difficulty = tk.StringVar(value="Normal")
        diff_combo = ttk.Combobox(diff_frame, textvariable=self.difficulty, 
                                 values=["Easy", "Normal", "Hard"], state="readonly", width=10)
        diff_combo.pack(side='left', padx=5)
        
        # Question UI
        question_frame = ttk.Frame(self)
        question_frame.pack(fill='x', padx=20, pady=20)
        
        self.question_var = tk.StringVar(value="Click 'Start Quiz' to begin")
        ttk.Label(question_frame, textvariable=self.question_var, 
                 wraplength=700, font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Answer buttons
        self.buttons = []
        for i in range(4):
            btn = ttk.Button(self, command=lambda idx=i: self.check_answer(idx))
            btn.pack(fill='x', padx=50, pady=5)
            self.buttons.append(btn)
        
        score_frame = ttk.Frame(self)
        score_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(score_frame, text="Score:").pack(side='left')
        self.score_var = tk.StringVar(value="0/0")
        ttk.Label(score_frame, textvariable=self.score_var, font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        
        self.accuracy_var = tk.StringVar(value="0%")
        ttk.Label(score_frame, textvariable=self.accuracy_var).pack(side='left', padx=10)
        
        control_frame = ttk.Frame(self)
        control_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(control_frame, text="Start Quiz", command=self.new_question).pack(side='right')
        ttk.Button(control_frame, text="Reset Score", command=self.reset_score).pack(side='right', padx=5)
        
        self.refresh_available()
    
    def update_score(self):
        self.score_var.set(f"{self.score}/{self.total_questions}")
        accuracy = (self.score / self.total_questions * 100) if self.total_questions > 0 else 0
        self.accuracy_var.set(f"{accuracy:.1f}%")
    
    def reset_score(self):
        self.score = 0
        self.total_questions = 0
        self.update_score()
        messagebox.showinfo("Score Reset", "Your score has been reset")
    
    def refresh_available(self):
        self.available_shortcuts = self.app.manager.get_shortcuts()
        self.new_question()
    
    def new_question(self):
        if not self.available_shortcuts:
            self.question_var.set("No shortcuts available. Add some first!")
            for btn in self.buttons:
                btn.config(text="", state='disabled')
            return
        
        self.current_question = random.choice(self.available_shortcuts)
        shortcut, correct_desc, _ = self.current_question
        
        diff = self.difficulty.get()
        if diff == "Easy":
            other_descs = [d for s, d, c in self.available_shortcuts 
                          if d != correct_desc and c == self.current_question[2]]
        elif diff == "Hard":
            other_descs = [d for s, d, c in self.available_shortcuts 
                          if d != correct_desc and c != self.current_question[2]]
        else:
            other_descs = [d for s, d, c in self.available_shortcuts 
                          if d != correct_desc]
        
        wrong_count = 3 if len(other_descs) >= 3 else len(other_descs)
        wrong_answers = random.sample(other_descs, wrong_count) if wrong_count > 0 else []
        
        all_answers = [correct_desc] + wrong_answers
        random.shuffle(all_answers)
        self.correct_answer = all_answers.index(correct_desc)
        
        self.question_var.set(f"What does '{shortcut}' do?")
        for i, btn in enumerate(self.buttons):
            if i < len(all_answers):
                btn.config(text=all_answers[i], state='normal')
            else:
                btn.config(text="", state='disabled')
    
    def check_answer(self, index):
        self.total_questions += 1
        if index == self.correct_answer:
            self.score += 1
            result = "Correct!"
        else:
            result = f"Wrong! The correct answer was: {self.current_question[1]}"
        
        self.update_score()
        messagebox.showinfo("Result", result)
        self.new_question()

if __name__ == "__main__":
    app = KeysnapApp()
    app.mainloop()