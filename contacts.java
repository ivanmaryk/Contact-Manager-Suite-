// contacts.java - Менеджер контактов на Java Swing
import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.awt.event.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.List;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;

class Contact {
    public int id;
    public String firstName;
    public String lastName;
    public String phone;
    public String email;
    public String address;
    public String group;
    public String notes;
    public String photoUrl;
    public String created;

    public Contact() {}
    public Contact(int id, String firstName, String lastName, String phone, String email, String address, String group, String notes, String photoUrl, String created) {
        this.id = id; this.firstName = firstName; this.lastName = lastName; this.phone = phone; this.email = email;
        this.address = address; this.group = group; this.notes = notes; this.photoUrl = photoUrl; this.created = created;
    }
    public String fullName() { return (firstName + " " + lastName).trim(); }
}

public class ContactManager extends JFrame {
    private List<Contact> contacts = new ArrayList<>();
    private int nextId = 1;
    private final String DATA_FILE = "contacts.json";
    private ObjectMapper mapper = new ObjectMapper();
    private JTable contactTable;
    private DefaultTableModel tableModel;
    private JTextField searchField;
    private JComboBox<String> groupFilter;

    public ContactManager() {
        loadContacts();
        initUI();
    }

    private void loadContacts() {
        File f = new File(DATA_FILE);
        if (f.exists()) {
            try {
                String content = new String(Files.readAllBytes(Paths.get(DATA_FILE)));
                contacts = mapper.readValue(content, new TypeReference<List<Contact>>(){});
                nextId = contacts.stream().mapToInt(c -> c.id).max().orElse(0) + 1;
            } catch (Exception e) { e.printStackTrace(); }
        } else {
            contacts = new ArrayList<>();
            nextId = 1;
        }
    }

    private void saveContacts() {
        try {
            mapper.writeValue(new File(DATA_FILE), contacts);
        } catch (Exception e) { e.printStackTrace(); }
    }

    private void initUI() {
        setTitle("Менеджер контактов Java");
        setSize(900, 600);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout());

        // Верхняя панель
        JPanel topPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        topPanel.add(new JLabel("Поиск:"));
        searchField = new JTextField(15);
        searchField.addKeyListener(new KeyAdapter() {
            public void keyReleased(KeyEvent e) { refreshTable(); }
        });
        topPanel.add(searchField);
        topPanel.add(new JLabel("Группа:"));
        groupFilter = new JComboBox<>(new String[]{"All", "Family", "Work", "Friends", "Other"});
        groupFilter.addActionListener(e -> refreshTable());
        topPanel.add(groupFilter);
        JButton addBtn = new JButton("Добавить");
        addBtn.addActionListener(e -> addEditContact(null));
        topPanel.add(addBtn);
        add(topPanel, BorderLayout.NORTH);

        // Таблица
        tableModel = new DefaultTableModel(new String[]{"ID", "Имя", "Телефон", "Email", "Группа"}, 0);
        contactTable = new JTable(tableModel);
        contactTable.getSelectionModel().addListSelectionListener(e -> {
            if (!e.getValueIsAdjusting()) {
                int row = contactTable.getSelectedRow();
                if (row != -1) {
                    int id = (int) tableModel.getValueAt(row, 0);
                    showContactDetails(id);
                }
            }
        });
        add(new JScrollPane(contactTable), BorderLayout.CENTER);

        // Панель деталей справа
        JPanel detailsPanel = new JPanel(new GridBagLayout());
        detailsPanel.setPreferredSize(new Dimension(300, 0));
        detailsPanel.setBorder(BorderFactory.createTitledBorder("Детали"));
        add(detailsPanel, BorderLayout.EAST);

