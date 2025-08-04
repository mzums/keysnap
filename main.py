import tkinter as tk
from tkinter import ttk

class ShortcutManager:
    def __init__(self):
        self.shortcuts = []
        self.categories = []
    
    def add_shortcut(self, shortcut, description, category):
        if category not in self.categories:
            self.categories.append(category)
        self.shortcuts.append({
            'shortcut': shortcut,
            'description': description,
            'category': category
        })
    
    def get_shortcuts(self):
        return self.shortcuts.copy()
    
    def get_categories(self):
        return self.categories.copy()

class KeysnapApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Keysnap - Stage 1")
        self.geometry("600x400")
        
        self.manager = ShortcutManager()
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.list_frame = ShortcutListFrame(self.notebook, self)
        self.add_frame = AddShortcutFrame(self.notebook, self)
        
        self.notebook.add(self.list_frame, text='Shortcut List')
        self.notebook.add(self.add_frame, text='Add Shortcut')
        
        self.manager.add_shortcut("Ctrl+C", "Copy", "General")
        self.manager.add_shortcut("Ctrl+V", "Paste", "General")
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
        self.category_entry = ttk.Entry(self, width=30)
        self.category_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        save_btn = ttk.Button(self, text="Save Shortcut", command=self.save_shortcut)
        save_btn.grid(row=3, column=1, pady=10, sticky='e')
    
    def save_shortcut(self):
        shortcut = self.shortcut_entry.get().strip()
        description = self.desc_entry.get().strip()
        category = self.category_entry.get().strip()
        
        if shortcut and description and category:
            self.app.manager.add_shortcut(shortcut, description, category)
            self.app.list_frame.refresh_list()
            
            self.shortcut_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
            self.category_entry.delete(0, tk.END)

if __name__ == "__main__":
    app = KeysnapApp()
    app.mainloop()
