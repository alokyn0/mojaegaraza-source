import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import Toplevel, Label, Button, Frame, messagebox
from PIL import Image, ImageTk
import time  # For retrying the database operation
import os
import pandas as pd
from datetime import datetime

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

class ZaliheFrame(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master, bg=COLOR_BG)
        self.master = master
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

        # Title for the section with export button
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill="x", pady=(0, 10))
        
        # Use grid for better control of element placement
        title_frame.columnconfigure(0, weight=1)  # Title will expand
        title_frame.columnconfigure(1, weight=0)  # Button stays fixed size
        
        tk.Label(title_frame, 
                text="Zalihe", 
                font=("Segoe UI", 14, "bold"), 
                bg=COLOR_BG, 
                fg=COLOR_TEXT).grid(row=0, column=0, sticky="w")
        
        # Export button positioned on the right
        export_btn = ModernButton(title_frame, text="Export", command=self.export_to_excel)
        export_btn.grid(row=0, column=1, sticky="e")
        
        # Create frame for the treeview
        self.frame_table = tk.LabelFrame(self, text="Pregled Zaliha", 
                              font=("Segoe UI", 10), 
                              bg=COLOR_FRAME_BG, 
                              fg=COLOR_TEXT,
                              bd=1, 
                              relief=tk.GROOVE)
        self.frame_table.pack(expand=True, fill="both", pady=10)
        
        # Create a frame for the treeview and scrollbars
        tree_frame = tk.Frame(self.frame_table, bg=COLOR_FRAME_BG)
        tree_frame.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Add vertical scrollbar
        scrollbar_y = ttk.Scrollbar(tree_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add horizontal scrollbar
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create the treeview
        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Naziv", "Kategorija", "Stanje"), show="headings",
                                yscrollcommand=scrollbar_y.set,
                                xscrollcommand=scrollbar_x.set)
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        self.tree.pack(expand=True, fill="both")

        # Configure columns
        self.tree.heading("ID", text="ID", command=lambda: self.on_column_click("ID"))
        self.tree.heading("Naziv", text="Naziv", command=lambda: self.on_column_click("Naziv"))
        self.tree.heading("Kategorija", text="Kategorija", command=lambda: self.on_column_click("Kategorija"))
        self.tree.heading("Stanje", text="Stanje")
        
        # Set column widths
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Naziv", width=200)
        self.tree.column("Kategorija", width=150)
        self.tree.column("Stanje", width=80, anchor="center")

        self.tree.bind("<Button-3>", self.on_right_click)  # Right-click binding
        self.tree.bind("<Double-1>", self.on_double_click)  # Double-click binding

        self.load_data()

    def export_to_excel(self):
        try:
            # Create Documents/Garaza directory if it doesn't exist
            documents_path = os.path.join(os.path.expanduser("~"), "Documents")
            garaza_path = os.path.join(documents_path, "Garaza")
            
            if not os.path.exists(garaza_path):
                os.makedirs(garaza_path)
            
            # Get current date and time for filename
            current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"export-{current_datetime}.xlsx"
            filepath = os.path.join(garaza_path, filename)
            
            # Get data from database
            with sqlite3.connect("garage.db") as conn:
                # Read directly into pandas DataFrame
                df = pd.read_sql_query("SELECT id, naziv, kategorija, stanje FROM zalihe", conn)
                
                # Rename columns for better Excel formatting
                df.columns = ['ID', 'Naziv', 'Kategorija', 'Stanje']
                
                # Export to Excel
                df.to_excel(filepath, index=False, engine='openpyxl')
            
            # Show success message
            messagebox.showinfo("Uspešno", f"Podaci uspešno exportovani u:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("Greška", f"Greška prilikom exportovanja: {str(e)}")

    def on_double_click(self, event):
        item = self.tree.selection()
        if item:
            product_id = self.tree.item(item, "values")[0]
            self.show_product_details(product_id)

    def load_data(self):
        with sqlite3.connect("garage.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, naziv, kategorija, stanje FROM zalihe")
            for record in cursor.fetchall():
                self.tree.insert("", "end", values=record)

    def on_column_click(self, column):
        if column == "ID":
            self.open_id_popup()
        elif column == "Naziv":
            self.open_naziv_popup()
        elif column == "Kategorija":
            self.open_kategorija_popup()

    def open_id_popup(self):
        popup = tk.Toplevel(self.master)
        popup.iconbitmap("ico.ico")
        popup.title("Pretraga po ID-u")
        popup.geometry("300x150")
        popup.configure(bg=COLOR_BG)
        popup.grab_set()

        # Create a centered frame with padding
        frame = tk.Frame(popup, bg=COLOR_BG, padx=20, pady=20)
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="Unesite ID proizvoda:", 
                font=("Segoe UI", 10), 
                bg=COLOR_BG, 
                fg=COLOR_TEXT).pack(pady=(0, 10))
                
        entry_id = tk.Entry(frame, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        entry_id.pack(fill="x", pady=(0, 15))

        def search_by_id(event=None):
            self.show_product_details(entry_id.get(), popup)

        button_frame = tk.Frame(frame, bg=COLOR_BG)
        button_frame.pack()
        
        search_btn = ModernButton(button_frame, text="Pretraži", command=search_by_id)
        search_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ModernButton(button_frame, text="Odustani", bg="#e74c3c", command=popup.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        entry_id.bind("<Return>", search_by_id)
        entry_id.focus()
        popup.bind("<Escape>", lambda e: popup.destroy())

    def show_product_details(self, product_id, parent_popup=None):
        with sqlite3.connect("garage.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM zalihe WHERE id = ?", (product_id,))
            record = cursor.fetchone()

        if record:
            id_, naziv, slika, kategorija, stanje = record

            dp = Toplevel(self.master)
            dp.title(f"Proizvod {id_}")
            dp.iconbitmap("ico.ico")
            dp.geometry("650x400")
            dp.configure(bg=COLOR_BG)
            dp.resizable(False, False)
            dp.grab_set()

            # Title
            tk.Label(dp, text="DETALJI O PROIZVODU", 
                    font=("Segoe UI", 16, "bold"), 
                    bg=COLOR_BG, 
                    fg=COLOR_TEXT).pack(pady=(15, 10))
                    
            # Content container
            content = Frame(dp, bg=COLOR_BG)
            content.pack(fill="both", expand=True, padx=20, pady=10)
            content.columnconfigure(0, weight=1)
            content.columnconfigure(1, weight=0)

            # Details frame
            d = Frame(content, bg=COLOR_BG)
            d.grid(row=0, column=0, sticky="n")

            for i, (label, value) in enumerate([("ID:", id_), ("Naziv:", naziv),
                                                ("Kategorija:", kategorija), ("Stanje:", stanje)]):
                tk.Label(d, text=label, font=("Segoe UI", 12, "bold"), 
                       bg=COLOR_BG, fg=COLOR_TEXT).grid(row=i, column=0, sticky="w", pady=8)
                       
                value_label = tk.Label(d, text=str(value), font=("Segoe UI", 12),
                                    width=25, anchor="w", bg=COLOR_FRAME_BG, 
                                    relief="solid", bd=1, padx=8, pady=4)
                value_label.grid(row=i, column=1, pady=8, padx=(10, 0))

            # Image frame with border
            img_frame = Frame(content, relief="solid", bd=1, width=150, height=150, bg=COLOR_FRAME_BG)
            img_frame.grid(row=0, column=1, sticky="n", padx=(30, 0))
            
            # Handle image display
            if slika:
                try:
                    img = Image.open(slika)
                    img.thumbnail((150, 150))
                    img_tk = ImageTk.PhotoImage(img)
                    tk.Label(img_frame, image=img_tk, bg=COLOR_FRAME_BG).pack(padx=5, pady=5)
                    dp.img_ref = img_tk  # Keep a reference to prevent garbage collection
                except Exception as e:
                    tk.Label(img_frame, text="Greška pri učitavanju slike", 
                           bg=COLOR_FRAME_BG, fg=COLOR_TEXT,
                           font=("Segoe UI", 9)).pack(expand=True, padx=10, pady=10)
            else:
                tk.Label(img_frame, text="Slika nije dostupna", 
                       bg=COLOR_FRAME_BG, fg=COLOR_TEXT,
                       font=("Segoe UI", 9)).pack(expand=True, padx=10, pady=10)

            # Button at bottom
            btn_frame = Frame(dp, bg=COLOR_BG)
            btn_frame.pack(pady=15, side="bottom")
            
            ok_btn = ModernButton(btn_frame, text="OK", 
                                command=lambda: [dp.destroy(), parent_popup.destroy() if parent_popup else None])
            ok_btn.pack()
            
        else:
            # Error popup when product not found
            error = Toplevel(self.master)
            error.title("Greška")
            error.geometry("300x150")
            error.configure(bg=COLOR_BG)
            error.grab_set()
            
            frame = Frame(error, bg=COLOR_BG, padx=20, pady=20)
            frame.pack(expand=True, fill="both")
            
            Label(frame, text="Ne postoji proizvod sa tim ID-om.", 
                 font=("Segoe UI", 12), bg=COLOR_BG, fg=COLOR_TEXT).pack(pady=(0, 15))
                 
            ok_btn = ModernButton(frame, text="OK", 
                               command=lambda: [error.destroy(), parent_popup.destroy() if parent_popup else None])
            ok_btn.pack()

    def open_naziv_popup(self):
        popup = tk.Toplevel(self.master)
        popup.title("Pretraga po Nazivu")
        popup.geometry("300x150")
        popup.configure(bg=COLOR_BG)
        popup.grab_set()
        popup.iconbitmap("ico.ico")

        # Create a centered frame with padding
        frame = tk.Frame(popup, bg=COLOR_BG, padx=20, pady=20)
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="Unesite naziv proizvoda:", 
                font=("Segoe UI", 10), 
                bg=COLOR_BG, 
                fg=COLOR_TEXT).pack(pady=(0, 10))
                
        entry = tk.Entry(frame, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        entry.pack(fill="x", pady=(0, 15))

        def search(event=None):
            naziv = entry.get()
            print(f"Searching for products with naziv: {naziv}")  # Debugging statement
            popup.destroy()
            self.open_filtered_table(naziv_filter=naziv)

        button_frame = tk.Frame(frame, bg=COLOR_BG)
        button_frame.pack()
        
        search_btn = ModernButton(button_frame, text="Pretraži", command=search)
        search_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ModernButton(button_frame, text="Odustani", bg="#e74c3c", command=popup.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        entry.bind("<Return>", search)
        entry.focus()
        popup.bind("<Escape>", lambda e: popup.destroy())

    def open_kategorija_popup(self):
        # Get unique categories from database
        with sqlite3.connect("garage.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT kategorija FROM zalihe")
            categories = [row[0] for row in cursor.fetchall()]
        
        if not categories:
            messagebox.showinfo("Info", "Nema dostupnih kategorija u bazi.")
            return
            
        popup = tk.Toplevel(self.master)
        popup.title("Pretraga po Kategoriji")
        popup.geometry("300x250")
        popup.configure(bg=COLOR_BG)
        popup.iconbitmap("ico.ico")
        popup.grab_set()

        # Create a centered frame with padding
        frame = tk.Frame(popup, bg=COLOR_BG, padx=20, pady=20)
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="Izaberite kategoriju:", 
                font=("Segoe UI", 10), 
                bg=COLOR_BG, 
                fg=COLOR_TEXT).pack(pady=(0, 10))
        
        # Create a listbox with scrollbar
        list_frame = tk.Frame(frame, bg=COLOR_BG)
        list_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, 
                          font=("Segoe UI", 10),
                          bd=1,
                          relief=tk.SOLID,
                          selectbackground=COLOR_ACCENT,
                          selectforeground=COLOR_BUTTON_TEXT,
                          yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Insert categories into listbox
        for category in categories:
            listbox.insert(tk.END, category)

        def search():
            selection = listbox.curselection()
            if selection:
                category = listbox.get(selection[0])
                popup.destroy()
                self.open_filtered_table(kategorija_filter=category)
            else:
                messagebox.showinfo("Info", "Molimo izaberite kategoriju.")

        button_frame = tk.Frame(frame, bg=COLOR_BG)
        button_frame.pack(pady=10)
        
        search_btn = ModernButton(button_frame, text="Pretraži", command=search)
        search_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ModernButton(button_frame, text="Odustani", bg="#e74c3c", command=popup.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Double-click to select and search
        listbox.bind("<Double-1>", lambda e: search())
        
        popup.bind("<Escape>", lambda e: popup.destroy())

    def open_filtered_table(self, naziv_filter=None, kategorija_filter=None):
        window = Toplevel(self.master)
        window.title("Rezultati pretrage")
        window.geometry("700x400")
        window.iconbitmap("ico.ico")
        window.configure(bg=COLOR_BG)
        window.grab_set()

        # Title label
        if naziv_filter:
            title_text = f"Rezultati pretrage za naziv: '{naziv_filter}'"
        elif kategorija_filter:
            title_text = f"Rezultati pretrage za kategoriju: '{kategorija_filter}'"
        else:
            title_text = "Rezultati pretrage"
            
        title_frame = tk.Frame(window, bg=COLOR_BG)
        title_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(title_frame, text=title_text, 
                font=("Segoe UI", 12, "bold"), 
                bg=COLOR_BG, 
                fg=COLOR_TEXT).pack(anchor="w")

        # Frame for the treeview
        tree_frame = tk.LabelFrame(window, text="Pronađeni proizvodi", 
                              font=("Segoe UI", 10), 
                              bg=COLOR_FRAME_BG, 
                              fg=COLOR_TEXT,
                              bd=1, 
                              relief=tk.GROOVE)
        tree_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Create a frame for the treeview and scrollbars
        inner_frame = tk.Frame(tree_frame, bg=COLOR_FRAME_BG)
        inner_frame.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Add vertical scrollbar
        scrollbar_y = ttk.Scrollbar(inner_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add horizontal scrollbar
        scrollbar_x = ttk.Scrollbar(inner_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Create the filtered tree
        tree = ttk.Treeview(inner_frame, columns=("ID", "Naziv", "Kategorija", "Stanje"), show="headings",
                           yscrollcommand=scrollbar_y.set,
                           xscrollcommand=scrollbar_x.set)
        scrollbar_y.config(command=tree.yview)
        scrollbar_x.config(command=tree.xview)
        tree.pack(expand=True, fill="both")

        # Configure columns
        for col in ("ID", "Naziv", "Kategorija", "Stanje"):
            tree.heading(col, text=col)
            
        # Set column widths
        tree.column("ID", width=50, anchor="center")
        tree.column("Naziv", width=200)
        tree.column("Kategorija", width=150)
        tree.column("Stanje", width=80, anchor="center")

        # Get results from database
        with sqlite3.connect("garage.db") as conn:
            cursor = conn.cursor()

            if naziv_filter:
                cursor.execute("SELECT id, naziv, kategorija, stanje FROM zalihe WHERE naziv LIKE ?", ('%' + naziv_filter + '%',))
            elif kategorija_filter:
                cursor.execute("SELECT id, naziv, kategorija, stanje FROM zalihe WHERE kategorija = ?", (kategorija_filter,))
            results = cursor.fetchall()

        # Insert results into the tree
        for record in results:
            tree.insert("", "end", values=record)

        # Show result count in the title
        tk.Label(title_frame, text=f"Ukupno pronađeno: {len(results)}", 
                font=("Segoe UI", 10), 
                bg=COLOR_BG, 
                fg=COLOR_LIGHT_TEXT).pack(anchor="w")

        # Button at the bottom
        button_frame = tk.Frame(window, bg=COLOR_BG)
        button_frame.pack(pady=10)
        
        close_btn = ModernButton(button_frame, text="Zatvori", command=window.destroy)
        close_btn.pack()

        def on_double_click(event):
            item = tree.selection()
            if item:
                product_id = tree.item(item, "values")[0]
                self.show_product_details(product_id, parent_popup=window)

        tree.bind("<Double-1>", on_double_click)

        # Bind the right-click event to show the context menu on filtered tree
        tree.bind("<Button-3>", lambda event: self.on_right_click_filtered(event, tree))

    def on_right_click_filtered(self, event, tree):
        # Get the item under the cursor (selected item)
        item = tree.identify_row(event.y)

        # If an item is selected, proceed with showing the menu
        if item:
            # Now we are using the correct `item` for this row
            product_id = tree.item(item, "values")[0]  # Get the product ID from the selected row

            # Show the context menu (or other options)
            self.show_right_click_menu(event, product_id)

    def on_right_click(self, event):
        # Get the item under the cursor (selected item)
        item = self.tree.identify_row(event.y)

        # If an item is selected, proceed with showing the menu
        if item:
            # Now we are using the correct `item` for this row
            product_id = self.tree.item(item, "values")[0]  # Get the product ID from the selected row
            
            # Show the context menu (or other options)
            self.show_right_click_menu(event, product_id)

    def show_right_click_menu(self, event, product_id):
        # Create a context menu on right-click with modern styling
        menu = tk.Menu(self.master, tearoff=0, bg=COLOR_FRAME_BG, fg=COLOR_TEXT,
                      activebackground=COLOR_ACCENT, activeforeground=COLOR_BUTTON_TEXT,
                      relief=tk.FLAT, bd=1)
                      
        menu.add_command(label="Vidi detalje", command=lambda: self.show_product_details(product_id))
        menu.add_command(label="Azuriraj Stanje", command=lambda: self.save_status(product_id))
        
        # Position the menu at the mouse cursor location
        menu.post(event.x_root, event.y_root)

    def save_status(self, product_id):
        popup = tk.Toplevel(self.master)
        popup.title("Unesite količinu")
        popup.geometry("300x150")
        popup.iconbitmap("ico.ico")
        popup.configure(bg=COLOR_BG)
        popup.grab_set()
        popup.resizable(False, False)

        # Create a centered frame with padding
        frame = tk.Frame(popup, bg=COLOR_BG, padx=20, pady=20)
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="Unesite broj količine:", 
                font=("Segoe UI", 10), 
                bg=COLOR_BG, 
                fg=COLOR_TEXT).pack(pady=(0, 10))

        # Dohvati trenutno stanje iz baze
        conn = sqlite3.connect("garage.db")
        cursor = conn.cursor()
        cursor.execute("SELECT stanje FROM zalihe WHERE id = ?", (product_id,))
        result = cursor.fetchone()
        conn.close()

        # Podrazumevana vrednost (npr. 0 ako nije nađeno)
        current_status = str(result[0]) if result else "0"

        entry_status = tk.Entry(frame, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        entry_status.insert(0, current_status)
        entry_status.pack(fill="x", pady=(0, 15))
        
        # Error label that will be shown if input is invalid
        error_label = tk.Label(frame, text="", font=("Segoe UI", 9), 
                             bg=COLOR_BG, fg="#e74c3c")
        error_label.pack()

        def update_status(event=None):
            try:
                new_status = int(entry_status.get())  # Ensure it's a number
                if new_status < 0:
                    error_label.config(text="Količina ne može biti negativna")
                    return
                self.update_product_status(product_id, new_status)
                popup.destroy()
            except ValueError:
                # Show an error if input is not a valid number
                error_label.config(text="Molimo unesite važeći broj")

        button_frame = tk.Frame(frame, bg=COLOR_BG)
        button_frame.pack(pady=(5, 0))
        
        update_btn = ModernButton(button_frame, text="Ažuriraj", command=update_status)
        update_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ModernButton(button_frame, text="Odustani", bg="#e74c3c", command=popup.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        entry_status.bind("<Return>", update_status)
        entry_status.focus()
        popup.bind("<Escape>", lambda e: popup.destroy())

    def update_product_status(self, product_id, new_status):
        for _ in range(3):  # Retry 3 times
            try:
                # Open connection within the try block
                conn = sqlite3.connect("garage.db")
                cursor = conn.cursor()

                # Check if the product exists before attempting to update
                cursor.execute("SELECT 1 FROM zalihe WHERE id = ?", (product_id,))
                if cursor.fetchone() is None:
                    messagebox.showerror("Greška", f"Proizvod sa ID {product_id} ne postoji.")
                    conn.close()
                    return

                # Perform the update query
                cursor.execute("UPDATE zalihe SET stanje = ? WHERE id = ?", (new_status, product_id))
                conn.commit()
                conn.close()  # Close the connection after commit

                # Close all open windows except the main one
                self.close_all_windows()

                # Show success message
                messagebox.showinfo("Uspeh", f"Stanje proizvoda je ažurirano na {new_status}.")
                
                self.reload_data()

                break  # If update is successful, exit loop
            except sqlite3.OperationalError:
                time.sleep(1)  # Wait for a second and retry if database is locked
            except Exception as e:
                messagebox.showerror("Greška", f"Greška pri ažuriranju: {e}")
                break

    def close_all_windows(self):
        # Close all child windows (popups, detail views, etc.) except the main window
        for window in self.master.winfo_children():
            if isinstance(window, Toplevel):  # Toplevel windows are child windows
                window.destroy()

    def reload_data(self):
        # Clear the existing rows in the Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Re-load the data from the database and update the Treeview
        with sqlite3.connect("garage.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, naziv, kategorija, stanje FROM zalihe")
            for record in cursor.fetchall():
                self.tree.insert("", "end", values=record)


#
if __name__ == "__main__":
    root = tk.Tk()
    
    # Set icon (if available)
    try:
        root.iconbitmap("icon.ico")  # Replace with your icon path if you have one
    except:
        pass