        refreshTable();
    }

    private void refreshTable() {
        tableModel.setRowCount(0);
        String search = searchField.getText().toLowerCase();
        String group = (String) groupFilter.getSelectedItem();
        for (Contact c : contacts) {
            if (!group.equals("All") && !c.group.equals(group)) continue;
            if (!search.isEmpty() && !c.fullName().toLowerCase().contains(search) && !c.phone.contains(search) && !c.email.toLowerCase().contains(search)) continue;
            tableModel.addRow(new Object[]{c.id, c.fullName(), c.phone, c.email, c.group});
        }
    }

    private void showContactDetails(int id) {
        Contact c = contacts.stream().filter(ct -> ct.id == id).findFirst().orElse(null);
        if (c == null) return;
        JPanel details = (JPanel) getContentPane().getComponent(2);
        details.removeAll();
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.gridx = 0; gbc.gridy = 0; gbc.anchor = GridBagConstraints.WEST;
        details.add(new JLabel("Имя:"), gbc);
        gbc.gridx = 1; details.add(new JLabel(c.fullName()), gbc);
        gbc.gridx = 0; gbc.gridy = 1; details.add(new JLabel("Телефон:"), gbc);
        gbc.gridx = 1; details.add(new JLabel(c.phone), gbc);
        gbc.gridx = 0; gbc.gridy = 2; details.add(new JLabel("Email:"), gbc);
        gbc.gridx = 1; details.add(new JLabel(c.email), gbc);
        gbc.gridx = 0; gbc.gridy = 3; details.add(new JLabel("Адрес:"), gbc);
        gbc.gridx = 1; details.add(new JLabel(c.address), gbc);
        gbc.gridx = 0; gbc.gridy = 4; details.add(new JLabel("Группа:"), gbc);
        gbc.gridx = 1; details.add(new JLabel(c.group), gbc);
        gbc.gridx = 0; gbc.gridy = 5; details.add(new JLabel("Заметки:"), gbc);
        gbc.gridx = 1; details.add(new JLabel(c.notes), gbc);
        gbc.gridy = 6; gbc.gridx = 0;
        JButton editBtn = new JButton("Редактировать");
        editBtn.addActionListener(e -> addEditContact(c));
        details.add(editBtn, gbc);
        gbc.gridx = 1;
        JButton delBtn = new JButton("Удалить");
        delBtn.addActionListener(e -> {
            if (JOptionPane.showConfirmDialog(this, "Удалить?") == JOptionPane.YES_OPTION) {
                contacts.removeIf(ct -> ct.id == id);
                saveContacts();
                refreshTable();
                details.removeAll();
                details.revalidate();
                details.repaint();
            }
        });
        details.add(delBtn, gbc);
        details.revalidate();
        details.repaint();
    }

    private void addEditContact(Contact existing) {
        JDialog dialog = new JDialog(this, existing == null ? "Новый контакт" : "Редактировать", true);
        dialog.setSize(400, 500);
        dialog.setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5,5,5,5);
        gbc.gridx = 0; gbc.gridy = 0; gbc.anchor = GridBagConstraints.EAST;
        JTextField firstName = new JTextField(15);
        JTextField lastName = new JTextField(15);
        JTextField phone = new JTextField(15);
        JTextField email = new JTextField(15);
        JTextField address = new JTextField(15);
        JComboBox<String> group = new JComboBox<>(new String[]{"Family","Work","Friends","Other"});
        JTextArea notes = new JTextArea(3,15);
        JTextField photoUrl = new JTextField(15);
        if (existing != null) {
            firstName.setText(existing.firstName);
            lastName.setText(existing.lastName);
            phone.setText(existing.phone);
            email.setText(existing.email);
            address.setText(existing.address);
            group.setSelectedItem(existing.group);
            notes.setText(existing.notes);
            photoUrl.setText(existing.photoUrl);
        }
        addField(dialog, gbc, "Имя *:", firstName);
        addField(dialog, gbc, "Фамилия:", lastName);
        addField(dialog, gbc, "Телефон:", phone);
        addField(dialog, gbc, "Email:", email);
        addField(dialog, gbc, "Адрес:", address);
        addField(dialog, gbc, "Группа:", group);
        addField(dialog, gbc, "Заметки:", new JScrollPane(notes));
        addField(dialog, gbc, "Фото URL:", photoUrl);
        gbc.gridy++; gbc.gridx = 0; gbc.gridwidth = 2; gbc.anchor = GridBagConstraints.CENTER;
        JButton save = new JButton("Сохранить");
        save.addActionListener(e -> {
            if (firstName.getText().trim().isEmpty()) {
                JOptionPane.showMessageDialog(dialog, "Имя обязательно");
                return;
            }
            if (existing == null) {
                Contact c = new Contact(nextId++, firstName.getText().trim(), lastName.getText().trim(),
                        phone.getText().trim(), email.getText().trim(), address.getText().trim(),
                        (String) group.getSelectedItem(), notes.getText().trim(), photoUrl.getText().trim(),
                        java.time.LocalDateTime.now().toString());
                contacts.add(c);
            } else {
                existing.firstName = firstName.getText().trim();
                existing.lastName = lastName.getText().trim();
                existing.phone = phone.getText().trim();
                existing.email = email.getText().trim();
                existing.address = address.getText().trim();
                existing.group = (String) group.getSelectedItem();
                existing.notes = notes.getText().trim();
                existing.photoUrl = photoUrl.getText().trim();
            }
            saveContacts();
            refreshTable();
            dialog.dispose();
        });
        dialog.add(save, gbc);
        dialog.setVisible(true);
    }

    private void addField(JDialog dialog, GridBagConstraints gbc, String label, Component field) {
        gbc.gridx = 0; gbc.gridy++; gbc.gridwidth = 1;
        dialog.add(new JLabel(label), gbc);
        gbc.gridx = 1;
        dialog.add(field, gbc);
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new ContactManager().setVisible(true));
    }
}
