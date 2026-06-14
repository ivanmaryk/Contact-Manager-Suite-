// contacts.rs - Менеджер контактов на Rust (CLI с диалогами и JSON)
use serde::{Serialize, Deserialize};
use std::fs;
use std::io::{self, Write};
use std::collections::HashMap;
use chrono::Local;

#[derive(Serialize, Deserialize, Clone)]
struct Contact {
    id: u64,
    first_name: String,
    last_name: String,
    phone: String,
    email: String,
    address: String,
    group: String,
    notes: String,
    photo_url: String,
    created: String,
}

impl Contact {
    fn full_name(&self) -> String {
        format!("{} {}", self.first_name, self.last_name).trim().to_string()
    }
}

const DATA_FILE: &str = "contacts.json";

fn load_contacts() -> Vec<Contact> {
    if let Ok(data) = fs::read_to_string(DATA_FILE) {
        serde_json::from_str(&data).unwrap_or_else(|_| vec![])
    } else {
        vec![]
    }
}

fn save_contacts(contacts: &Vec<Contact>) {
    let data = serde_json::to_string_pretty(contacts).unwrap();
    fs::write(DATA_FILE, data).unwrap();
}

fn next_id(contacts: &Vec<Contact>) -> u64 {
    contacts.iter().map(|c| c.id).max().unwrap_or(0) + 1
}

fn read_line(prompt: &str) -> String {
    print!("{}", prompt);
    io::stdout().flush().unwrap();
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    input.trim().to_string()
}

fn add_contact(contacts: &mut Vec<Contact>) {
    println!("\n--- Новый контакт ---");
    let first_name = read_line("Имя: ");
    if first_name.is_empty() {
        println!("Имя обязательно");
        return;
    }
    let last_name = read_line("Фамилия: ");
    let phone = read_line("Телефон: ");
    let email = read_line("Email: ");
    let address = read_line("Адрес: ");
    let group = read_line("Группа (Family/Work/Friends/Other): ");
    let notes = read_line("Заметки: ");
    let photo_url = read_line("Фото URL: ");
    let id = next_id(contacts);
    let created = Local::now().to_rfc3339();
    contacts.push(Contact {
        id,
        first_name,
        last_name,
        phone,
        email,
        address,
        group,
        notes,
        photo_url,
        created,
    });
    save_contacts(contacts);
    println!("✅ Контакт добавлен (ID: {})", id);
}

fn list_contacts(contacts: &Vec<Contact>, filter_group: Option<&str>, search: Option<&str>) {
    let mut filtered = contacts.clone();
    if let Some(g) = filter_group {
        if g != "all" {
            filtered.retain(|c| c.group == g);
        }
    }
    if let Some(s) = search {
        let s_lower = s.to_lowercase();
        filtered.retain(|c| {
            c.full_name().to_lowercase().contains(&s_lower) ||
            c.phone.contains(&s_lower) ||
            c.email.to_lowercase().contains(&s_lower)
        });
    }
    if filtered.is_empty() {
        println!("Нет контактов.");
        return;
    }
    println!("\n{:-<60}", "");
    for c in filtered {
        println!("ID: {} | {} | {} | {}", c.id, c.full_name(), c.phone, c.email);
    }
    println!("{:-<60}", "");
}

fn view_contact(contacts: &Vec<Contact>, id: u64) {
    if let Some(c) = contacts.iter().find(|c| c.id == id) {
        println!("\n--- Контакт ID: {} ---", c.id);
        println!("Имя: {} {}", c.first_name, c.last_name);
        println!("Телефон: {}", c.phone);
        println!("Email: {}", c.email);
        println!("Адрес: {}", c.address);
        println!("Группа: {}", c.group);
        println!("Заметки: {}", c.notes);
        println!("Фото: {}", c.photo_url);
        println!("Создан: {}", c.created);
    } else {
        println!("Контакт не найден");
    }
}

fn edit_contact(contacts: &mut Vec<Contact>, id: u64) {
    let idx = contacts.iter().position(|c| c.id == id);
    if let Some(idx) = idx {
        let mut c = contacts[idx].clone();
        println!("Редактирование контакта (оставьте пустым для сохранения старого значения)");
        let new_first = read_line(&format!("Имя ({}): ", c.first_name));
        if !new_first.is_empty() { c.first_name = new_first; }
        let new_last = read_line(&format!("Фамилия ({}): ", c.last_name));
        if !new_last.is_empty() { c.last_name = new_last; }
        let new_phone = read_line(&format!("Телефон ({}): ", c.phone));
        if !new_phone.is_empty() { c.phone = new_phone; }
        let new_email = read_line(&format!("Email ({}): ", c.email));
        if !new_email.is_empty() { c.email = new_email; }
        let new_addr = read_line(&format!("Адрес ({}): ", c.address));
        if !new_addr.is_empty() { c.address = new_addr; }
        let new_group = read_line(&format!("Группа ({}): ", c.group));
        if !new_group.is_empty() { c.group = new_group; }
        let new_notes = read_line(&format!("Заметки ({}): ", c.notes));
        if !new_notes.is_empty() { c.notes = new_notes; }
        let new_photo = read_line(&format!("Фото URL ({}): ", c.photo_url));
        if !new_photo.is_empty() { c.photo_url = new_photo; }
        contacts[idx] = c;
        save_contacts(contacts);
        println!("Контакт обновлён");
    } else {
        println!("Контакт не найден");
    }
}

fn delete_contact(contacts: &mut Vec<Contact>, id: u64) {
    let len = contacts.len();
    contacts.retain(|c| c.id != id);
    if contacts.len() < len {
        save_contacts(contacts);
        println!("Контакт удалён");
    } else {
        println!("Контакт не найден");
    }
}

fn main() {
    let mut contacts = load_contacts();
    loop {
        println!("\n=== Менеджер контактов Rust ===");
        println!("1. Добавить контакт");
        println!("2. Список всех");
        println!("3. Поиск/фильтр");
        println!("4. Просмотреть контакт");
        println!("5. Редактировать");
        println!("6. Удалить");
        println!("7. Экспорт в CSV (не реализован)");
        println!("0. Выход");
        let choice = read_line("Выбор: ");
        match choice.as_str() {
            "1" => add_contact(&mut contacts),
            "2" => list_contacts(&contacts, None, None),
            "3" => {
                let group = read_line("Фильтр по группе (all/Family/Work/Friends/Other): ");
                let search = read_line("Поиск (название/телефон/email): ");
                list_contacts(&contacts, Some(&group), if search.is_empty() { None } else { Some(&search) });
            }
            "4" => {
                let id_str = read_line("ID контакта: ");
                if let Ok(id) = id_str.parse() {
                    view_contact(&contacts, id);
                } else { println!("Неверный ID"); }
            }
            "5" => {
                let id_str = read_line("ID контакта для редактирования: ");
                if let Ok(id) = id_str.parse() {
                    edit_contact(&mut contacts, id);
                } else { println!("Неверный ID"); }
            }
            "6" => {
                let id_str = read_line("ID контакта для удаления: ");
                if let Ok(id) = id_str.parse() {
                    delete_contact(&mut contacts, id);
                } else { println!("Неверный ID"); }
            }
            "0" => break,
            _ => println!("Неизвестная команда"),
        }
    }
}
