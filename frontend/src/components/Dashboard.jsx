import React, { useEffect, useState } from "react";
import logo from "../assets/SoochnaMitra_logo.png";
import api from "../api/client";
import { motion } from "framer-motion";
import { Info } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

export default function Dashboard() {
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [selectedState, setSelectedState] = useState("");
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [months, setMonths] = useState(12);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStates, setLoadingStates] = useState(false);
  const [loadingDistricts, setLoadingDistricts] = useState(false);
  const [error, setError] = useState("");
  const [lastRefreshed, setLastRefreshed] = useState(new Date());
  const [showInfo, setShowInfo] = useState(null);
  const [geoData, setGeoData] = useState(null);

  // Utility functions
  const toNumber = (v) => {
    if (v === null || v === undefined || v === "") return 0;
    const n = Number(v);
    if (!isNaN(n)) return n;
    try {
      return Number(String(v).replace(/,/g, ""));
    } catch {
      return 0;
    }
  };

  const formatCurrency = (num, fullLabel = false) => {
    if (!num) return "₹0";
    let label = "";
    if (num >= 10000000) label = " Crores";
    else if (num >= 100000) label = " Lakhs";
    const formatted = num.toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return fullLabel ? `₹${formatted}${label}` : `₹${formatted}`;
  };

  // Auto-refresh timer display
  useEffect(() => {
    const timer = setInterval(() => setLastRefreshed(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  // Fetch States
  useEffect(() => {
    const fetchStates = async () => {
      setLoadingStates(true);
      try {
        const res = await api.get("/states");
        setStates(res.data.states || []);
      } catch {
        setError("Failed to load states.");
      } finally {
        setLoadingStates(false);
      }
    };
    fetchStates();
  }, []);

  // Fetch Districts when State changes
  useEffect(() => {
    const fetchDistricts = async () => {
      if (!selectedState) {
        setDistricts([]);
        return;
      }
      setLoadingDistricts(true);
      try {
        const res = await api.get("/districts", {
          params: { state: selectedState },
        });
        setDistricts(res.data.districts || []);
      } catch {
        setError("Failed to load districts.");
      } finally {
        setLoadingDistricts(false);
      }
    };
    fetchDistricts();
  }, [selectedState]);

  // Detect user location on mount
  useEffect(() => {
    if (!("geolocation" in navigator)) return;

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const { latitude, longitude } = pos.coords;
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`
          );
          const data = await res.json();
          const districtName =
            data.address.district ||
            data.address.county ||
            data.address.state_district ||
            "";
          const stateName = data.address.state || data.address.region || "";

          if (districtName && stateName) {
            const confirm = window.confirm(
              `We detected your location as ${districtName}, ${stateName}. Do you want to see its MGNREGA data?`
            );
            if (confirm) {
              setGeoData({
                state: stateName.toUpperCase(),
                district: districtName.toUpperCase(),
              });
            }
          }
        } catch (e) {
          console.warn("Location fetch failed", e);
        }
      },
      () => console.log("User denied location access")
    );
  }, []);

  // Auto-select detected state and district
  useEffect(() => {
    const autoSelectDetected = async () => {
      if (!geoData || states.length === 0) return;

      const matchedState = states.find(
        (s) => s.toUpperCase() === geoData.state
      );
      if (matchedState) {
        setSelectedState(matchedState);
        setLoadingDistricts(true);
        try {
          const res = await api.get("/districts", {
            params: { state: matchedState },
          });
          const list = res.data.districts || [];
          setDistricts(list);

          // wait a tick to ensure React updates state before matching
          setTimeout(() => {
            const matchedDistrict = list.find(
              (d) => d.toUpperCase() === geoData.district
            );
            if (matchedDistrict) {
              setSelectedDistrict(matchedDistrict);
              loadDashboard(matchedState, matchedDistrict);
            }
          }, 500);
        } catch {
          setError("Failed to auto-load districts for detected state.");
        } finally {
          setLoadingDistricts(false);
        }
      }
    };
    autoSelectDetected();
  }, [geoData, states]);

  // Load dashboard data
  const loadDashboard = async (
    stateParam = selectedState,
    districtParam = selectedDistrict
  ) => {
    if (!stateParam || !districtParam) {
      alert("Please select both State and District.");
      return;
    }
    setLoading(true);
    try {
      const res = await api.get("/dashboard", {
        params: { state: stateParam, district: districtParam, months },
      });
      setDashboardData(res.data);
      setError("");
    } catch {
      setError("Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  const monthOrder = [
    "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
    "Dec", "Jan", "Feb", "Mar",
  ];

  // Prepare data for chart
  let monthlyData =
    dashboardData?.series?.map((s) => ({
      month: `${s.month.trim()} (${s.fin_year})`,
      monthName: s.month.trim(),
      finYear: s.fin_year,
      Expenditure: toNumber(s.expenditure),
      Households: toNumber(s.households),
    })) || [];

  // sort + remove duplicates
  monthlyData.sort(
    (a, b) =>
      a.finYear.localeCompare(b.finYear) ||
      monthOrder.indexOf(a.monthName) - monthOrder.indexOf(b.monthName)
  );
  const seen = new Set();
  monthlyData = monthlyData.filter((d) => {
    const key = `${d.monthName}-${d.finYear}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  monthlyData = monthlyData.slice(-months);

  const kpiExpenditure = toNumber(dashboardData?.kpis?.total_expenditure);
  const kpiHouseholds = toNumber(dashboardData?.kpis?.total_households_worked);
  const kpiPersondays = toNumber(dashboardData?.kpis?.total_persondays);

  const summary = dashboardData
    ? `In the last ${months} months, ${kpiHouseholds.toLocaleString()} families in ${dashboardData.district} collectively received ${formatCurrency(
        kpiExpenditure,
        true
      )} — total money spent by government (not per family).`
    : "";

  const kpiInfo = [
    {
      label: "💰 Total Expenditure",
      value: formatCurrency(kpiExpenditure),
      color: "from-indigo-50 to-blue-50",
      info_en:
        "Total money spent by the Government (Central + State share) on MGNREGA wages, materials and admin costs.",
      info_hi:
        "सरकार द्वारा मजदूरी, सामग्री और प्रशासन पर खर्च की गई कुल राशि (मनरेगा के तहत)।",
    },
    {
      label: "🏠 Families Worked",
      value: kpiHouseholds.toLocaleString(),
      color: "from-green-50 to-teal-50",
      info_en:
        "Number of families that got at least one person employed under MGNREGA.",
      info_hi: "जिन परिवारों को इस अवधि में मनरेगा के तहत काम मिला।",
    },
    {
      label: "👷‍♀️ Persondays",
      value: kpiPersondays.toLocaleString(),
      color: "from-yellow-50 to-orange-50",
      info_en:
        "One personday = one person working for one day. Example: 10 people × 10 days = 100 persondays.",
      info_hi:
        "‘एक व्यक्ति द्वारा एक दिन का काम’। उदाहरण: 10 लोग × 10 दिन = 100 व्यक्ति-दिवस।",
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
      className="min-h-screen bg-linear-to-br from-indigo-100 via-blue-50 to-sky-100 p-6 flex flex-col items-center"
    >
      <div className="flex items-center justify-center gap-4 mb-6">
        <img
          src={logo}
          alt="Soochna Mitra Logo"
          className="w-14 h-14 sm:w-16 sm:h-16 drop-shadow-lg"
        />
        <h1 className="text-4xl font-extrabold text-indigo-700 text-center">
          Soochna Mitra Dashboard
        </h1>
      </div>

      {/* Dropdowns */}
      <div className="flex flex-wrap justify-center gap-4 mb-4">
        <select
          className="border rounded-lg p-2 w-56"
          value={selectedState}
          onChange={(e) => {
            setSelectedState(e.target.value);
            setSelectedDistrict("");
          }}
          disabled={loadingStates}
        >
          <option value="">
            {loadingStates ? "Loading states..." : "Select State"}
          </option>
          {states.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <select
          className="border rounded-lg p-2 w-56"
          value={selectedDistrict}
          onChange={(e) => setSelectedDistrict(e.target.value)}
          disabled={!selectedState || loadingDistricts}
        >
          <option value="">
            {loadingDistricts
              ? "Loading districts..."
              : selectedState
              ? "Select District"
              : "Select State first"}
          </option>
          {districts.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>

        <select
          className="border rounded-lg p-2 w-44"
          value={months}
          onChange={(e) => setMonths(Number(e.target.value))}
        >
          <option value={1}>Past 1 month</option>
          <option value={3}>Past 3 months</option>
          <option value={6}>Past 6 months</option>
          <option value={12}>Past 12 months</option>
        </select>

        <motion.button
          whileTap={{ scale: 0.95 }}
          className={`px-6 py-2 rounded-lg text-white ${
            loading ? "bg-gray-400" : "bg-indigo-600 hover:bg-indigo-700"
          }`}
          onClick={() => loadDashboard()}
          disabled={loading}
        >
          {loading ? "Loading..." : "Go"}
        </motion.button>
      </div>

      {/* Dashboard */}
      {dashboardData && !loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="max-w-4xl w-full bg-white/80 p-6 mt-4 rounded-2xl shadow"
        >
          <h2 className="text-2xl font-semibold text-indigo-700 mb-2 text-center">
            {dashboardData.district}, {dashboardData.state}
          </h2>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            {kpiInfo.map((item, i) => (
              <div
                key={i}
                className={`relative p-4 rounded-xl bg-linear-to-br ${item.color} shadow text-center`}
              >
                <h3 className="font-semibold text-gray-700 flex items-center justify-center gap-2">
                  {item.label}
                  <Info
                    size={16}
                    className="text-gray-500 cursor-pointer hover:text-indigo-600"
                    onClick={() => setShowInfo(showInfo === i ? null : i)}
                  />
                </h3>
                <p className="text-xl font-bold mt-1">{item.value}</p>
                {showInfo === i && (
                  <div className="absolute z-10 top-full left-1/2 -translate-x-1/2 mt-2 bg-white shadow-lg border p-3 rounded-xl w-64 text-sm text-gray-700">
                    <p className="font-semibold">📘 English:</p>
                    <p>{item.info_en}</p>
                    <p className="font-semibold mt-2">🇮🇳 हिंदी:</p>
                    <p>{item.info_hi}</p>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Chart */}
          <div className="h-72 w-full mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip
                  formatter={(value, name) => [
                    name === "₹ Expenditure"
                      ? formatCurrency(value, true)
                      : value.toLocaleString(),
                    name,
                  ]}
                />
                <Legend />
                <Bar dataKey="Expenditure" fill="#4f46e5" name="₹ Expenditure" />
                <Bar
                  dataKey="Households"
                  fill="#f59e0b"
                  name="Families Worked"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <p className="text-center text-gray-700 font-medium">{summary}</p>
          {dashboardData.from_cache && (
            <p className="text-center text-sm text-gray-500 mt-2">
              ⚡ Cached Data (Last backend update:{" "}
              {new Date(dashboardData.last_updated).toLocaleString()})
            </p>
          )}

          <p className="mt-4 text-gray-500 text-sm text-center">
            Records: {dashboardData.kpis.records_count} • Last refreshed:{" "}
            {lastRefreshed.toLocaleTimeString()}
          </p>
        </motion.div>
      )}
    </motion.div>
  );
}
