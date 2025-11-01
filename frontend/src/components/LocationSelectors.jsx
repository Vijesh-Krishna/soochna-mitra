import { useState, useEffect } from "react";
import api from "../api/client";

export default function LocationSelectors({ onSelect }) {
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [state, setState] = useState("");
  const [district, setDistrict] = useState("");

  useEffect(() => {
    api.get("/states").then(res => setStates(res.data));
  }, []);

  useEffect(() => {
    if (state) {
      api.get(`/districts?state=${state}`).then(res => setDistricts(res.data));
    }
  }, [state]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSelect({ state, district });
  };

  return (
    <form className="flex gap-4 items-center justify-center mt-4" onSubmit={handleSubmit}>
      <select
        className="p-2 border rounded-lg"
        value={state}
        onChange={(e) => setState(e.target.value)}
      >
        <option value="">Select State</option>
        {states.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>

      <select
        className="p-2 border rounded-lg"
        value={district}
        onChange={(e) => setDistrict(e.target.value)}
        disabled={!state}
      >
        <option value="">Select District</option>
        {districts.map((d) => (
          <option key={d} value={d}>{d}</option>
        ))}
      </select>

      <button className="px-4 py-2 bg-blue-600 text-white rounded-lg">Go</button>
    </form>
  );
}
