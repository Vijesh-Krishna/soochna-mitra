import api from "../api/client";

export default function RefreshButton({ onRefresh }) {
  const handleClick = async () => {
    if (!confirm("Run ETL refresh now?")) return;
    await api.post("/refresh");
    onRefresh();
  };

  return (
    <button className="mt-4 px-4 py-2 bg-green-600 text-white rounded-lg" onClick={handleClick}>
      🔄 Refresh Data
    </button>
  );
}
