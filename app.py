import tkinter as tk
from tkinter import ttk
import time
import sqlite3
import os
from datetime import datetime
from vrste import VrsteFrame
from zalihe import ZaliheFrame
from kategorije import CategoriesFrame
from tkinter import messagebox

# Define a modern orange color scheme
COLOR_BG = "#ffffff"
COLOR_FRAME_BG = "#f9f9f9"
COLOR_ACCENT = "#FF8C00"  # Dark Orange
COLOR_BUTTON = "#FF8C00"  # Dark Orange
COLOR_BUTTON_TEXT = "#ffffff"
COLOR_TEXT = "#333333"
COLOR_LIGHT_TEXT = "#666666"
COLOR_SECONDARY = "#FFA500"  # Orange
COLOR_ACCENT_LIGHT = "#FFD700"  # Gold accent for highlights

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
            activebackground=COLOR_SECONDARY,
            activeforeground=COLOR_BUTTON_TEXT,
            **kwargs
        )
        
        # Add hover effect
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
    def on_enter(self, e):
        self.config(bg=COLOR_SECONDARY)
        
    def on_leave(self, e):
        self.config(bg=COLOR_BUTTON)

class FilteredProductsWindow(tk.Toplevel):
    def __init__(self, parent, filter_type):
        super().__init__(parent)
        self.filter_type = filter_type
        
        # Set window properties
        if filter_type == "low_stock":
            self.title("Proizvodi - Još malo pa nestalo")
            self.filter_condition = "z.stanje BETWEEN 1 AND 10"
            self.iconbitmap("ico.ico")
            self.sort_order = "z.stanje ASC"
            self.export_prefix = "jmpn"
        else:  # out_of_stock
            self.title("Proizvodi - Nestalo")
            self.filter_condition = "z.stanje = 0"
            self.iconbitmap("ico.ico")
            self.sort_order = "z.naziv"
            self.export_prefix = "nestalo"
            
        self.geometry("800x500")
        self.configure(bg=COLOR_BG)
        
        # Create main container
        main_frame = tk.Frame(self, bg=COLOR_BG, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title and description
        title_frame = tk.Frame(main_frame, bg=COLOR_BG)
        title_frame.pack(fill="x", pady=(0, 15))
        
        title_text = "Proizvodi koji su uskoro nestali" if filter_type == "low_stock" else "Proizvodi kojih nema na stanju"
        tk.Label(
            title_frame, 
            text=title_text,
            font=("Segoe UI", 14, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT
        ).pack(side="left")
        
        # Export button
        export_button = ModernButton(
            title_frame,
            text="Exportuj podatke",
            command=self.export_data
        )
        export_button.pack(side="right")
        
        # Create table
        table_frame = tk.Frame(main_frame, bg=COLOR_FRAME_BG)
        table_frame.pack(fill="both", expand=True)
        
        # Define style for Treeview
        style = ttk.Style()
        style.theme_use("default")
        
        # Configure the Treeview colors
        style.configure("Treeview", 
                        background=COLOR_BG,
                        foreground=COLOR_TEXT,
                        rowheight=25,
                        fieldbackground=COLOR_BG)
        
        # Change selected color
        style.map('Treeview', 
                  background=[('selected', COLOR_ACCENT)])
        
        # Create the Treeview widget for the table
        self.tree = ttk.Treeview(table_frame, columns=("id", "naziv", "stanje"), show="headings")
        
        # Define column headings
        self.tree.heading("id", text="ID")
        self.tree.heading("naziv", text="Naziv")
        self.tree.heading("stanje", text="Stanje")
        
        # Define column widths
        self.tree.column("id", width=50)
        self.tree.column("naziv", width=250)
        self.tree.column("stanje", width=100)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the Treeview and scrollbar
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate the table with data
        self.load_data()
        self.lift()
        self.focus_force()
        self.grab_set()
    
    def load_data(self):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            # Connect to the database
            conn = sqlite3.connect("garage.db")
            cursor = conn.cursor()
            
            query = f"""
                    SELECT z.id, z.naziv, 
                    z.stanje 
                    FROM zalihe z 
                    WHERE {self.filter_condition}
                    ORDER BY {self.sort_order}
                """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Insert data into the treeview
            for row in rows:
                self.tree.insert("", "end", values=row)
                
            # Ako nema podataka, dodaj poruku
            if len(rows) == 0:
                self.tree.insert("", "end", values=("", "Nema podataka", ""))
                
            conn.close()
        except sqlite3.Error as e:
            # Dodaj red sa greškom u tabelu da bi korisnik video
            self.tree.insert("", "end", values=("", f"Greška: {e}", ""))
    
    def export_data(self):
        try:
            # Connect to the database
            conn = sqlite3.connect("garage.db")
            cursor = conn.cursor()
            
            # Execute the query
            query = f"""
                SELECT z.id, z.naziv, z.stanje 
                FROM zalihe z 
                WHERE {self.filter_condition}
                ORDER BY {self.sort_order}
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Create directory if it doesn't exist
            export_dir = os.path.join(os.path.expanduser("~"), "Documents", "garaza")
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate filename with current date and time
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"export-{self.export_prefix}-{timestamp}.csv"
            filepath = os.path.join(export_dir, filename)
            
            # Write data to CSV file
            with open(filepath, "w", encoding="utf-8") as file:
                # Write header
                file.write("ID,Naziv,Stanje\n")
                
                # Write data rows
                for row in rows:
                    # Escape commas in text fields
                    escaped_row = [str(cell).replace(",", ";") for cell in row]
                    file.write(",".join(escaped_row) + "\n")
            
            # Show confirmation in a popup
            confirm_window = tk.Toplevel(self)
            confirm_window.title("Export uspešan")
            confirm_window.geometry("400x150")
            confirm_window.configure(bg=COLOR_BG)
            
            confirm_frame = tk.Frame(confirm_window, bg=COLOR_BG, padx=20, pady=20)
            confirm_frame.pack(fill="both", expand=True)
            
            tk.Label(
                confirm_frame,
                text=f"Podaci su uspešno exportovani u:\n{filepath}",
                font=("Segoe UI", 10),
                bg=COLOR_BG,
                fg=COLOR_TEXT,
                wraplength=360,
                justify="center"
            ).pack(pady=10)
            
            close_button = ModernButton(
                confirm_frame,
                text="OK",
                command=confirm_window.destroy
            )
            close_button.pack()
            
            conn.close()
            
        except Exception as e:
            # Show error message
            error_window = tk.Toplevel(self)
            error_window.title("Greška")
            error_window.geometry("400x150")
            error_window.configure(bg=COLOR_BG)
            
            error_frame = tk.Frame(error_window, bg=COLOR_BG, padx=20, pady=20)
            error_frame.pack(fill="both", expand=True)
            
            tk.Label(
                error_frame,
                text=f"Došlo je do greške prilikom exporta:\n{str(e)}",
                font=("Segoe UI", 10),
                bg=COLOR_BG,
                fg="#e74c3c",  # Red color for error
                wraplength=360,
                justify="center"
            ).pack(pady=10)
            
            close_button = ModernButton(
                error_frame,
                text="OK",
                command=error_window.destroy
            )
            close_button.pack()

def check_database():
    """Check if the database exists and create it if it doesn't"""
    try:
        if not os.path.exists("garage.db"):
            # Database doesn't exist, create it
            conn = sqlite3.connect("garage.db")
            cursor = conn.cursor()
            
            # Create kategorije table
            cursor.execute("""
                CREATE TABLE kategorije (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    naziv TEXT NOT NULL UNIQUE
                )
            """)
            
            # Create zalihe table
            cursor.execute("""
                CREATE TABLE zalihe (
                    id INTEGER PRIMARY KEY,
                    naziv TEXT NOT NULL,
                    slika TEXT,
                    kategorija TEXT,
                    stanje INTEGER DEFAULT 0
                )
            """)
            
            conn.commit()
            conn.close()
            print("Database created successfully")
            return True
        return False
    except sqlite3.Error as e:
        print(f"Database creation error: {e}")
        return False

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Moja Garaza")
        
        # Fixed window size - not resizable
        width = 1024
        height = 768
        self.state('zoomed')
        
        self.configure(bg=COLOR_BG)

        # Set ttk style
        self.style = ttk.Style()
        self.style.theme_use('default')
        
        # Configure the Treeview colors
        self.style.configure("Treeview", 
                            background=COLOR_BG,
                            foreground=COLOR_TEXT,
                            rowheight=25,
                            fieldbackground=COLOR_BG)
        
        # Change selected color
        self.style.map('Treeview', 
                      background=[('selected', COLOR_ACCENT)])

        # Check database on startup
        db_created = check_database()
    
        # Gornji meni (top menu)
        menu_frame = tk.Frame(self, bg=COLOR_ACCENT, height=50)
        menu_frame.pack(side="top", fill="x")
        
        # Shadow effect for menu
        shadow_frame = tk.Frame(self, height=3, bg="#e0e0e0")
        shadow_frame.pack(side="top", fill="x")

        # Menu buttons with modern styling - white text on orange background
        btn_pocetna = tk.Button(menu_frame, text="Početna", command=self.prikazi_pocetnu, 
                              bg=COLOR_ACCENT, fg="white", relief=tk.FLAT, 
                              font=("Segoe UI", 10, "bold"), padx=15, pady=10,
                              activebackground=COLOR_SECONDARY, activeforeground="white",
                              cursor="hand2", bd=0)
        btn_vrste = tk.Button(menu_frame, text="Vrste", command=self.prikazi_vrste,
                            bg=COLOR_ACCENT, fg="white", relief=tk.FLAT, 
                            font=("Segoe UI", 10, "bold"), padx=15, pady=10,
                            activebackground=COLOR_SECONDARY, activeforeground="white",
                            cursor="hand2", bd=0)
        btn_kategorije = tk.Button(menu_frame, text="Kategorije", command=self.prikazi_kategorije,
                                 bg=COLOR_ACCENT, fg="white", relief=tk.FLAT, 
                                 font=("Segoe UI", 10, "bold"), padx=15, pady=10,
                                 activebackground=COLOR_SECONDARY, activeforeground="white",
                                 cursor="hand2", bd=0)
        btn_zalihe = tk.Button(menu_frame, text="Zalihe", command=self.prikazi_zalihe,
                             bg=COLOR_ACCENT, fg="white", relief=tk.FLAT, 
                             font=("Segoe UI", 10, "bold"), padx=15, pady=10,
                             activebackground=COLOR_SECONDARY, activeforeground="white",
                             cursor="hand2", bd=0)
        btn_uputstvo = tk.Button(menu_frame, text="Uputstvo", command=self.prikazi_uputstvo,
                               bg=COLOR_ACCENT, fg="white", relief=tk.FLAT, 
                               font=("Segoe UI", 10, "bold"), padx=15, pady=10,
                               activebackground=COLOR_SECONDARY, activeforeground="white",
                               cursor="hand2", bd=0)
        btn_uslovi = tk.Button(menu_frame, text="Uslovi koriscenja", command=self.prikazi_uslove_koriscenja,
                             bg=COLOR_ACCENT, fg="white", relief=tk.FLAT, 
                             font=("Segoe UI", 10, "bold"), padx=15, pady=10,
                             activebackground=COLOR_SECONDARY, activeforeground="white",
                             cursor="hand2", bd=0)

        btn_pocetna.pack(side="left")
        btn_vrste.pack(side="left")
        btn_kategorije.pack(side="left")
        btn_zalihe.pack(side="left")
        btn_uputstvo.pack(side="left")
        btn_uslovi.pack(side="left")

        # Sat u gornjem desnom uglu (clock in top right)
        clock_container = tk.Frame(menu_frame, bg=COLOR_ACCENT)
        clock_container.pack(side="right", padx=15, pady=10)
        
        # Label for "Time:" text
        tk.Label(clock_container, 
                text="Time:", 
                font=("Segoe UI", 12, "bold"), 
                bg=COLOR_ACCENT, 
                fg="white").pack(side="left", padx=(0, 5))
                
        # Modern digital clock with custom styling
        self.clock_label = tk.Label(
            clock_container, 
            font=("Segoe UI", 16, "bold"), 
            fg=COLOR_ACCENT, 
            bg="white",
            padx=10,
            pady=4,
            relief=tk.FLAT
        )
        self.clock_label.pack(side="right")
        self.azuriraj_vreme()

        # Main content container
        self.content_frame = tk.Frame(self, bg=COLOR_BG)
        self.content_frame.pack(expand=True, fill="both", padx=20, pady=15)

        self.trenutni_prikaz = None
        self.prikazi_pocetnu()

        footer = tk.Label(self, text="© 2025 Alokyn | alokyn.com", bg=COLOR_BG, fg="#999999", font=("Segoe UI", 9))
        footer.pack(side='bottom', anchor='e', pady=5, padx=10)

    def azuriraj_vreme(self):
        trenutno = time.strftime("%H:%M:%S")  # Format HH:MM:SS
        self.clock_label.config(text=trenutno)
        self.after(1000, self.azuriraj_vreme)  # Update every 1 second

    def ocisti_prikaz(self):
        if self.trenutni_prikaz:
            self.trenutni_prikaz.destroy()
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def prikazi_pocetnu(self):
        self.ocisti_prikaz()

        # Main container for the dashboard
        main_container = tk.Frame(self.content_frame, bg=COLOR_BG)
        main_container.pack(expand=True, fill="both")
        
        # Dashboard title
        title_frame = tk.Frame(main_container, bg=COLOR_BG)
        title_frame.pack(fill="x", pady=(0, 20))
        
        # Title with orange underline
        title_container = tk.Frame(title_frame, bg=COLOR_BG)
        title_container.pack(anchor="w")
        
        tk.Label(
            title_container, 
            text="Početna stranica", 
            font=("Segoe UI", 18, "bold"), 
            bg=COLOR_BG, 
            fg=COLOR_TEXT
        ).pack(anchor="w")
        
        # Orange underline
        underline = tk.Frame(title_container, height=3, width=200, bg=COLOR_ACCENT)
        underline.pack(anchor="w", pady=(2, 0))
        
        # Create dashboard cards container
        cards_container = tk.Frame(main_container, bg=COLOR_BG)
        cards_container.pack(fill="x", pady=30)
        
        # "Uskoro Nestalo" Card (Low Stock)
        self.frame_uskoro_nestalo = self.create_stat_card(
            cards_container, 
            "Jos malo pa nestalo", 
            "Broj proizvoda koji imamo manje od 10 na stanju",
            "#FF8C00",  # Orange color
            "low_stock"  # Add click_action parameter
        )
        self.frame_uskoro_nestalo.pack(side="left", padx=10, fill="both", expand=True)
        
        # "Nestalo" Card (Out of Stock)
        self.frame_nestalo = self.create_stat_card(
            cards_container, 
            "Nestalo", 
            "Broj proizvoda koji su 0.",
            "#FF8C00",  # Orange color
            "out_of_stock"  # Add click_action parameter
        )
        self.frame_nestalo.pack(side="left", padx=10, fill="both", expand=True)
        
        # Fetch data from the database and update the cards
        self.fetch_product_counts()
        
        # Store reference to current view
        self.trenutni_prikaz = main_container

    def create_instruction_frame(self, parent, title, content, color_accent):
        """Creates an instruction frame for the UPUTSTVO section"""
        frame = tk.Frame(parent, bg=COLOR_FRAME_BG, bd=1, relief=tk.GROOVE)
        
        # Color accent bar at top
        accent_bar = tk.Frame(frame, bg=color_accent, height=5)
        accent_bar.pack(fill="x")
        
        # Content padding
        content_frame = tk.Frame(frame, bg=COLOR_FRAME_BG, padx=15, pady=15)
        content_frame.pack(fill="both", expand=True)
        
        # Title
        tk.Label(
            content_frame, 
            text=title, 
            font=("Segoe UI", 12, "bold"), 
            bg=COLOR_FRAME_BG, 
            fg=COLOR_TEXT
        ).pack(anchor="w")
        
        # Content
        tk.Label(
            content_frame, 
            text=content, 
            font=("Segoe UI", 9), 
            bg=COLOR_FRAME_BG, 
            fg=COLOR_LIGHT_TEXT,
            wraplength=200,  # Limit text width
            justify="left"
        ).pack(anchor="w", pady=(5, 0), fill="both", expand=True)
        
        return frame

    def create_stat_card(self, parent, title, subtitle, color_accent, click_action=None):
        """Creates a styled statistic card for the dashboard"""
        card = tk.Frame(parent, bg="white", bd=0, relief=tk.GROOVE, highlightbackground=color_accent, highlightthickness=1)
        
        # Make cursor change when hovering if card is clickable
        if click_action:
            card.config(cursor="hand2")
        
        # Title bar with accent color
        title_bar = tk.Frame(card, bg=color_accent, height=8)
        title_bar.pack(fill="x")
        
        # Content padding
        content = tk.Frame(card, bg="white", padx=20, pady=20)
        content.pack(fill="both", expand=True)
        
        # Title and subtitle
        title_label = tk.Label(
            content, 
            text=title, 
            font=("Segoe UI", 14, "bold"), 
            bg="white", 
            fg=COLOR_TEXT
        )
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(
            content, 
            text=subtitle, 
            font=("Segoe UI", 9), 
            bg="white", 
            fg=COLOR_LIGHT_TEXT
        )
        subtitle_label.pack(anchor="w", pady=(0, 15))
        
        # Value display with large font and accent color
        value_label = tk.Label(
            content, 
            text="0", 
            font=("Segoe UI", 28, "bold"), 
            bg="white", 
            fg=color_accent
        )
        value_label.pack(anchor="w")
        
        # Add a "View Details" link-style button
        details_frame = tk.Frame(content, bg="white")
        details_frame.pack(anchor="e", pady=(10, 0))
        
        details_label = tk.Label(
            details_frame,
            text="Prikaži detalje",
            font=("Segoe UI", 9, "underline"),
            bg="white",
            fg=color_accent,
            cursor="hand2"
        )
        details_label.pack()
        
        # Store the value label reference for easy updating
        if click_action == "low_stock":
            self.low_stock_label = value_label
        elif click_action == "out_of_stock":
            self.out_of_stock_label = value_label
        
        # Add click functionality if specified
        if click_action:
            # Bind click events to all parts of the card
            card.bind("<Button-1>", lambda e: self.open_filtered_window(click_action))
            content.bind("<Button-1>", lambda e: self.open_filtered_window(click_action))
            title_bar.bind("<Button-1>", lambda e: self.open_filtered_window(click_action))
            title_label.bind("<Button-1>", lambda e: self.open_filtered_window(click_action))
            subtitle_label.bind("<Button-1>", lambda e: self.open_filtered_window(click_action))
            value_label.bind("<Button-1>", lambda e: self.open_filtered_window(click_action))
            details_label.bind("<Button-1>", lambda e: self.open_filtered_window(click_action))
            details_frame.bind("<Button-1>", lambda e: self.open_filtered_window(click_action))
        
        return card

    def open_filtered_window(self, filter_type):
        """Opens a new window with filtered products"""
        FilteredProductsWindow(self, filter_type)

    def fetch_product_counts(self):
        try:
            # Open SQLite database connection
            conn = sqlite3.connect("garage.db")
            cursor = conn.cursor()

            # Count products with stanje between 1 and 10 (Uskoro Nestalo)
            cursor.execute("SELECT COUNT(*) FROM zalihe WHERE stanje BETWEEN 1 AND 10")
            uskoro_count = cursor.fetchone()[0]
            
            # Update the low stock count label
            if hasattr(self, 'low_stock_label'):
                self.low_stock_label.config(text=str(uskoro_count))

            # Count products with stanje equal to 0 (Nestalo)
            cursor.execute("SELECT COUNT(*) FROM zalihe WHERE stanje = 0")
            nestalo_count = cursor.fetchone()[0]
            
            # Update the out of stock count label
            if hasattr(self, 'out_of_stock_label'):
                self.out_of_stock_label.config(text=str(nestalo_count))

            conn.close()  # Close the connection after use

        except sqlite3.Error as e:
            print(f"Error fetching data: {e}")

    def prikazi_vrste(self):
        self.ocisti_prikaz()
        self.trenutni_prikaz = VrsteFrame(self.content_frame)
        self.trenutni_prikaz.pack(expand=True, fill="both")

    def prikazi_kategorije(self):
        """Display the Categories page"""
        self.ocisti_prikaz()
        self.trenutni_prikaz = CategoriesFrame(self.content_frame)
        self.trenutni_prikaz.pack(expand=True, fill="both")

    def prikazi_zalihe(self):
        self.ocisti_prikaz()
        self.trenutni_prikaz = ZaliheFrame(self.content_frame)
        self.trenutni_prikaz.pack(expand=True, fill="both")

    def prikazi_uputstvo(self):
        uputstvo_prozor = tk.Toplevel(self)
        uputstvo_prozor.title("Uputstvo")
        uputstvo_prozor.geometry("500x400")
        uputstvo_prozor.iconbitmap("ico.ico")
        uputstvo_prozor.resizable(False, False)  # Fiksiran prozor
        uputstvo_prozor.configure(bg=COLOR_BG)

        # Naslov sa orange pozadinom
        naslov_frame = tk.Frame(uputstvo_prozor, bg=COLOR_ACCENT, pady=10)
        naslov_frame.pack(fill='x')
        
        naslov = tk.Label(naslov_frame, text="Uputstvo za korišcenje", font=("Segoe UI", 14, "bold"), fg="white", bg=COLOR_ACCENT)
        naslov.pack()

        # Scrollbar + Text polje
        okvir = tk.Frame(uputstvo_prozor, bg=COLOR_BG)
        okvir.pack(fill='both', expand=True, padx=20, pady=20)

        tekst_scroll = tk.Scrollbar(okvir)
        tekst_scroll.pack(side='right', fill='y')

        tekst = tk.Text(okvir, wrap='word', yscrollcommand=tekst_scroll.set, font=("Segoe UI", 10), fg=COLOR_TEXT, bg="white", relief='flat', padx=10, pady=10, border=0)
        tekst.insert("1.0", """
    Dobrodošli u aplikaciju za upravljanje garažom!

    🟠 Sekcija 'Vrste':
    - Prikazuje sve proizvode u bazi.
    - U datoj sekciji mozete dodavati proizvod, svaki dodati proizvod dobija pocetno stanje 0.
    - Desnim klikom na red u tabeli ispod, izlazi meni preko kojeg mozete da izmenite ili obrisete proizvod koji je odabran.

    🟠 Sekcija 'Kategorije':
    - Prikazuje kategorije proizvoda.
    - U ovoj sekciji mozete dodavati kategorije za proizvod.

    🟠 Sekcija 'Zalihe':
    - Prikazuje zalihe proizvoda koje ste dodali u sekciji vrste.
    - Date zalihe mozete filtrirati klikom na kolonu, ID , Naziv, Kategoriju.
    - Desnim klikom na red u tabeli, za dati red se otvara meni gde mozete videti detalje o datom proizvodu ili izmeniti stanje datog proizvoda.
    - Moguce je exportovati tabelu kao CSV format i odstampati ga :) 
    
    Za pomoć kontaktirajte podršku.
    """)
        tekst.config(state='disabled')  # Samo za čitanje
        tekst.pack(fill='both', expand=True)
        tekst_scroll.config(command=tekst.yview)
        uputstvo_prozor.grab_set()


    def prikazi_uslove_koriscenja(self):
        uputstvo_prozor = tk.Toplevel(self)
        uputstvo_prozor.title("Uslovi koriscenja")
        uputstvo_prozor.geometry("500x400")
        uputstvo_prozor.iconbitmap("ico.ico")
        uputstvo_prozor.resizable(False, False)  # Fiksiran prozor
        uputstvo_prozor.configure(bg=COLOR_BG)

        # Pozadinska boja u skladu sa temom
        naslov_frame = tk.Frame(uputstvo_prozor, bg=COLOR_ACCENT, pady=10)
        naslov_frame.pack(fill='x')

        # Naslov
        naslov = tk.Label(naslov_frame, text="Uslovi koriscenja", font=("Segoe UI", 14, "bold"), fg="white", bg=COLOR_ACCENT)
        naslov.pack(pady=10)

        # Scrollbar + Text polje
        okvir = tk.Frame(uputstvo_prozor, bg=COLOR_BG)
        okvir.pack(fill='both', expand=True, padx=20, pady=20)

        tekst_scroll = tk.Scrollbar(okvir)
        tekst_scroll.pack(side='right', fill='y')

        tekst = tk.Text(okvir, wrap='word', yscrollcommand=tekst_scroll.set, font=("Segoe UI", 10), fg=COLOR_TEXT, bg="white", relief='flat', padx=10, pady=10, border=0)
        tekst.insert("1.0", """
    Dobrodošli u aplikaciju za upravljanje garažom!

    📝 Uslovi korišćenja:

    - Aplikacija radi 100% lokalno i ne koristi internet konekciju.
    - Svi podaci se čuvaju na vašem računaru, u lokalnoj SQLite bazi.
    - Korisnik je isključivo odgovoran za unos i čuvanje podataka.
    - U slučaju gubitka podataka, grešaka u radu ili bilo kakvih problema, autor ne snosi odgovornost.
    - Preporučuje se redovno pravljenje rezervnih kopija baze podataka.

    Korišćenjem aplikacije prihvatate navedene uslove.
    """)
        tekst.config(state='disabled')  # Samo za čitanje
        tekst.pack(fill='both', expand=True)
        tekst_scroll.config(command=tekst.yview)
        uputstvo_prozor.grab_set()

if __name__ == "__main__":
    app = App()
    app.iconbitmap("ico.ico")
    app.mainloop()