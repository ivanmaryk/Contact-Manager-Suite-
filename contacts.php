<?php
// contacts.php - Менеджер контактов на PHP + MySQL (или JSON)
// Для простоты используем JSON-файл. Для MySQL раскомментируйте.
session_start();
$dataFile = 'contacts.json';

function loadContacts() {
    global $dataFile;
    if (file_exists($dataFile)) {
        $json = file_get_contents($dataFile);
        return json_decode($json, true) ?? [];
    }
    return [];
}

function saveContacts($contacts) {
    global $dataFile;
    file_put_contents($dataFile, json_encode(array_values($contacts), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

// Обработка API запросов
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_SERVER['HTTP_X_REQUESTED_WITH']) && $_SERVER['HTTP_X_REQUESTED_WITH'] === 'XMLHttpRequest') {
    header('Content-Type: application/json');
    $action = $_POST['action'] ?? '';
    $contacts = loadContacts();
    if ($action === 'add') {
        $newId = count($contacts) > 0 ? max(array_column($contacts, 'id')) + 1 : 1;
        $contact = [
            'id' => $newId,
            'firstName' => $_POST['firstName'],
            'lastName' => $_POST['lastName'],
            'phone' => $_POST['phone'],
            'email' => $_POST['email'],
            'address' => $_POST['address'],
            'group' => $_POST['group'],
            'notes' => $_POST['notes'],
            'photoUrl' => $_POST['photoUrl'],
            'created' => date('c')
        ];
        $contacts[] = $contact;
        saveContacts($contacts);
        echo json_encode($contact);
    } elseif ($action === 'edit') {
        $id = (int)$_POST['id'];
        foreach ($contacts as &$c) {
            if ($c['id'] == $id) {
                $c['firstName'] = $_POST['firstName'];
                $c['lastName'] = $_POST['lastName'];
                $c['phone'] = $_POST['phone'];
                $c['email'] = $_POST['email'];
                $c['address'] = $_POST['address'];
                $c['group'] = $_POST['group'];
                $c['notes'] = $_POST['notes'];
                $c['photoUrl'] = $_POST['photoUrl'];
                saveContacts($contacts);
                echo json_encode($c);
                exit;
            }
        }
        echo json_encode(['error' => 'Not found']);
    } elseif ($action === 'delete') {
        $id = (int)$_POST['id'];
        $contacts = array_filter($contacts, fn($c) => $c['id'] != $id);
        saveContacts($contacts);
        echo json_encode(['success' => true]);
    } elseif ($action === 'list') {
        $group = $_GET['group'] ?? 'all';
        $search = $_GET['search'] ?? '';
        $filtered = $contacts;
        if ($group !== 'all') $filtered = array_filter($filtered, fn($c) => $c['group'] == $group);
        if ($search) {
            $search = strtolower($search);
            $filtered = array_filter($filtered, function($c) use ($search) {
                return strpos(strtolower($c['firstName'].$c['lastName']), $search) !== false ||
                       strpos($c['phone'], $search) !== false ||
                       strpos(strtolower($c['email']), $search) !== false;
            });
        }
        echo json_encode(array_values($filtered));
    }
    exit;
}
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Контакты PHP</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin:0; padding:20px; }
        .container { max-width: 1200px; margin:0 auto; background:white; border-radius: 16px; box-shadow:0 2px 10px rgba(0,0,0,0.1); overflow:hidden; }
        .header { background:#2c3e50; color:white; padding:15px 20px; display:flex; gap:15px; flex-wrap:wrap; align-items:center; }
        .header input, .header select, .header button { padding:8px 12px; border-radius:20px; border:none; }
        .header button { background:#3498db; color:white; cursor:pointer; }
        .main { display:flex; min-height:500px; }
        .sidebar { width:40%; border-right:1px solid #ddd; padding:20px; }
        .contact-item { padding:10px; border-bottom:1px solid #eee; cursor:pointer; display:flex; align-items:center; gap:12px; }
        .contact-item:hover { background:#f5f5f5; }
        .avatar { width:40px; height:40px; background:#3498db; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-weight:bold; }
        .details { flex:1; padding:20px; background:#fafafa; }
        .modal { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); justify-content:center; align-items:center; }
        .modal-content { background:white; padding:20px; border-radius:16px; width:500px; max-width:90%; }
        .form-row { margin-bottom:12px; display:flex; }
        .form-row label { width:100px; }
        .form-row input, .form-row select, .form-row textarea { flex:1; }
        button { cursor:pointer; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h2 style="margin:0">📇 Менеджер контактов</h2>
        <input type="text" id="search" placeholder="Поиск...">
        <select id="groupFilter">
            <option value="all">Все группы</option>
            <option value="Family">Семья</option>
            <option value="Work">Работа</option>
            <option value="Friends">Друзья</option>
            <option value="Other">Другое</option>
        </select>
        <button id="addBtn">➕ Добавить</button>
    </div>
    <div class="main">
        <div class="sidebar" id="contactList"></div>
        <div class="details" id="details">Выберите контакт</div>
    </div>
</div>
<div id="modal" class="modal">
    <div class="modal-content">
        <h3 id="modalTitle">Новый контакт</h3>
        <div class="form-row"><label>Имя *</label><input type="text" id="firstName"></div>
        <div class="form-row"><label>Фамилия</label><input type="text" id="lastName"></div>
        <div class="form-row"><label>Телефон</label><input type="text" id="phone"></div>
        <div class="form-row"><label>Email</label><input type="email" id="email"></div>
        <div class="form-row"><label>Адрес</label><input type="text" id="address"></div>
        <div class="form-row"><label>Группа</label>
            <select id="group"><option>Family</option><option>Work</option><option>Friends</option><option>Other</option></select>
        </div>
        <div class="form-row"><label>Заметки</label><textarea id="notes" rows="3"></textarea></div>
        <div class="form-row"><label>Фото URL</label><input type="text" id="photoUrl"></div>
        <div style="text-align:right; margin-top:20px">
            <button id="saveModalBtn">Сохранить</button>
            <button id="cancelModalBtn">Отмена</button>
        </div>
    </div>
</div>
<script>
    let currentContactId = null;
    async function fetchContacts() {
        const search = document.getElementById('search').value;
        const group = document.getElementById('groupFilter').value;
        const url = `?action=list&group=${group}&search=${encodeURIComponent(search)}`;
        const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const contacts = await res.json();
        renderList(contacts);
    }
    function renderList(contacts) {
        const container = document.getElementById('contactList');
        container.innerHTML = '';
        contacts.forEach(c => {
            const div = document.createElement('div');
            div.className = 'contact-item';
            if (currentContactId === c.id) div.classList.add('active');
            const avatar = document.createElement('div');
            avatar.className = 'avatar';
            avatar.textContent = (c.firstName[0] || '') + (c.lastName[0] || '');
            const info = document.createElement('div');
            info.innerHTML = `<strong>${c.firstName} ${c.lastName}</strong><br><small>${c.phone || '-'}</small>`;
            div.appendChild(avatar);
            div.appendChild(info);
            div.onclick = () => showDetails(c.id);
            container.appendChild(div);
        });
    }
    async function showDetails(id) {
        const contacts = await fetchContactsData();
        const contact = contacts.find(c => c.id == id);
        if (!contact) return;
        currentContactId = id;
        const detailsDiv = document.getElementById('details');
        detailsDiv.innerHTML = `
            <h3>${contact.firstName} ${contact.lastName}</h3>
            <p><strong>Телефон:</strong> ${contact.phone || '—'}</p>
            <p><strong>Email:</strong> ${contact.email || '—'}</p>
            <p><strong>Адрес:</strong> ${contact.address || '—'}</p>
            <p><strong>Группа:</strong> ${contact.group || '—'}</p>
            <p><strong>Заметки:</strong> ${contact.notes || '—'}</p>
            <button id="editDetailBtn">✏️ Редактировать</button>
            <button id="deleteDetailBtn" style="background:#e74c3c;color:white">🗑 Удалить</button>
        `;
        document.getElementById('editDetailBtn').onclick = () => openModal(contact);
        document.getElementById('deleteDetailBtn').onclick = async () => {
            if (confirm('Удалить контакт?')) {
                await fetch('', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest' }, body: `action=delete&id=${contact.id}` });
                fetchContacts();
                detailsDiv.innerHTML = 'Контакт удалён';
                currentContactId = null;
            }
        };
        // подсветка
        document.querySelectorAll('.contact-item').forEach(el => el.classList.remove('active'));
        const active = Array.from(document.querySelectorAll('.contact-item')).find(el => el.innerText.includes(contact.firstName));
        if (active) active.classList.add('active');
    }
    async function fetchContactsData() {
        const res = await fetch('?action=list&group=all', { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        return await res.json();
    }
    function openModal(contact = null) {
        const modal = document.getElementById('modal');
        document.getElementById('modalTitle').innerText = contact ? 'Редактировать' : 'Новый контакт';
        document.getElementById('firstName').value = contact ? contact.firstName : '';
        document.getElementById('lastName').value = contact ? contact.lastName : '';
        document.getElementById('phone').value = contact ? contact.phone : '';
        document.getElementById('email').value = contact ? contact.email : '';
        document.getElementById('address').value = contact ? contact.address : '';
        document.getElementById('group').value = contact ? contact.group : 'Family';
        document.getElementById('notes').value = contact ? contact.notes : '';
        document.getElementById('photoUrl').value = contact ? contact.photoUrl : '';
        modal.style.display = 'flex';
        const saveBtn = document.getElementById('saveModalBtn');
        const cancelBtn = document.getElementById('cancelModalBtn');
        const saveHandler = async () => {
            const data = {
                action: contact ? 'edit' : 'add',
                id: contact ? contact.id : null,
                firstName: document.getElementById('firstName').value,
                lastName: document.getElementById('lastName').value,
                phone: document.getElementById('phone').value,
                email: document.getElementById('email').value,
                address: document.getElementById('address').value,
                group: document.getElementById('group').value,
                notes: document.getElementById('notes').value,
                photoUrl: document.getElementById('photoUrl').value
            };
            if (!data.firstName) { alert('Имя обязательно'); return; }
            const body = new URLSearchParams(data).toString();
            await fetch('', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest' }, body });
            modal.style.display = 'none';
            fetchContacts();
            if (contact && contact.id) showDetails(contact.id);
            else document.getElementById('details').innerHTML = 'Контакт добавлен';
        };
        saveBtn.onclick = saveHandler;
        cancelBtn.onclick = () => modal.style.display = 'none';
        // Убираем старые, но переопределяем
    }
    document.getElementById('search').addEventListener('input', fetchContacts);
    document.getElementById('groupFilter').addEventListener('change', fetchContacts);
    document.getElementById('addBtn').onclick = () => openModal();
    fetchContacts();
</script>
</body>
</html>
