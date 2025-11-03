// frontend/src/api.js
import axios from "axios";

const baseURL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.MODE === "development"
    ? "http://127.0.0.1:8000/api/v1"
    : "https://soochna-backend.onrender.com/api/v1");

const api = axios.create({
  baseURL,
});

export default api;
