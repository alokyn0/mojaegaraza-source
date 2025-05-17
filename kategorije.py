import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, Toplevel, messagebox, font
import sqlite3
import os

# Define a modern ORANGE color scheme
COLOR_BG = "#ffffff"
COLOR_FRAME_BG = "#fff5ec"
COLOR_ACCENT = "#ff8c00"  # Bright orange 
COLOR_BUTTON = "#ff8c00"  # Orange
COLOR_BUTTON_TEXT = "#ffffff"
COLOR_TEXT = "#333333"
COLOR_LIGHT_TEXT = "#666666"

class ModernButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        # Extract specific styling params or use defaults
        bg_color = kwargs.pop('bg', COLOR_BUTTON)
        fg_color = kwargs.pop('fg', COLOR_BUTTON_TEXT)
        
        # Call the parent constructor with our modified parameters
        super().__init__(
            master, 
            bg=bg_color,
            fg=fg_color,
            relief=tk.FLAT,
            padx=10,
            pady=4,
            font=('Segoe UI', 9),
            cursor="hand2",
            activebackground="#e67e00",  # Darker orange for hover
            activeforeground=COLOR_BUTTON_TEXT,
            **kwargs
        )

class CategoriesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_BG)
        self.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Configure custom styles
        self.style = ttk.Style()
        self.style.configure("Treeview", 
                             background=COLOR_BG,
                             foreground=COLOR_TEXT, 
                             rowheight=25, 
                             fieldbackground=COLOR_BG)
        self.style.configure("Treeview.Heading", 
                            font=('Segoe UI', 9, 'bold'),
                            background=COLOR_FRAME_BG,
                            foreground=COLOR_TEXT)
        self.style.map('Treeview', background=[('selected', COLOR_ACCENT)])
        
        # Initialize database if not exists
        self.initialize_db()

        # Main container with two frames
        self.main_container = tk.Frame(self, bg=COLOR_BG)
        self.main_container.pack(expand=True, fill="both")
        
        # Title for the section
        title_frame = tk.Frame(self.main_container, bg=COLOR_BG)
        title_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(title_frame, 
                text="Kategorije", 
                font=("Segoe UI", 14, "bold"), 
                bg=COLOR_BG, 
                fg=COLOR_TEXT).pack(anchor="w")

        # First Frame: Input form for adding a new category
        self.frame_input = tk.LabelFrame(self.main_container, text="Dodaj novu kategoriju", 
                            font=("Segoe UI", 10), 
                            bg=COLOR_FRAME_BG, 
                            fg=COLOR_TEXT,
                            bd=1, 
                            relief=tk.GROOVE)
        self.frame_input.pack(fill="x", pady=10, ipady=5)

        # Create a grid for the form with proper padding
        input_content = tk.Frame(self.frame_input, bg=COLOR_FRAME_BG, padx=15, pady=10)
        input_content.pack(fill="x")

        # Naziv field
        tk.Label(input_content, text="Naziv:", font=("Segoe UI", 10), bg=COLOR_FRAME_BG, fg=COLOR_TEXT).grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.entry_naziv = tk.Entry(input_content, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        self.entry_naziv.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

        # Configure column weights
        input_content.columnconfigure(1, weight=1)

        # Button container
        btn_frame = tk.Frame(self.frame_input, bg=COLOR_FRAME_BG, pady=5)
        btn_frame.pack(fill="x", padx=15)
        
        self.add_btn = ModernButton(btn_frame, text="Dodaj kategoriju", command=self.add_category)
        self.add_btn.pack(side=tk.LEFT)

        # Second Frame: Table to display the categories
        self.frame_table = tk.LabelFrame(self.main_container, text="Trenutne kategorije", 
                              font=("Segoe UI", 10), 
                              bg=COLOR_FRAME_BG, 
                              fg=COLOR_TEXT,
                              bd=1, 
                              relief=tk.GROOVE)
        self.frame_table.pack(expand=True, fill="both", pady=10)

        # Add a scrollbar to the treeview
        tree_frame = tk.Frame(self.frame_table, bg=COLOR_FRAME_BG)
        tree_frame.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Add vertical scrollbar
        scrollbar_y = ttk.Scrollbar(tree_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add horizontal scrollbar
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Naziv"), show="headings",
                                yscrollcommand=scrollbar_y.set, 
                                xscrollcommand=scrollbar_x.set)
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        self.tree.pack(expand=True, fill="both")
        
        # Configure columns
        self.tree.heading("ID", text="ID")
        self.tree.heading("Naziv", text="Naziv")
        
        # Set column widths
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Naziv", width=350)

        # Bind right-click event for context menu
        self.tree.bind("<Button-3>", self.on_right_click)

        # Load data initially
        self.load_data()
    
    def initialize_db(self):
        """Create kategorije table if it doesn't exist"""
        try:
            with sqlite3.connect("garage.db") as conn:
                cursor = conn.cursor()
                
                # Create categories table if not exists
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS kategorije (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        naziv TEXT NOT NULL UNIQUE
                    )
                ''')
                
                # Add some default categories if the table is empty
                cursor.execute("SELECT COUNT(*) FROM kategorije")
                if cursor.fetchone()[0] == 0:
                    default_categories = ["Alati", "Srafovi"]
                    for category in default_categories:
                        cursor.execute("INSERT INTO kategorije (naziv) VALUES (?)", (category,))
                
                conn.commit()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {e}")

    def add_category(self):
        """Add a new category to the database"""
        naziv = self.entry_naziv.get().strip()
        
        if not naziv:
            messagebox.showerror("Greška", "Unesite naziv kategorije")
            return
        
        try:
            with sqlite3.connect("garage.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO kategorije (naziv) VALUES (?)", (naziv,))
                conn.commit()
            
            # Clear the form
            self.entry_naziv.delete(0, tk.END)
            
            self.load_data()  # Reload the table
            messagebox.showinfo("Uspeh", "Kategorija uspešno dodata!")
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Greška", "Kategorija sa ovim nazivom već postoji")
        except Exception as e:
            messagebox.showerror("Greška", f"Greška pri dodavanju kategorije: {e}")

    def load_data(self):
        """Load categories from the database into the treeview"""
        # Clear existing rows in the treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Fetch data from the database and insert into the treeview
        try:
            with sqlite3.connect("garage.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, naziv FROM kategorije ORDER BY naziv")
                categories = cursor.fetchall()

                for category in categories:
                    self.tree.insert("", "end", values=category)
        except Exception as e:
            messagebox.showerror("Greška", f"Greška pri učitavanju podataka: {e}")
    
    def on_right_click(self, event):
        """Handle right-click on a category in the treeview"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            category_id = self.tree.item(item, "values")[0]
            self.show_right_click_menu(event, category_id)

    def show_right_click_menu(self, event, category_id):
        """Show context menu for editing or deleting a category"""
        menu = tk.Menu(self.master, tearoff=0)
        menu.add_command(label="Izmeni", command=lambda: self.edit_category(category_id))
        menu.add_command(label="Obriši", command=lambda: self.delete_category(category_id))
        menu.post(event.x_root, event.y_root)

    def edit_category(self, category_id):
        """Open a popup to edit the selected category"""
        # Get the current value for the category
        with sqlite3.connect("garage.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT naziv FROM kategorije WHERE id = ?", (category_id,))
            category = cursor.fetchone()
        
        if not category:
            messagebox.showerror("Greška", "Kategorija nije pronađena")
            return

        naziv = category[0]

        # Open an edit popup
        popup = Toplevel(self.master)
        popup.title("Izmeni kategoriju")
        popup.geometry("350x180")
        popup.configure(bg=COLOR_BG)
        popup.grab_set()  # Make the popup modal
        
        # Add icon to the popup window
        try:
            popup.iconbitmap("ico.ico")
        except:
            pass  # If icon file isn't found, continue without it
        
        # Create padding frame
        main_frame = tk.Frame(popup, bg=COLOR_BG, padx=20, pady=15)
        main_frame.pack(fill="both", expand=True)
        
        # Create a frame for the form with a subtle background
        form_frame = tk.Frame(main_frame, bg=COLOR_FRAME_BG, bd=1, relief=tk.GROOVE)
        form_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Inner padding
        inner_frame = tk.Frame(form_frame, bg=COLOR_FRAME_BG, padx=15, pady=15)
        inner_frame.pack(fill="both", expand=True)

        # Naziv field
        tk.Label(inner_frame, text="Naziv:", bg=COLOR_FRAME_BG, fg=COLOR_TEXT, font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=8)
        entry_naziv = tk.Entry(inner_frame, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        entry_naziv.insert(0, naziv)
        entry_naziv.grid(row=0, column=1, sticky="ew", pady=8, padx=5)
        entry_naziv.focus_set()  # Auto-focus the entry field

        # Configure column weights
        inner_frame.columnconfigure(1, weight=1)

        def save_changes():
            new_naziv = entry_naziv.get().strip()
            
            if not new_naziv:
                messagebox.showerror("Greška", "Unesite naziv kategorije")
                return

            # Update the category in the database
            try:
                with sqlite3.connect("garage.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE kategorije SET naziv = ? WHERE id = ?",
                                (new_naziv, category_id))
                    conn.commit()

                self.load_data()  # Reload table with updated data
                popup.destroy()
                messagebox.showinfo("Uspeh", "Kategorija uspešno izmenjena!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Greška", "Kategorija sa ovim nazivom već postoji")
            except Exception as e:
                messagebox.showerror("Greška", f"Greška pri izmeni kategorije: {e}")

        # Buttons frame
        btn_frame = tk.Frame(main_frame, bg=COLOR_BG)
        btn_frame.pack(pady=10)
        
        save_btn = ModernButton(btn_frame, text="Sačuvaj", command=save_changes)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ModernButton(btn_frame, text="Otkaži", bg="#e74c3c", command=popup.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to save function
        entry_naziv.bind("<Return>", lambda event: save_changes())

    def delete_category(self, category_id):
        """Delete the selected category from the database"""
        # Check if category is in use in zalihe table
        try:
            with sqlite3.connect("garage.db") as conn:
                cursor = conn.cursor()
                # Get category name first for the confirmation message
                cursor.execute("SELECT naziv FROM kategorije WHERE id = ?", (category_id,))
                category_name = cursor.fetchone()[0]
                
                # Check if category is in use
                cursor.execute("SELECT COUNT(*) FROM zalihe WHERE kategorija = ?", (category_name,))
                in_use_count = cursor.fetchone()[0]
                
                if in_use_count > 0:
                    messagebox.showerror(
                        "Greška", 
                        f"Kategorija '{category_name}' se koristi u zalihama i ne može biti obrisana.\n"
                        f"Broj stavki koje koriste ovu kategoriju: {in_use_count}"
                    )
                    return
                
                # Confirm deletion
                confirm = messagebox.askyesno(
                    "Potvrda brisanja", 
                    f"Da li ste sigurni da želite da obrišete kategoriju '{category_name}'?"
                )
                
                if confirm:
                    cursor.execute("DELETE FROM kategorije WHERE id = ?", (category_id,))
                    conn.commit()
                    self.load_data()  # Reload table
                    messagebox.showinfo("Uspeh", "Kategorija uspešno obrisana!")
                    
        except Exception as e:
            messagebox.showerror("Greška", f"Greška pri brisanju kategorije: {e}")