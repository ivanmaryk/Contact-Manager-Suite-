// contacts.cs - Менеджер контактов на C# Windows Forms
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows.Forms;

namespace ContactManager
{
    public class Contact
    {
        public int Id { get; set; }
        public string FirstName { get; set; }
        public string LastName { get; set; }
        public string Phone { get; set; }
        public string Email { get; set; }
        public string Address { get; set; }
        public string Group { get; set; }
        public string Notes { get; set; }
        public string PhotoUrl { get; set; }
        public string Created { get; set; }
        public string FullName => $"{FirstName} {LastName}".Trim();
    }

    public class MainForm : Form
    {
        private List<Contact> contacts = new List<Contact>();
        private int nextId = 1;
        private string dataFile = "contacts.json";
        private DataGridView dgv;
        private TextBox searchBox;
        private ComboBox groupFilter;
        private Panel detailsPanel;

        public MainForm()
        {
            Text = "Менеджер контактов C#";
            Size = new Size(1000, 600);
            LoadContacts();
            InitializeUI();
        }

        private void LoadContacts()
        {
            if (File.Exists(dataFile))
            {
                string json = File.ReadAllText(dataFile);
                contacts = JsonSerializer.Deserialize<List<Contact>>(json) ?? new List<Contact>();
                nextId = contacts.Count > 0 ? contacts.Max(c => c.Id) + 1 : 1;
            }
        }

        private void SaveContacts()
        {
            string json = JsonSerializer.Serialize(contacts, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(dataFile, json);
        }

        private void InitializeUI()
        {
            // Верхняя панель
            var topPanel = new FlowLayoutPanel { Dock = DockStyle.Top, Padding = new Padding(5), Height = 45 };
            topPanel.Controls.Add(new Label { Text = "Поиск:", AutoSize = true });
            searchBox = new TextBox { Width = 200 };
            searchBox.TextChanged += (s, e) => RefreshGrid();
            topPanel.Controls.Add(searchBox);
            topPanel.Controls.Add(new Label { Text = "Группа:" });
            groupFilter = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 120 };
            groupFilter.Items.AddRange(new[] { "All", "Family", "Work", "Friends", "Other" });
            groupFilter.SelectedIndex = 0;
            groupFilter.SelectedIndexChanged += (s, e) => RefreshGrid();
            topPanel.Controls.Add(groupFilter);
            var addBtn = new Button { Text = "Добавить", BackColor = Color.DodgerBlue, ForeColor = Color.White };
            addBtn.Click += (s, e) => AddEditContact(null);
            topPanel.Controls.Add(addBtn);
            Controls.Add(topPanel);

            // DataGridView
            dgv = new DataGridView { Dock = DockStyle.Fill, AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill, SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = false };
            dgv.SelectionChanged += (s, e) => ShowDetails();
            Controls.Add(dgv);

            // Панель деталей справа
            detailsPanel = new Panel { Dock = DockStyle.Right, Width = 300, BorderStyle = BorderStyle.FixedSingle };
            Controls.Add(detailsPanel);

            RefreshGrid();
        }

        private void RefreshGrid()
        {
            var filtered = contacts.AsEnumerable();
            string search = searchBox.Text.ToLower();
            string group = groupFilter.SelectedItem?.ToString();
            if (group != "All") filtered = filtered.Where(c => c.Group == group);
            if (!string.IsNullOrEmpty(search))
                filtered = filtered.Where(c => c.FullName.ToLower().Contains(search) || c.Phone.Contains(search) || c.Email.ToLower().Contains(search));
            dgv.DataSource = null;
            dgv.DataSource = filtered.Select(c => new { c.Id, c.FirstName, c.LastName, c.Phone, c.Email, c.Group }).ToList();
        }

