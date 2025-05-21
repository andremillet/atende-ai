from flask import Flask, render_template, request, jsonify, send_file
import os
import sqlite3
from datetime import datetime
import re

app = Flask(__name__)

# Diretório para salvar prontuários
PRONTUARIOS_DIR = "prontuarios"
if not os.path.exists(PRONTUARIOS_DIR):
    os.makedirs(PRONTUARIOS_DIR)

# Inicializa e migra o banco de dados
def init_db():
    with sqlite3.connect('prontuarios.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS patients (
                     cpf TEXT PRIMARY KEY,
                     name TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS persistent_items (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     cpf TEXT,
                     item TEXT,
                     category TEXT,
                     start_date TEXT,
                     FOREIGN KEY (cpf) REFERENCES patients (cpf))''')
        c.execute('''CREATE TABLE IF NOT EXISTS prontuarios (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     cpf TEXT,
                     filename TEXT,
                     created_at DATETIME,
                     FOREIGN KEY (cpf) REFERENCES patients (cpf))''')
        
        # Verifica e adiciona colunas
        c.execute("PRAGMA table_info(persistent_items)")
        columns = [col[1] for col in c.fetchall()]
        if 'category' not in columns:
            c.execute('ALTER TABLE persistent_items ADD COLUMN category TEXT')
            c.execute("UPDATE persistent_items SET category = 'INFO' WHERE category IS NULL")
        if 'start_date' not in columns:
            c.execute('ALTER TABLE persistent_items ADD COLUMN start_date TEXT')
        
        conn.commit()

init_db()

# Função para parsear prontuário
def parse_prontuario(content):
    sections = {'ANAMNESE': [], 'EXAME FISICO': [], 'HIPOTESE DIAGNOSTICA': [], 'CONDUTA': []}
    current_section = None
    persistent_items = []

    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('[') and line.endswith(']'):
            section_name = line[1:-1]
            if section_name in sections:
                current_section = section_name
            continue
        if line.startswith('!!'):
            item = line[2:].strip()
            if item.startswith('MED '):
                meds = item[4:].split(';')
                for med in meds:
                    if med.strip():
                        # Extrai data entre colchetes, se presente
                        match = re.match(r'(.+?)(?:\[(.+?)\])?$', med.strip())
                        if match:
                            med_name, date = match.groups()
                            med_name = med_name.strip()
                            date = date or None
                            persistent_items.append({'category': 'MED', 'item': med_name, 'start_date': date})
                            if current_section:
                                sections[current_section].append({'type': 'menu_item', 'content': f"MED: {med_name}{f'[{date}]' if date else ''}"})
            elif item.startswith('HPP '):
                conditions = item[4:].split(';')
                for cond in conditions:
                    if cond.strip():
                        persistent_items.append({'category': 'HPP', 'item': cond.strip(), 'start_date': None})
                        if current_section:
                            sections[current_section].append({'type': 'menu_item', 'content': f"HPP: {cond.strip()}"})
            else:
                persistent_items.append({'category': 'INFO', 'item': item, 'start_date': None})
                if current_section:
                    sections[current_section].append({'type': 'menu_item', 'content': item})
        elif line.startswith(('!', '+', '--', '>>', '>')):
            if current_section:
                sections[current_section].append({'type': 'action_item', 'content': line})
        elif current_section:
            sections[current_section].append({'type': 'text', 'content': line})

    return sections, persistent_items

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search_patients', methods=['POST'])
def search_patients():
    query = request.form.get('query', '').strip()
    with sqlite3.connect('prontuarios.db') as conn:
        c = conn.cursor()
        c.execute('SELECT cpf, name FROM patients WHERE cpf LIKE ? OR name LIKE ?', (f'%{query}%', f'%{query}%'))
        patients = [{'cpf': row[0], 'name': row[1]} for row in c.fetchall()]
    return jsonify({'patients': patients})

@app.route('/save_prontuario', methods=['POST'])
def save_prontuario():
    data = request.form
    cpf = data.get('cpf', '').strip()
    patient_name = data.get('patient_name', 'Paciente_Sem_Nome').replace(' ', '_')
    content = data.get('content', '')
    is_edit = data.get('is_edit', 'false') == 'true'
    original_filename = data.get('original_filename', '')
    current_date = datetime.now().strftime('%d/%m/%Y')

    with sqlite3.connect('prontuarios.db') as conn:
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO patients (cpf, name) VALUES (?, ?)', (cpf, patient_name))
        
        # Processa mudanças em medicamentos a partir de CONDUTA
        medication_changes = []
        persistent_items = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('!!'):
                item = line[2:].strip()
                if item.startswith('MED '):
                    for med in item[4:].split(';'):
                        if med.strip():
                            match = re.match(r'(.+?)(?:\[(.+?)\])?$', med.strip())
                            if match:
                                med_name, date = match.groups()
                                med_name = med_name.strip()
                                date = date or current_date
                                persistent_items.append(('MED', med_name, date))
                elif item.startswith('HPP '):
                    for cond in item[4:].split(';'):
                        if cond.strip():
                            persistent_items.append(('HPP', cond.strip(), None))
                else:
                    persistent_items.append(('INFO', item, None))
            elif line.startswith(('-', '++', '!', '--')) and '[CONDUTA]' in content[:content.index(line)]:
                # Processa mudanças de medicamentos
                if line.startswith('-'):
                    med = line[1:].strip()
                    medication_changes.append(('REMOVE', med, current_date))
                elif line.startswith('++'):
                    med = line[2:].strip()
                    medication_changes.append(('INCREMENT', med, current_date))
                elif line.startswith('!'):
                    med = line[1:].strip()
                    medication_changes.append(('UPDATE', med, current_date))
                elif line.startswith('--'):
                    med = line[2:].strip()
                    medication_changes.append(('REDUCE', med, current_date))

        # Atualiza persistent_items com mudanças
        c.execute('DELETE FROM persistent_items WHERE cpf = ? AND category = ?', (cpf, 'MED'))
        for category, item, date in persistent_items:
            c.execute('INSERT OR IGNORE INTO persistent_items (cpf, category, item, start_date) VALUES (?, ?, ?, ?)', 
                      (cpf, category, item, date))
        
        # Gera nome do arquivo
        if is_edit and original_filename:
            filename = original_filename
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{patient_name}_{cpf}_{timestamp}.txt"

        # Salva arquivo
        filepath = os.path.join(PRONTUARIOS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        if not is_edit:
            c.execute('INSERT INTO prontuarios (cpf, filename, created_at) VALUES (?, ?, ?)',
                      (cpf, filename, datetime.now()))
        conn.commit()

    return jsonify({'filename': filename, 'filepath': filepath, 'medication_changes': medication_changes})

@app.route('/get_prontuarios', methods=['POST'])
def get_prontuarios():
    cpf = request.form.get('cpf', '')
    with sqlite3.connect('prontuarios.db') as conn:
        c = conn.cursor()
        c.execute('SELECT filename, created_at FROM prontuarios WHERE cpf = ? ORDER BY created_at DESC LIMIT 5', (cpf,))
        prontuarios = [{'filename': row[0], 'created_at': row[1]} for row in c.fetchall()]
    return jsonify({'prontuarios': prontuarios})

@app.route('/load_prontuario/<filename>', methods=['GET'])
def load_prontuario(filename):
    filepath = os.path.join(PRONTUARIOS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        sections, _ = parse_prontuario(content)
        return jsonify({'sections': sections, 'content': content, 'filename': filename})
    return jsonify({'error': 'Arquivo não encontrado'}), 404

@app.route('/get_persistent_items', methods=['POST'])
def get_persistent_items():
    cpf = request.form.get('cpf', '')
    with sqlite3.connect('prontuarios.db') as conn:
        c = conn.cursor()
        c.execute('SELECT category, item, start_date FROM persistent_items WHERE cpf = ?', (cpf,))
        items = [{'category': row[0], 'item': row[1], 'start_date': row[2]} for row in c.fetchall()]
        c.execute('SELECT filename, created_at FROM prontuarios WHERE cpf = ? ORDER BY created_at DESC LIMIT 5', (cpf,))
        prontuarios = [{'filename': row[0], 'created_at': row[1]} for row in c.fetchall()]
    return jsonify({'items': items, 'prontuarios': prontuarios})

@app.route('/download_prontuario/<filename>', methods=['GET'])
def download_prontuario(filename):
    filepath = os.path.join(PRONTUARIOS_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'Arquivo não encontrado'}), 404

if __name__ == '__main__':
    app.run(debug=True)