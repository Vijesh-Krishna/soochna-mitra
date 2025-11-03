import axios from "axios";

const baseURL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.MODE === "development"
    ? "http://127.0.0.1:8000"
    : "https://soochna-backend.onrender.com");

const api = axios.create({
  baseURL,
});

export default api;
