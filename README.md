# 📚 Flask Book API – "The Reader"

Welcome to **Flask Book API**, a RESTful service built with Flask, created specifically for the **"The Reader"** Android App. This API allows users to upload, manage, and access PDF books with associated metadata and thumbnails.

---

## 🚀 Features

- 📤 Upload PDF files with metadata and thumbnails  
- 📄 Read all uploaded book entries  
- 🛠️ Update book information  
- ❌ Delete books by ID  
- 🔍 Search books by title or author  
- 🏡 Beautiful root landing page (HTML-based)

---

## 👨‍💻 Developer

**Name**: Sumon Kumar  
[🔗 LinkedIn](https://www.linkedin.com/in/sumonkmr/)

---

## 🛠️ Technologies Used

- Python 3.11+  
- Flask  
- Flask-SQLAlchemy  
- SQLite (Default DB)  
- HTML (for root page)  
- RESTful API Design

---

## 📂 Project Structure

```
flask-book-api-the-reader/
│
├── templates/
│   └── index.html               # Landing page
│
├── uploads/                     # PDF and thumbnails stored here
│
├── app.py                       # Main Flask app
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation
```

---

## ⚙️ Installation & Setup

1. **Clone the Repository**

```bash
git clone https://github.com/yourusername/flask-book-api-the-reader.git
cd flask-book-api-the-reader
```

2. **Create a Virtual Environment**

```bash
python -m venv myenv
source myenv/bin/activate  # For Linux/Mac
myenv\Scripts\activate     # For Windows
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Run the App**

```bash
python app.py
```

Server will start at:  
`http://127.0.0.1:5000/`

---

## 🌐 Deployed URL

**Live Root Endpoint**:  
[https://flask-book-api-the-reader.onrender.com](https://flask-book-api-the-reader.onrender.com)

---

## 📬 API Endpoints

| Method   | Endpoint                                              | Description                         |
|----------|-------------------------------------------------------|-------------------------------------|
| `GET`    | `/`                                                   | Homepage with project info          |
| `GET`    | `/pdfs`                                               | List all uploaded PDFs              |
| `POST`   | `/upload`                                             | Upload PDF + metadata + thumbnail   |
| `PUT`    | `/update/<int:id>`                                    | Update metadata by ID               |
| `DELETE` | `/delete/<int:id>`                                    | Delete a book by ID                 |
| `GET`    | `/search?query=<search_term>`                         | Search by title or author           |

---

## 📥 Example POST Request (Using Postman)

**Endpoint:**  
`POST https://flask-book-api-the-reader.onrender.com/upload`

**Form-Data Body:**

```
title: Python Crash Course  
author: Eric Matthes  
category: International  
pdf_file: [select file]  
thumbnail: [select image]
```

---

## 📌 Metadata Format for Upload

When uploading a file, make sure to send metadata as `form-data`:

- `title`: (string)  
- `author`: (string)  
- `category`: (string)  
- `pdf_file`: (file)  
- `thumbnail`: (file)

---

## ❤️ Acknowledgments

This API was developed with passion to support readers through **The Reader Android App**. Your feedback and contributions are welcome!

---

## 📃 License

This project is open source and available under the [MIT License](LICENSE).
