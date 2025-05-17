import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, Toplevel, messagebox, font
import sqlite3
from PIL import Image, ImageTk
import os

# Define an orange color scheme
COLOR_BG = "#ffffff"
COLOR_FRAME_BG = "#fff9f5"
COLOR_ACCENT = "#FF8C00"  # Dark Orange
COLOR_BUTTON = "#FF8C00"  # Dark Orange
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
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_BUTTON_TEXT,
            **kwargs
        )

class VrsteFrame(tk.Frame):
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
        
        # Configure styling for combobox
        self.style.configure('TCombobox', 
                             background=COLOR_BG,
                             fieldbackground=COLOR_BG)
        
        # Initialize database if not exists
        self.initialize_db()

        # Main container with two frames
        self.main_container = tk.Frame(self, bg=COLOR_BG)
        self.main_container.pack(expand=True, fill="both")
        
        # Title for the section
        title_frame = tk.Frame(self.main_container, bg=COLOR_BG)
        title_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(title_frame, 
                text="Vrste ", 
                font=("Segoe UI", 14, "bold"), 
                bg=COLOR_BG, 
                fg=COLOR_TEXT).pack(anchor="w")

        # First Frame: Input form for adding a new item
        self.frame_input = tk.LabelFrame(self.main_container, text="Dodaj novu vrstu", 
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

        # Slika field
        tk.Label(input_content, text="Slika:", font=("Segoe UI", 10), bg=COLOR_FRAME_BG, fg=COLOR_TEXT).grid(row=1, column=0, padx=5, pady=8, sticky="w")
        
        # Create a frame to hold the upload button and path label
        self.img_frame = tk.Frame(input_content, bg=COLOR_FRAME_BG)
        self.img_frame.grid(row=1, column=1, padx=5, pady=8, sticky="ew")
        
        self.img_path = None
        self.upload_btn = ModernButton(self.img_frame, text="Dodaj sliku", command=self.upload_image)
        self.upload_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Add a label to show the image path
        self.img_path_label = tk.Label(self.img_frame, text="Nema slike", bg=COLOR_FRAME_BG, fg=COLOR_LIGHT_TEXT, font=("Segoe UI", 9), anchor="w")
        self.img_path_label.pack(side=tk.LEFT, fill="x")

        # Kategorija field with a frame to hold both combobox and add button
        tk.Label(input_content, text="Kategorija:", font=("Segoe UI", 10), bg=COLOR_FRAME_BG, fg=COLOR_TEXT).grid(row=2, column=0, padx=5, pady=8, sticky="w")
        
        self.kat_frame = tk.Frame(input_content, bg=COLOR_FRAME_BG)
        self.kat_frame.grid(row=2, column=1, padx=5, pady=8, sticky="ew")
        
        # Load existing categories for the combobox
        self.categories = self.load_categories()
        self.combo_kategorija = ttk.Combobox(
            self.kat_frame,
            values=self.categories,
            font=("Segoe UI", 10),
            state="readonly"  # <-- OVA LINIJA POSTAVLJA DA MOŽE SAMO ODABIR
        )
        self.combo_kategorija.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 10))

        # Configure column weights
        input_content.columnconfigure(1, weight=1)

        # Button container
        btn_frame = tk.Frame(self.frame_input, bg=COLOR_FRAME_BG, pady=5)
        btn_frame.pack(fill="x", padx=15)
        
        self.add_btn = ModernButton(btn_frame, text="Dodaj stavku", command=self.add_item)
        self.add_btn.pack(side=tk.LEFT)

        # Second Frame: Table to display the items
        self.frame_table = tk.LabelFrame(self.main_container, text="Trenutna zaliha", 
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
        
        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Naziv", "Kategorija"), show="headings",
                                yscrollcommand=scrollbar_y.set, 
                                xscrollcommand=scrollbar_x.set)
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        self.tree.pack(expand=True, fill="both")
        
        # Configure columns
        self.tree.heading("ID", text="ID")
        self.tree.heading("Naziv", text="Naziv")
        self.tree.heading("Kategorija", text="Kategorija")
        
        # Set column widths
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Naziv", width=200)
        self.tree.column("Kategorija", width=150)

        self.tree.bind("<Button-3>", self.on_right_click)

        self.load_data()
    
    def initialize_db(self):
        """Create tables if they don't exist"""
        try:
            with sqlite3.connect("garage.db") as conn:
                cursor = conn.cursor()
                
                # Create zalihe table if not exists
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS zalihe (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        naziv TEXT NOT NULL,
                        slika TEXT,
                        kategorija TEXT NOT NULL
                    )
                ''')
                
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

    def load_categories(self):
        """Load categories from the database"""
        try:
            with sqlite3.connect("garage.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT naziv FROM kategorije ORDER BY naziv")
                categories = [row[0] for row in cursor.fetchall()]
                return categories
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load categories: {e}")
            return []
    
    def update_categories_combobox(self):
        """Update the categories combobox with fresh data"""
        self.categories = self.load_categories()
        self.combo_kategorija['values'] = self.categories
    
    def add_category(self):
        """Open dialog to add a new category"""
        popup = Toplevel(self.master)
        popup.title("Nova kategorija")
        popup.geometry("350x150")
        popup.configure(bg=COLOR_BG)
        popup.grab_set()  # Make the popup modal
        
        # Set icon
        try:
            popup.iconbitmap("ico.ico")
        except:
            pass
        
        # Create padding frame
        main_frame = tk.Frame(popup, bg=COLOR_BG, padx=20, pady=15)
        main_frame.pack(fill="both", expand=True)
        
        # Create input form
        input_frame = tk.Frame(main_frame, bg=COLOR_FRAME_BG, bd=1, relief=tk.GROOVE, padx=15, pady=15)
        input_frame.pack(fill="both", expand=True)
        
        # Naziv field
        tk.Label(input_frame, text="Naziv kategorije:", bg=COLOR_FRAME_BG, fg=COLOR_TEXT, font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=8)
        entry_naziv = tk.Entry(input_frame, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        entry_naziv.grid(row=0, column=1, sticky="ew", pady=8, padx=5)
        entry_naziv.focus_set()  # Auto-focus the entry field
        
        input_frame.columnconfigure(1, weight=1)
        
        def save_category():
            naziv = entry_naziv.get().strip()
            if not naziv:
                messagebox.showerror("Greška", "Unesite naziv kategorije")
                return
            
            try:
                with sqlite3.connect("garage.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO kategorije (naziv) VALUES (?)", (naziv,))
                    conn.commit()
                
                self.update_categories_combobox()
                self.combo_kategorija.set(naziv)  # Select the newly added category
                popup.destroy()
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Greška", "Kategorija sa ovim nazivom već postoji")
            except Exception as e:
                messagebox.showerror("Greška", f"Greška pri dodavanju kategorije: {e}")
        
        # Buttons
        btn_frame = tk.Frame(main_frame, bg=COLOR_BG, pady=10)
        btn_frame.pack(fill="x")
        
        save_btn = ModernButton(btn_frame, text="Sačuvaj", command=save_category)
        save_btn.pack(side=tk.LEFT)
        
        cancel_btn = ModernButton(btn_frame, text="Otkaži", bg="#e74c3c", command=popup.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to save function
        entry_naziv.bind("<Return>", lambda event: save_category())

    def upload_image(self):
        # Open file dialog to select image
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        if path:
            self.img_path = path
            # Display filename instead of full path for cleaner UI
            filename = os.path.basename(path)
            self.img_path_label.config(text=filename)
            return path
        return None
    
    def add_item(self):
        naziv = self.entry_naziv.get().strip()
        kategorija = self.combo_kategorija.get().strip()
        
        if not naziv:
            messagebox.showerror("Greška", "Unesite naziv")
            return
        
        if not kategorija:
            messagebox.showerror("Greška", "Izaberite ili kreirajte kategoriju")
            return
        
        if not self.img_path:
            messagebox.showerror("Greška", "Izaberite sliku")
            return
        
        try:
            # Insert the new item into the `zalihe` table
            with sqlite3.connect("garage.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO zalihe (naziv, slika, kategorija) VALUES (?, ?, ?)", 
                               (naziv, self.img_path, kategorija))
                conn.commit()
            
            # Clear the form
            self.entry_naziv.delete(0, tk.END)
            self.combo_kategorija.set('')
            self.img_path = None
            self.img_path_label.config(text="Nema slike")
            
            self.load_data()  # Reload the table
            messagebox.showinfo("Uspeh", "Stavka uspešno dodata!")

        except Exception as e:
            messagebox.showerror("Greška", f"Greška pri dodavanju stavke: {e}")

    def load_data(self):
        # Clear existing rows in the treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Fetch data from the database and insert into the treeview
        try:
            with sqlite3.connect("garage.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, naziv, kategorija FROM zalihe")
                records = cursor.fetchall()

                for record in records:
                    self.tree.insert("", "end", values=record)
        except Exception as e:
            messagebox.showerror("Greška", f"Greška pri učitavanju podataka: {e}")
    
    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            product_id = self.tree.item(item, "values")[0]
            self.show_right_click_menu(event, product_id)

    def show_right_click_menu(self, event, product_id):
        # Create a context menu for editing or deleting
        menu = tk.Menu(self.master, tearoff=0)
        menu.add_command(label="Izmeni", command=lambda: self.edit_item(product_id))
        menu.add_command(label="Obriši", command=lambda: self.delete_item(product_id))
        menu.post(event.x_root, event.y_root)

    def edit_item(self, product_id):
        # Get the current values for the item
        with sqlite3.connect("garage.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT naziv, kategorija, slika FROM zalihe WHERE id = ?", (product_id,))
            item = cursor.fetchone()
        
        if not item:
            messagebox.showerror("Greška", "Stavka nije pronađena")
            return

        naziv, kategorija, slika = item

        # Open an edit popup
        popup = Toplevel(self.master)
        popup.title("Izmeni stavku")
        popup.geometry("400x300")
        popup.configure(bg=COLOR_BG)
        popup.grab_set()  # Make the popup modal
        
        # Set icon
        try:
            popup.iconbitmap("ico.ico")
        except:
            pass
        
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

        # Kategorija field
        tk.Label(inner_frame, text="Kategorija:", bg=COLOR_FRAME_BG, fg=COLOR_TEXT, font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=8)
        
        # Create a frame for the category selection in edit mode
        edit_kat_frame = tk.Frame(inner_frame, bg=COLOR_FRAME_BG)
        edit_kat_frame.grid(row=1, column=1, sticky="ew", pady=8, padx=5)
        
        # Get updated list of categories
        categories = self.load_categories()
        combo_kategorija = ttk.Combobox(edit_kat_frame, values=categories, font=("Segoe UI", 10))
        combo_kategorija.set(kategorija)
        combo_kategorija.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 10))
        
        # Add button for creating a new category in edit mode
        def add_category_from_edit():
            # Create a temporary function to add new category from edit popup
            popup_add_cat = Toplevel(popup)
            popup_add_cat.title("Nova kategorija")
            popup_add_cat.geometry("350x150")
            popup_add_cat.configure(bg=COLOR_BG)
            popup_add_cat.grab_set()  # Make the popup modal
            
            # Set icon
            try:
                popup_add_cat.iconbitmap("ico.ico")
            except:
                pass
            
            # Create padding frame
            cat_main_frame = tk.Frame(popup_add_cat, bg=COLOR_BG, padx=20, pady=15)
            cat_main_frame.pack(fill="both", expand=True)
            
            # Create input form
            cat_input_frame = tk.Frame(cat_main_frame, bg=COLOR_FRAME_BG, bd=1, relief=tk.GROOVE, padx=15, pady=15)
            cat_input_frame.pack(fill="both", expand=True)
            
            # Naziv field
            tk.Label(cat_input_frame, text="Naziv kategorije:", bg=COLOR_FRAME_BG, fg=COLOR_TEXT, font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=8)
            cat_entry_naziv = tk.Entry(cat_input_frame, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
            cat_entry_naziv.grid(row=0, column=1, sticky="ew", pady=8, padx=5)
            cat_entry_naziv.focus_set()
            
            cat_input_frame.columnconfigure(1, weight=1)
            
            def save_new_category():
                new_cat_name = cat_entry_naziv.get().strip()
                if not new_cat_name:
                    messagebox.showerror("Greška", "Unesite naziv kategorije")
                    return
                
                try:
                    with sqlite3.connect("garage.db") as conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO kategorije (naziv) VALUES (?)", (new_cat_name,))
                        conn.commit()
                    
                    # Update categories in the edit dialog
                    updated_categories = self.load_categories()
                    combo_kategorija['values'] = updated_categories
                    combo_kategorija.set(new_cat_name)
                    popup_add_cat.destroy()
                    
                except sqlite3.IntegrityError:
                    messagebox.showerror("Greška", "Kategorija sa ovim nazivom već postoji")
                except Exception as e:
                    messagebox.showerror("Greška", f"Greška pri dodavanju kategorije: {e}")
            
            # Buttons
            cat_btn_frame = tk.Frame(cat_main_frame, bg=COLOR_BG, pady=10)
            cat_btn_frame.pack(fill="x")
            
            save_cat_btn = ModernButton(cat_btn_frame, text="Sačuvaj", command=save_new_category)
            save_cat_btn.pack(side=tk.LEFT)
            
            cancel_cat_btn = ModernButton(cat_btn_frame, text="Otkaži", bg="#e74c3c", command=popup_add_cat.destroy)
            cancel_cat_btn.pack(side=tk.LEFT, padx=5)
            
            # Bind Enter key to save function
            cat_entry_naziv.bind("<Return>", lambda event: save_new_category())

        # Slika field
        tk.Label(inner_frame, text="Slika:", bg=COLOR_FRAME_BG, fg=COLOR_TEXT, font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", pady=8)
        
        # Create a frame for image selection
        img_frame = tk.Frame(inner_frame, bg=COLOR_FRAME_BG)
        img_frame.grid(row=2, column=1, sticky="ew", pady=8, padx=5)
        
        # Store the image path in the edit popup scope
        edit_img_path = tk.StringVar(value=slika if slika else "")
        
        # Display filename instead of full path
        display_text = os.path.basename(slika) if slika else "Nema slike"
        img_path_label = tk.Label(img_frame, text=display_text, bg=COLOR_FRAME_BG, fg=COLOR_LIGHT_TEXT, font=("Segoe UI", 9), anchor="w")
        img_path_label.pack(side=tk.RIGHT, fill="x", expand=True)

        def update_edit_image():
            path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
            if path:
                edit_img_path.set(path)
                filename = os.path.basename(path)
                img_path_label.config(text=filename)

        upload_btn = ModernButton(img_frame, text="Učitaj", command=update_edit_image)
        upload_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Configure column weights
        inner_frame.columnconfigure(1, weight=1)

        def save_changes():
            new_naziv = entry_naziv.get().strip()
            new_kategorija = combo_kategorija.get().strip()
            new_img_path = edit_img_path.get()
            
            if not new_naziv:
                messagebox.showerror("Greška", "Unesite naziv")
                return
                
            if not new_kategorija:
                messagebox.showerror("Greška", "Izaberite ili kreirajte kategoriju")
                return
                
            if not new_img_path:
                messagebox.showerror("Greška", "Izaberite sliku")
                return

            # Update the item in the database
            try:
                with sqlite3.connect("garage.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE zalihe SET naziv = ?, kategorija = ?, slika = ? WHERE id = ?",
                                (new_naziv, new_kategorija, new_img_path, product_id))
                    conn.commit()

                self.load_data()  # Reload table with updated data
                popup.destroy()
                messagebox.showinfo("Uspeh", "Stavka uspešno izmenjena!")
            except Exception as e:
                messagebox.showerror("Greška", f"Greška pri izmeni stavke: {e}")

        # Buttons frame
        btn_frame = tk.Frame(main_frame, bg=COLOR_BG)
        btn_frame.pack(pady=10)
        
        save_btn = ModernButton(btn_frame, text="Sačuvaj", command=save_changes)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ModernButton(btn_frame, text="Otkaži", bg="#e74c3c", command=popup.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def delete_item(self, product_id):
        # Confirm deletion
        confirm = messagebox.askyesno("Potvrda brisanja", "Da li ste sigurni da želite da obrišete ovu stavku?")
        if confirm:
            try:
                with sqlite3.connect("garage.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM zalihe WHERE id = ?", (product_id,))
                    conn.commit()

                self.load_data()  # Reload table
                messagebox.showinfo("Uspeh", "Stavka uspešno obrisana!")

            except Exception as e:
                messagebox.showerror("Greška", f"Greška pri brisanju stavke: {e}")

    def delete_all_categories(self):
        """For testing purposes - deletes all categories"""
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete ALL categories?")
        if confirm:
            try:
                with sqlite3.connect("garage.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM kategorije")
                    conn.commit()
                self.update_categories_combobox()
            except Exception as e:
                messagebox.showerror("Error", f"Error while deleting categories: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Upravljanje zalihama")
    root.geometry("700x500")
    
    # Set icon
    try:
        root.iconbitmap("ico.ico")  # Using ico.ico as requested
    except:
        pass
    
    app = VrsteFrame(root)
    app.mainloop()