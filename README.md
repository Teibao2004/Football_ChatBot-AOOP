# Football ChatBot AOOP

## 🇵🇹 Instalação e Utilização

### Pré-requisitos
- Python 3.8+
- Node.js 16+

### 1. Backend (Python + Flask)
1. Acede à pasta `backend`:
   ```bash
   cd backend
   ```
2. Cria e ativa um ambiente virtual:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```
3. Instala as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Cria um ficheiro `.env` com a tua API key do API-Sports:
   ```env
   APISPORTS_KEY=coloca_aqui_a_tua_api_key
   FLASK_ENV=development
   ```
5. Inicia o backend:
   ```bash
   python app.py
   ```

### 2. Frontend (Node.js + HTML/CSS/JS)
1. Acede à pasta `frontend`:
   ```bash
   cd ../frontend
   ```
2. Instala as dependências:
   ```bash
   npm install
   ```
3. Inicia o frontend:
   ```bash
   node server.js
   ```
4. Acede ao chatbot no browser:
   - Normalmente em [http://localhost:3000](http://localhost:3000)

---

## 🇬🇧 Installation and Usage

### Prerequisites
- Python 3.8+
- Node.js 16+

### 1. Backend (Python + Flask)
1. Go to the `backend` folder:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your API-Sports key:
   ```env
   APISPORTS_KEY=your_api_key_here
   FLASK_ENV=development
   ```
5. Start the backend:
   ```bash
   python app.py
   ```

### 2. Frontend (Node.js + HTML/CSS/JS)
1. Go to the `frontend` folder:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the frontend:
   ```bash
   node server.js
   ```
4. Open the chatbot in your browser:
   - Usually at [http://localhost:3000](http://localhost:3000)
   
---

Qualquer dúvida, consulta o código ou contacta o autor.
For any questions, check the code or contact the author.