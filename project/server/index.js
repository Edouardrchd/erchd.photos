import express from 'express';
import mysql from 'mysql2/promise';
import multer from 'multer';
import cors from 'cors';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import bodyParser from 'body-parser';

dotenv.config();

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const port = 3000;

// Configuration de multer pour le stockage des images
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, join(__dirname, '../uploads'))
  },
  filename: function (req, file, cb) {
    cb(null, Date.now() + '-' + file.originalname)
  }
});

const upload = multer({ storage: storage });

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use('/uploads', express.static(join(__dirname, '../uploads')));

// Configuration MySQL
const pool = mysql.createPool({
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'sports_portfolio',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

// Routes pour les images
app.post('/api/images', upload.single('image'), async (req, res) => {
  try {
    const { category } = req.body;
    const imagePath = `/uploads/${req.file.filename}`;
    
    const [result] = await pool.execute(
      'INSERT INTO images (path, category) VALUES (?, ?)',
      [imagePath, category]
    );
    
    res.json({ success: true, id: result.insertId, path: imagePath });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Erreur lors du téléchargement de l\'image' });
  }
});

app.get('/api/images/:category', async (req, res) => {
  try {
    const [rows] = await pool.execute(
      'SELECT * FROM images WHERE category = ?',
      [req.params.category]
    );
    res.json(rows);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Erreur lors de la récupération des images' });
  }
});

// Route pour les formulaires utilisateurs
app.post('/api/contact', async (req, res) => {
  try {
    const { name, email, message } = req.body;
    const [result] = await pool.execute(
      'INSERT INTO user_messages (name, email, message) VALUES (?, ?, ?)',
      [name, email, message]
    );
    res.json({ success: true, id: result.insertId });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Erreur lors de l\'envoi du message' });
  }
});

// Route pour les inscriptions newsletter
app.post('/api/subscribe', async (req, res) => {
  try {
    const { email } = req.body;
    await pool.execute(
      'INSERT INTO subscribers (email) VALUES (?)',
      [email]
    );
    res.json({ success: true });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Erreur lors de l\'inscription' });
  }
});

app.listen(port, () => {
  console.log(`Serveur démarré sur le port ${port}`);
});