        private void ShowDetails()
        {
            if (dgv.SelectedRows.Count == 0) return;
            int id = (int)dgv.SelectedRows[0].Cells[0].Value;
            Contact c = contacts.FirstOrDefault(cn => cn.Id == id);
            if (c == null) return;
            detailsPanel.Controls.Clear();
            var lbl = new Label { Text = $"Детали контакта", Font = new Font("Arial", 12, FontStyle.Bold), Dock = DockStyle.Top, TextAlign = ContentAlignment.MiddleCenter, Height = 30 };
            detailsPanel.Controls.Add(lbl);
            var props = new Dictionary<string, string> {
                {"Имя:", c.FullName}, {"Телефон:", c.Phone}, {"Email:", c.Email}, {"Адрес:", c.Address},
                {"Группа:", c.Group}, {"Заметки:", c.Notes}, {"Фото URL:", c.PhotoUrl}
            };
            int y = 40;
            foreach (var kv in props)
            {
                var label = new Label { Text = kv.Key, Location = new Point(10, y), AutoSize = true };
                var value = new Label { Text = kv.Value ?? "—", Location = new Point(90, y), AutoSize = true, Width = 180 };
                detailsPanel.Controls.Add(label);
                detailsPanel.Controls.Add(value);
                y += 25;
            }
            var editBtn = new Button { Text = "Редактировать", Location = new Point(10, y+10), Width = 120 };
            editBtn.Click += (s, e) => AddEditContact(c);
            var delBtn = new Button { Text = "Удалить", Location = new Point(140, y+10), Width = 120, BackColor = Color.Crimson, ForeColor = Color.White };
            delBtn.Click += (s, e) => {
                if (MessageBox.Show("Удалить контакт?", "Подтверждение", MessageBoxButtons.YesNo) == DialogResult.Yes)
                {
                    contacts.Remove(c);
                    SaveContacts();
                    RefreshGrid();
                    detailsPanel.Controls.Clear();
                }
            };
            detailsPanel.Controls.Add(editBtn);
            detailsPanel.Controls.Add(delBtn);
        }

        private void AddEditContact(Contact existing)
        {
            var form = new Form { Text = existing == null ? "Новый контакт" : "Редактировать", Size = new Size(400, 500), StartPosition = FormStartPosition.CenterParent };
            var table = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 9, Padding = new Padding(10) };
            table.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 100));
            var firstName = new TextBox(); var lastName = new TextBox(); var phone = new TextBox(); var email = new TextBox();
            var address = new TextBox(); var group = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Items = { "Family", "Work", "Friends", "Other" } };
            var notes = new TextBox { Multiline = true, Height = 60 }; var photoUrl = new TextBox();
            if (existing != null)
            {
                firstName.Text = existing.FirstName; lastName.Text = existing.LastName; phone.Text = existing.Phone;
                email.Text = existing.Email; address.Text = existing.Address; group.SelectedItem = existing.Group;
                notes.Text = existing.Notes; photoUrl.Text = existing.PhotoUrl;
            }
            else group.SelectedIndex = 0;
            AddRow(table, "Имя *:", firstName); AddRow(table, "Фамилия:", lastName); AddRow(table, "Телефон:", phone);
            AddRow(table, "Email:", email); AddRow(table, "Адрес:", address); AddRow(table, "Группа:", group);
            AddRow(table, "Заметки:", notes); AddRow(table, "Фото URL:", photoUrl);
            var saveBtn = new Button { Text = "Сохранить", Dock = DockStyle.Bottom, Height = 40 };
            saveBtn.Click += (s, e) => {
                if (string.IsNullOrWhiteSpace(firstName.Text)) { MessageBox.Show("Имя обязательно"); return; }
                if (existing == null)
                {
                    var newContact = new Contact
                    {
                        Id = nextId++,
                        FirstName = firstName.Text.Trim(),
                        LastName = lastName.Text.Trim(),
                        Phone = phone.Text.Trim(),
                        Email = email.Text.Trim(),
                        Address = address.Text.Trim(),
                        Group = group.SelectedItem.ToString(),
                        Notes = notes.Text.Trim(),
                        PhotoUrl = photoUrl.Text.Trim(),
                        Created = DateTime.Now.ToString("o")
                    };
                    contacts.Add(newContact);
                }
                else
                {
                    existing.FirstName = firstName.Text.Trim();
                    existing.LastName = lastName.Text.Trim();
                    existing.Phone = phone.Text.Trim();
                    existing.Email = email.Text.Trim();
                    existing.Address = address.Text.Trim();
                    existing.Group = group.SelectedItem.ToString();
                    existing.Notes = notes.Text.Trim();
                    existing.PhotoUrl = photoUrl.Text.Trim();
                }
                SaveContacts();
                RefreshGrid();
                form.Close();
            };
            table.Controls.Add(saveBtn, 0, 8);
            table.SetColumnSpan(saveBtn, 2);
            form.Controls.Add(table);
            form.ShowDialog();
        }

        private void AddRow(TableLayoutPanel table, string label, Control control)
        {
            int row = table.RowCount-1;
            table.RowCount++;
            table.Controls.Add(new Label { Text = label, AutoSize = true, Anchor = AnchorStyles.Right }, 0, row);
            table.Controls.Add(control, 1, row);
        }

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.Run(new MainForm());
        }
    }
}
