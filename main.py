import tkinter as tk
from tkinter import ttk, messagebox
import os
import struct
import random

class ShortcutManager:
    def __init__(self, filename="shortcuts.bin"):
        self.filename = filename
        self.shortcuts = []
        self.categories = []
        self.load_from_file()
    
    def add_shortcut(self, shortcut, description, category, save=True):
        if category not in self.categories:
            self.categories.append(category)
        self.shortcuts.append({
            'shortcut': shortcut,
            'description': description,
            'category': category
        })
        if save:
            self.save_to_file()
    
    def get_shortcuts(self):
        return self.shortcuts.copy()
    
    def get_categories(self):
        return self.categories.copy()
    
    def save_to_file(self):
        try:
            with open(self.filename, 'wb') as f:
                f.write(struct.pack('I', len(self.shortcuts)))
                
                for shortcut in self.shortcuts:
                    enc_short = shortcut['shortcut'].encode('utf-8')
                    f.write(struct.pack('I', len(enc_short)))
                    f.write(enc_short)
                    
                    enc_desc = shortcut['description'].encode('utf-8')
                    f.write(struct.pack('I', len(enc_desc)))
                    f.write(enc_desc)
                    
                    enc_cat = shortcut['category'].encode('utf-8')
                    f.write(struct.pack('I', len(enc_cat)))
                    f.write(enc_cat)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data: {str(e)}")
    
    def load_from_file(self):
        if not os.path.exists(self.filename):
            return
            
        try:
            with open(self.filename, 'rb') as f:
                data = f.read(4)
                if not data:
                    return
                    
                num_shortcuts = struct.unpack('I', data)[0]
                
                for _ in range(num_shortcuts):
                    len_short_data = f.read(4)
                    if len(len_short_data) < 4:
                        break
                    len_short = struct.unpack('I', len_short_data)[0]
                    shortcut = f.read(len_short).decode('utf-8')
                    
                    len_desc_data = f.read(4)
                    if len(len_desc_data) < 4:
                        break
                    len_desc = struct.unpack('I', len_desc_data)[0]
                    description = f.read(len_desc).decode('utf-8')
                    
                    len_cat_data = f.read(4)
                    if len(len_cat_data) < 4:
                        break
                    len_cat = struct.unpack('I', len_cat_data)[0]
                    category = f.read(len_cat).decode('utf-8')
                    
                    self.add_shortcut(shortcut, description, category, save=False)
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load data: {str(e)}")

class KeysnapApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Keysnap - Stage 2")
        self.geometry("700x500")
        
        self.manager = ShortcutManager()
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.list_frame = ShortcutListFrame(self.notebook, self)
        self.add_frame = AddShortcutFrame(self.notebook, self)
        self.quiz_frame = QuizFrame(self.notebook, self)
        
        self.notebook.add(self.list_frame, text='Shortcut List')
        self.notebook.add(self.add_frame, text='Add Shortcut')
        self.notebook.add(self.quiz_frame, text='Quiz')
        
        self.list_frame.refresh_list()

class ShortcutListFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.tree = ttk.Treeview(self, columns=('Shortcut', 'Description', 'Category'), show='headings')
        self.tree.heading('Shortcut', text='Shortcut')
        self.tree.heading('Description', text='Description')
        self.tree.heading('Category', text='Category')
        
        self.tree.column('Shortcut', width=100)
        self.tree.column('Description', width=250)
        self.tree.column('Category', width=100)
        
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)
    
    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for shortcut in self.app.manager.get_shortcuts():
            self.tree.insert('', 'end', values=(
                shortcut['shortcut'],
                shortcut['description'],
                shortcut['category']
            ))

class AddShortcutFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        ttk.Label(self, text="Shortcut:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.shortcut_entry = ttk.Entry(self, width=30)
        self.shortcut_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(self, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.desc_entry = ttk.Entry(self, width=30)
        self.desc_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(self, text="Category:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.category_combo = ttk.Combobox(self, width=27)
        self.category_combo.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        self.refresh_categories()
        
        save_btn = ttk.Button(self, text="Save Shortcut", command=self.save_shortcut)
        save_btn.grid(row=3, column=1, pady=10, sticky='e')
    
    def refresh_categories(self):
        categories = self.app.manager.get_categories()
        self.category_combo['values'] = categories
        if categories:
            self.category_combo.current(0)
    
    def save_shortcut(self):
        shortcut = self.shortcut_entry.get().strip()
        description = self.desc_entry.get().strip()
        category = self.category_combo.get().strip()
        
        if not all([shortcut, description, category]):
            messagebox.showwarning("Input Error", "All fields are required!")
            return
        
        self.app.manager.add_shortcut(shortcut, description, category)
        self.app.list_frame.refresh_list()
        self.refresh_categories()
        
        self.shortcut_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)

class QuizFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.score = 0
        self.total = 0
        
        self.question_var = tk.StringVar(value="Click 'Start Quiz' to begin")
        ttk.Label(self, textvariable=self.question_var, 
                 wraplength=400, font=('Arial', 12)).pack(pady=20)
        
        self.buttons = []
        for i in range(4):
            btn = ttk.Button(self, command=lambda idx=i: self.check_answer(idx))
            btn.pack(fill='x', padx=50, pady=5)
            self.buttons.append(btn)
        
        score_frame = ttk.Frame(self)
        score_frame.pack(pady=10)
        
        ttk.Label(score_frame, text="Score:").pack(side='left')
        self.score_var = tk.StringVar(value="0/0")
        ttk.Label(score_frame, textvariable=self.score_var).pack(side='left', padx=5)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Start Quiz", command=self.new_question).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Reset Score", command=self.reset_score).pack(side='left')
    
    def reset_score(self):
        self.score = 0
        self.total = 0
        self.score_var.set("0/0")
        self.new_question()
    
    def update_score(self):
        self.score_var.set(f"{self.score}/{self.total}")
    
    def new_question(self):
        shortcuts = self.app.manager.get_shortcuts()
        if not shortcuts:
            self.question_var.set("No shortcuts available. Add some first!")
            for btn in self.buttons:
                btn.config(text="", state='disabled')
            return
        
        self.current = random.choice(shortcuts)
        self.question_var.set(f"What does '{self.current['shortcut']}' do?")
        
        correct = self.current['description']
        wrongs = [s['description'] for s in shortcuts if s['description'] != correct]
        random.shuffle(wrongs)
        answers = [correct] + wrongs[:3]
        random.shuffle(answers)
        
        self.correct_idx = answers.index(correct)
        
        for i, btn in enumerate(self.buttons):
            if i < len(answers):
                btn.config(text=answers[i], state='normal')
            else:
                btn.config(text="", state='disabled')
    
    def check_answer(self, index):
        self.total += 1
        if index == self.correct_idx:
            self.score += 1
            result = "Correct!"
        else:
            result = f"Wrong! The correct answer was: {self.current['description']}"
        
        self.update_score()
        messagebox.showinfo("Result", result)
        self.new_question()

if __name__ == "__main__":
    app = KeysnapApp()
    app.mainloop()