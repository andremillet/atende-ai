# Atende-AI: Medical Record Management System

## Overview
**Atende-AI** is a web-based application designed to streamline the creation, management, and consultation of medical records (prontuários) for healthcare professionals. Built with Flask, SQLite, HTML, JavaScript, and Tailwind CSS, it provides a modern, user-friendly interface for managing patient data, medications, and appointment histories. The system supports multiple patients, identified by CPF (Brazilian ID number), and ensures persistent storage of critical information like medications and medical history.

Developed as of May 21, 2025, Atende-AI addresses the need for a lightweight, customizable electronic medical record (EMR) solution, with a focus on usability and compliance with medical workflows.

## Key Features

### Patient Management
- **Search by Name or CPF**: Locate existing patients using partial or full matches for name or CPF.
- **New Patient Creation**: Suggests creating a new patient if no match is found, pre-filling CPF or name from the search query.
- **Persistent Patient Data**: Stores patient details (CPF, name) in a SQLite database.

### Medical Record Creation
- **Structured Form**: Create prontuários with sections for Anamnese, Exame Físico, Hipótese Diagnóstica, and Conduta.
- **Medication Management**:
  - List regular medications in Anamnese with start dates (e.g., `FLUOXETINA 20MG[12/01/2020]` or `LAMOTRIGINA 100MG[>5A]`).
  - Modify medications only via Conduta:
    - `+`: Add new medication.
    - `++`: Increment dose.
    - `-`: Suspend medication.
    - `!`: Update form/administration (e.g., `!VENLAFAXINA > VENLIFT OD 150MG`).
    - `--`: Reduce dose.
  - All changes are logged with the current date (e.g., `+SERTRALINA 25MG [21/05/2025]`).
- **Date Handling**: Supports exact (DD/MM/YYYY) or estimated dates (`>5A`, `5M`, `5S`, `5D`), case-insensitive. Uses appointment date if missing, with a discreet alert.
- **Output Format**: Generates `.txt` files in a standardized format, downloadable after saving.

### Consultation Interface
- **Sidebar (Informações Relevantes)**:
  - Displays persistent items: História Patológica Pregressa (HPP), other relevant information (INFO), and recent appointments (up to 5).
  - Recent appointments are listed as `Atendimento: DD/MM/YYYY`, clickable for view-only access.
- **Main Div**:
  - Shows regular medications (e.g., `FLUOXETINA 20MG[12/01/2020]`) in a read-only list.
- **Modal View**: View past prontuários in a centered modal dialog, displayed as plain text, non-editable.

### Data Persistence
- **SQLite Database**:
  - `patients`: Stores CPF (primary key) and name.
  - `persistent_items`: Stores HPP, INFO, and medications (with `start_date` for MED items).
  - `prontuarios`: Tracks prontuário files with CPF, filename, and creation date.
- **File Storage**: Prontuários are saved as `.txt` in the `prontuarios` directory, named as `PatientName_CPF_Timestamp.txt`.

## Technical Details

### Tech Stack
- **Backend**: Flask (Python 3.13) for routing and database interactions.
- **Database**: SQLite for lightweight, file-based storage.
- **Frontend**: HTML, JavaScript, Tailwind CSS for a modern, responsive UI.
- **Dependencies**: Flask (`pip install flask`).

### Directory Structure
```
atende-ai/
├── app.py
├── prontuarios/               # Stores .txt prontuários
├── prontuarios.db            # SQLite database
├── templates/
│   └── index.html
```

### Database Schema
- **patients**:
  - `cpf` (TEXT, PRIMARY KEY)
  - `name` (TEXT)
- **persistent_items**:
  - `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
  - `cpf` (TEXT, FOREIGN KEY)
  - `category` (TEXT: `MED`, `HPP`, `INFO`)
  - `item` (TEXT)
  - `start_date` (TEXT, for `MED` items)
- **prontuarios**:
  - `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
  - `cpf` (TEXT, FOREIGN KEY)
  - `filename` (TEXT)
  - `created_at` (DATETIME)

