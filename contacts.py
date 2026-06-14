"""
contacts.py - Менеджер контактов на Python (Tkinter + JSON + vCard)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import re
from datetime import datetime
from PIL import Image, ImageTk
import io
import base64

try:
    import vobject
    VOBJECT_AVAILABLE = True
except ImportError:
    VOBJECT_AVAILABLE = False
    print("Для экспорта vCard установите: pip install vobject")

DATA_FILE = "contacts.json"

class Contact:
    def __init__(self, id=None, first_name="", last_name="", phone="", email="", address="", group="", notes="", photo_b64="", created=None):
        self.id = id or int(datetime.now().timestamp() * 1000)
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.email = email
        self.address = address
        self.group = group  # Family, Work, Friends, Other
        self.notes = notes
        self.photo_b64 = photo_b64
        self.created = created or datetime.now().isoformat()

    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "group": self.group,
            "notes": self.notes,
            "photo_b64": self.photo_b64,
            "created": self.created
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

class ContactManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📇 Менеджер контактов")
        self.root.geometry("1000x650")
        self.root.configure(bg="#f0f0f0")
        
        self.contacts = []
        self.current_filter = "All"
        self.load_data()
        
        self.create_widgets()
        self.refresh_list()
        
    def create_widgets(self):
        # Верхняя панель: поиск и фильтр
        top_frame = tk.Frame(self.root, bg="#2c3e50", height=70)
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text="📇 Контакты", font=('Arial', 18, 'bold'), fg="white", bg="#2c3e50").pack(side=tk.LEFT, padx=20)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *a: self.refresh_list())
        search_entry = tk.Entry(top_frame, textvariable=self.search_var, width=30, font=('Arial', 12))
        search_entry.pack(side=tk.LEFT, padx=20)
        tk.Button(top_frame, text="🔍 Поиск", command=self.refresh_list, bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Фильтр по группам
        self.filter_var = tk.StringVar(value="All")
        groups = ["All", "Family", "Work", "Friends", "Other"]
        filter_menu = ttk.Combobox(top_frame, textvariable=self.filter_var, values=groups, width=10, state="readonly")
        filter_menu.pack(side=tk.LEFT, padx=20)
        filter_menu.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())
        
        # Кнопки действий
        btn_frame = tk.Frame(top_frame, bg="#2c3e50")
        btn_frame.pack(side=tk.RIGHT, padx=10)
        for text, cmd in [("➕ Добавить", self.add_contact), ("✏️ Редактировать", self.edit_contact), 
                          ("🗑 Удалить", self.delete_contact), ("📤 Экспорт vCard", self.export_vcard), 
                          ("📥 Импорт vCard", self.import_vcard)]:
            tk.Button(btn_frame, text=text, command=cmd, bg="#ecf0f1", fg="#2c3e50", font=('Arial', 10)).pack(side=tk.LEFT, padx=3)
        
        # Основная область: список контактов и детали
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель: список контактов
        left_frame = tk.Frame(main_pane)
        main_pane.add(left_frame, width=350)
        self.tree = ttk.Treeview(left_frame, columns=("name", "phone", "email"), show="headings", height=20)
        self.tree.heading("name", text="Имя")
        self.tree.heading("phone", text="Телефон")
        self.tree.heading("email", text="Email")
        self.tree.column("name", width=120)
        self.tree.column("phone", width=100)
        self.tree.column("email", width=120)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_contact_selected)
        
        # Правая панель: детали контакта
        right_frame = tk.Frame(main_pane, bg="white")
        main_pane.add(right_frame, width=450)
        
        self.photo_label = tk.Label(right_frame, text="Нет фото", bg="white", width=20, height=10, relief=tk.RIDGE)
        self.photo_label.pack(pady=10)
        
        details_frame = tk.Frame(right_frame, bg="white")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        fields = [
            ("Имя:", "first_name"), ("Фамилия:", "last_name"), ("Телефон:", "phone"),
            ("Email:", "email"), ("Адрес:", "address"), ("Группа:", "group"),
            ("Заметки:", "notes")
        ]
        self.detail_vars = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(details_frame, text=label, font=('Arial', 10, 'bold'), bg="white").grid(row=i, column=0, sticky="w", pady=5)
            var = tk.StringVar()
            entry = tk.Entry(details_frame, textvariable=var, width=40, state='readonly')
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            self.detail_vars[key] = var
        
        self.selected_contact_id = None
    
    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.contacts = [Contact.from_dict(c) for c in data]
        else:
            # Пример контактов
            self.contacts = [
                Contact(1, "Иван", "Иванов", "+7(999)123-45-67", "ivan@example.com", "Москва", "Work", "Коллега"),
                Contact(2, "Мария", "Петрова", "+7(888)765-43-21", "maria@example.com", "СПб", "Friends", "Старый друг")
            ]
            self.save_data()
    
    def save_data(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([c.to_dict() for c in self.contacts], f, indent=2, ensure_ascii=False)
    
    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        search_term = self.search_var.get().lower()
        filter_group = self.filter_var.get()
        filtered = self.contacts
        if filter_group != "All":
            filtered = [c for c in filtered if c.group == filter_group]
        if search_term:
            filtered = [c for c in filtered if search_term in c.full_name().lower() or search_term in c.phone or search_term in c.email]
        for contact in filtered:
            self.tree.insert("", tk.END, iid=contact.id, values=(contact.full_name(), contact.phone, contact.email))
    
    def on_contact_selected(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        contact_id = int(selected[0])
        contact = next((c for c in self.contacts if c.id == contact_id), None)
        if contact:
            self.selected_contact_id = contact.id
            self.detail_vars["first_name"].set(contact.first_name)
            self.detail_vars["last_name"].set(contact.last_name)
            self.detail_vars["phone"].set(contact.phone)
            self.detail_vars["email"].set(contact.email)
            self.detail_vars["address"].set(contact.address)
            self.detail_vars["group"].set(contact.group)
            self.detail_vars["notes"].set(contact.notes)
            # Отобразить фото, если есть
            if contact.photo_b64:
                try:
                    img_data = base64.b64decode(contact.photo_b64)
                    img = Image.open(io.BytesIO(img_data))
                    img = img.resize((100, 100), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.photo_label.config(image=photo, text="")
                    self.photo_label.image = photo
                except:
                    self.photo_label.config(image="", text="Ошибка фото")
            else:
                self.photo_label.config(image="", text="Нет фото")
    
    def add_contact(self):
        self.open_contact_dialog()
    
    def edit_contact(self):
        if not self.selected_contact_id:
            messagebox.showwarning("Предупреждение", "Выберите контакт")
            return
        contact = next((c for c in self.contacts if c.id == self.selected_contact_id), None)
        if contact:
            self.open_contact_dialog(contact)
    
    def delete_contact(self):
        if not self.selected_contact_id:
            messagebox.showwarning("Предупреждение", "Выберите контакт")
            return
        if messagebox.askyesno("Удаление", "Удалить контакт?"):
            self.contacts = [c for c in self.contacts if c.id != self.selected_contact_id]
            self.save_data()
            self.refresh_list()
            self.selected_contact_id = None
            for var in self.detail_vars.values():
                var.set("")
            self.photo_label.config(image="", text="Нет фото")
    
    def open_contact_dialog(self, contact=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование контакта" if contact else "Новый контакт")
        dialog.geometry("500x600")
        dialog.grab_set()
        
        fields = {}
        labels = [("Имя", "first_name"), ("Фамилия", "last_name"), ("Телефон", "phone"),
                  ("Email", "email"), ("Адрес", "address"), ("Группа", "group"),
                  ("Заметки (многострочные)", "notes")]
        row = 0
        for label, key in labels:
            tk.Label(dialog, text=label).grid(row=row, column=0, padx=5, pady=5, sticky="e")
            if key == "notes":
                entry = tk.Text(dialog, height=4, width=40)
                entry.grid(row=row, column=1, padx=5, pady=5)
                fields[key] = entry
            else:
                var = tk.StringVar()
                entry = tk.Entry(dialog, textvariable=var, width=40)
                entry.grid(row=row, column=1, padx=5, pady=5)
                fields[key] = var
            row += 1
        
        # Фото
        tk.Label(dialog, text="Фото (путь к файлу)").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        photo_path_var = tk.StringVar()
        photo_entry = tk.Entry(dialog, textvariable=photo_path_var, width=40)
        photo_entry.grid(row=row, column=1, padx=5, pady=5)
        def browse_photo():
            path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")])
            if path:
                photo_path_var.set(path)
        tk.Button(dialog, text="Обзор", command=browse_photo).grid(row=row, column=2, padx=5)
        row += 1
        
        if contact:
            fields["first_name"].set(contact.first_name)
            fields["last_name"].set(contact.last_name)
            fields["phone"].set(contact.phone)
            fields["email"].set(contact.email)
            fields["address"].set(contact.address)
            fields["group"].set(contact.group)
            if isinstance(fields["notes"], tk.Text):
                fields["notes"].insert(tk.END, contact.notes)
            else:
                fields["notes"].set(contact.notes)
        
        def save():
            data = {}
            data["first_name"] = fields["first_name"].get().strip()
            data["last_name"] = fields["last_name"].get().strip()
            data["phone"] = fields["phone"].get().strip()
            data["email"] = fields["email"].get().strip()
            data["address"] = fields["address"].get().strip()
            data["group"] = fields["group"].get().strip()
            if isinstance(fields["notes"], tk.Text):
                data["notes"] = fields["notes"].get("1.0", tk.END).strip()
            else:
                data["notes"] = fields["notes"].get().strip()
            
            # Валидация
            if not data["first_name"]:
                messagebox.showerror("Ошибка", "Имя обязательно")
                return
            if data["email"] and not re.match(r"[^@]+@[^@]+\.[^@]+", data["email"]):
                messagebox.showerror("Ошибка", "Неверный email")
                return
            
            photo_b64 = ""
            if photo_path_var.get():
                try:
                    with open(photo_path_var.get(), "rb") as f:
                        photo_b64 = base64.b64encode(f.read()).decode('utf-8')
                except:
                    pass
            
            if contact:
                contact.first_name = data["first_name"]
                contact.last_name = data["last_name"]
                contact.phone = data["phone"]
                contact.email = data["email"]
                contact.address = data["address"]
                contact.group = data["group"]
                contact.notes = data["notes"]
                if photo_b64:
                    contact.photo_b64 = photo_b64
            else:
                new_id = max([c.id for c in self.contacts], default=0) + 1
                new_contact = Contact(id=new_id, **data, photo_b64=photo_b64)
                self.contacts.append(new_contact)
            self.save_data()
            self.refresh_list()
            dialog.destroy()
        
        tk.Button(dialog, text="Сохранить", command=save, bg="#2ecc71", fg="white").grid(row=row, column=1, pady=20)
    
    def export_vcard(self):
        if not self.selected_contact_id:
            messagebox.showwarning("Выберите контакт")
            return
        contact = next((c for c in self.contacts if c.id == self.selected_contact_id), None)
        if not contact or not VOBJECT_AVAILABLE:
            messagebox.showerror("Ошибка", "vobject не установлен или контакт не выбран")
            return
        vcard = vobject.vCard()
        vcard.add('n').value = vobject.vcard.Name(family=contact.last_name, given=contact.first_name)
        vcard.add('fn').value = contact.full_name()
        if contact.phone:
            tel = vcard.add('tel')
            tel.value = contact.phone
            tel.type_param = 'CELL'
        if contact.email:
            email = vcard.add('email')
            email.value = contact.email
        if contact.address:
            adr = vcard.add('adr')
            adr.value = vobject.vcard.Address(street=contact.address)
        file_path = filedialog.asksaveasfilename(defaultextension=".vcf", filetypes=[("vCard", "*.vcf")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(vcard.serialize())
            messagebox.showinfo("Успех", "Экспортировано")
    
    def import_vcard(self):
        if not VOBJECT_AVAILABLE:
            messagebox.showerror("Ошибка", "Установите vobject")
            return
        file_path = filedialog.askopenfilename(filetypes=[("vCard", "*.vcf")])
        if not file_path:
            return
        with open(file_path, 'r', encoding='utf-8') as f:
            vcard_str = f.read()
        try:
            vcard = vobject.readOne(vcard_str)
            first_name = ""
            last_name = ""
            if hasattr(vcard, 'n') and vcard.n.value:
                last_name = vcard.n.value.family or ""
                first_name = vcard.n.value.given or ""
            fn = vcard.fn.value if hasattr(vcard, 'fn') else f"{first_name} {last_name}".strip()
            if not first_name:
                first_name = fn
            phone = vcard.tel.value if hasattr(vcard, 'tel') else ""
            email = vcard.email.value if hasattr(vcard, 'email') else ""
            address = ""
            if hasattr(vcard, 'adr') and vcard.adr.value:
                address = vcard.adr.value.street or ""
            new_id = max([c.id for c in self.contacts], default=0) + 1
            new_contact = Contact(id=new_id, first_name=first_name, last_name=last_name, phone=phone, email=email, address=address)
            self.contacts.append(new_contact)
            self.save_data()
            self.refresh_list()
            messagebox.showinfo("Успех", "Контакт импортирован")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ContactManagerApp(root)
    root.mainloop()