### Key Endpoints
- `GET /`: Renders the main interface (`index.html`).
- `POST /search_patients`: Searches patients by name or CPF.
- `POST /save_prontuario`: Saves a new or edited prontuário as `.txt` and updates the database.
- `POST /get_persistent_items`: Fetches persistent items and recent prontuários for a patient.
- `GET /load_prontuario/<filename>`: Loads a prontuário for viewing.
- `GET /download_prontuario/<filename>`: Downloads a prontuário `.txt`.

## Usage Guide

### Setup
1. **Install Dependencies**:
   ```bash
   pip install flask
   ```
2. **Directory Setup**:
   - Place `app.py` in the project root.
   - Create a `templates` folder with `index.html`.
   - Ensure the `prontuarios` folder exists for storing `.txt` files.
3. **Run the Application**:
   ```bash
   python app.py
   ```
   - Access at `http://localhost:5000`.

### Workflow
1. **Search or Create a Patient**:
   - Enter a CPF (e.g., `12345678900`) or name (e.g., `Carlos Matheus`) in the search bar.
   - Select an existing patient or click "Criar Novo Paciente" if none found.
2. **View Patient Data**:
   - **Main Div**: Displays regular medications (e.g., `FLUOXETINA 20MG[12/01/2020]`), read-only.
   - **Sidebar**:
     - Persistent items: `HPP: TOD`, `JA INICIOU ATIVIDADE FISICA`.
     - Recent appointments: `Atendimento: 21/05/2025`, clickable to view in a modal.
3. **Create a Prontuário**:
   - Fill the form:
     - **Anamnese**: Add medications with dates (e.g., `SERTRALINA 25MG[01/01/2023];LAMOTRIGINA 100MG[5M]`), HPP, and other info.
     - **Conduta**: Modify medications (e.g., `+CLONAZEPAM 1MG`, `-VENLAFAXINA 150MG`), logged with the current date.
   - If medication dates are missing, an alert appears, and the current date (e.g., `21/05/2025`) is used.
   - Click "Salvar e Baixar" to save and download the `.txt`.
4. **Consult Past Appointments**:
   - Click a recent atendimento in the sidebar to view its content in a centered modal, non-editable.

### Example Prontuário Output
```text
[ANAMNESE]
PACIENTE COM QUEIXAS DE ANSIEDADE
!!MED SERTRALINA 25MG[01/01/2023];LAMOTRIGINA 100MG[21/05/2025]
!!HPP TOD;AUTISMO INFANTIL
!!JA INICIOU ATIVIDADE FISICA
[EXAME FISICO]
VIGIL, COOPERATIVO
[HIPOTESE DIAGNOSTICA]
TRANSTORNO DE ANSIEDADE GENERALIZADA
[CONDUTA]
+CLONAZEPAM 1MG [21/05/2025]
++SERTRALINA 50MG [21/05/2025]
-VENLAFAXINA 150MG [21/05/2025]
```

## Future Improvements
- **Prontuário Editing**: Reintroduce editing via a sidebar button or form, distinguishing between view and edit modes.
- **Date Validation**: Enforce stricter formats for medication dates (e.g., regex for `DD/MM/YYYY` or estimates).
- **Formatted Modal**: Display prontuários in the modal with HTML styling (e.g., bold sections, lists).
- **Security**: Add authentication, input sanitization, and LGPD/HIPAA compliance for production.
- **Scalability**: Migrate to PostgreSQL for larger-scale deployments, as discussed previously (04/10/2025).
- **Format Support**: Integrate `.med` format (mentioned 04/08/2025) or FHIR standards for interoperability.

## Security Considerations
- **Current State**: Suitable for development or local use. Lacks authentication and input validation.
- **Production Needs**:
  - Implement user authentication (e.g., OAuth, JWT).
  - Sanitize inputs to prevent SQL injection or XSS.
  - Encrypt sensitive data (CPF, medical records) and ensure LGPD compliance.

## Conclusion
Atende-AI is a robust, user-centric solution for managing medical records, tailored to the needs of healthcare professionals. Its intuitive interface, persistent data storage, and flexible medication management make it a valuable tool for small clinics or individual practitioners. With planned enhancements, it can scale to larger systems and integrate with industry standards.

For further details or contributions, contact the development team or refer to the project repository.

*Last Updated: May 21, 2025*