import React, { useEffect, useState, useRef } from "react";
import logo from "../assets/SoochnaMitra_logo.png";
import api from "../api/client";
import { motion } from "framer-motion";
import { MapPin, Info } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, CartesianGrid, } from "recharts";

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
  const [geoData, setGeoData] = useState(null);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [activeTooltip, setActiveTooltip] = useState(null);
  const tooltipRef = useRef(null);

  // NEW: guard so automatic detectLocation runs only once (avoids double prompt in Strict Mode)
  const initialDetectRunRef = useRef(false);

  // close tooltip on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (tooltipRef.current && !tooltipRef.current.contains(e.target)) {
        setActiveTooltip(null);
      }
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const toNumber = (v) => {
    if (v === null || v === undefined || v === "") return 0;
    const n = Number(String(v).replace(/,/g, ""));
    return isNaN(n) ? 0 : n;
  };

  // Format currency properly
  const formatCurrency = (num) => {
    if (!num) return "₹0";
    const value = Number(num);
    if (value >= 100) return `₹ ${(value / 100).toFixed(2)} crore`;
    return `₹ ${value.toFixed(2)} lakh`;
  };

  // Load states
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

  // Load districts
  useEffect(() => {
    const fetchDistricts = async () => {
      if (!selectedState) {
        setDistricts([]);
        return;
      }
      setLoadingDistricts(true);
      try {
        const res = await api.get("/districts", { params: { state: selectedState } });
        setDistricts(res.data.districts || []);
      } catch {
        setError("Failed to load districts.");
      } finally {
        setLoadingDistricts(false);
      }
    };
    fetchDistricts();
  }, [selectedState]);

  // Detect location
  const detectLocation = async () => {
    if (!("geolocation" in navigator)) {
      alert("Your device does not support geolocation.");
      return;
    }
    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          try {
            const { latitude, longitude } = pos.coords;
            const res = await fetch(
              `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&zoom=10&format=json`
            );
            const data = await res.json();

            let districtName =
              data.address.district ||
              data.address.state_district ||
              data.address.county ||
              data.address.city_district ||
              "";
            districtName = districtName.replace(/\b(taluk|block|subdivision)\b/gi, "").trim();
            const stateName =
              data.address.state || data.address.region || data.address.state_name || "";

            if (districtName && stateName) {
              const confirm = window.confirm(
                `Detected location: ${districtName}, ${stateName}. View its MGNREGA data?`
              );
              if (confirm) {
                setGeoData({
                  state: stateName.toUpperCase(),
                  district: districtName.toUpperCase(),
                });
              }
              resolve(true);
            } else {
              alert("Could not determine district/state from GPS coordinates.");
              resolve(false);
            }
          } catch (e) {
            console.error("Location fetch failed:", e);
            alert("Failed to detect location. Please try again.");
            resolve(false);
          }
        },
        (err) => {
          console.warn("Location permission denied:", err);
          resolve(false);
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    });
  };

  // CHANGED: only run automatic detect once (prevents duplicate confirm/alert on initial mount)
  useEffect(() => {
    if (!initialDetectRunRef.current) {
      initialDetectRunRef.current = true;
      detectLocation();
    }
  }, []);

  useEffect(() => {
    const autoSelect = async () => {
      if (!geoData || states.length === 0) return;
      const matchedState = states.find((s) => s.toUpperCase() === geoData.state);
      if (matchedState) {
        setSelectedState(matchedState);
        setLoadingDistricts(true);
        try {
          const res = await api.get("/districts", { params: { state: matchedState } });
          const list = res.data.districts || [];
          setDistricts(list);
          setTimeout(() => {
            const matchedDistrict = list.find((d) => d.toUpperCase() === geoData.district);
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
    autoSelect();
  }, [geoData, states]);

  const loadDashboard = async (stateParam = selectedState, districtParam = selectedDistrict) => {
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

  const monthOrder = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"];
  let monthlyData =
    dashboardData?.series?.map((s) => ({
      month: `${s.month.trim()} (${s.fin_year})`,
      monthName: s.month.trim(),
      finYear: s.fin_year,
      Expenditure: toNumber(s.expenditure),
      Households: toNumber(s.households),
    })) || [];

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
    ? `During this period, ${kpiHouseholds.toLocaleString()} families in ${dashboardData.district} collectively earned wages amounting to ${formatCurrency(
        kpiExpenditure
      )} under the MGNREGA scheme.`
    : "";

  const kpiInfo = [
    {
      label: "💰 Total Expenditure",
      value: formatCurrency(kpiExpenditure),
      color: "from-indigo-50 to-blue-50",
      tooltip: {
        en: "📘 English:\nTotal expenditure includes government spending (Central + State) on wages, materials, and administrative costs under MGNREGA. Amounts are in lakh rupees; 100 lakh = 1 crore.",
        hi: "🇮🇳 हिंदी:\nकुल व्यय में मनरेगा के तहत मजदूरी, सामग्री और प्रशासन पर केंद्र व राज्य सरकार द्वारा किया गया खर्च शामिल है। राशि लाख रुपये में है (100 लाख = 1 करोड़)।",
      },
    },
    {
      label: "🏠 Families Worked",
      value: kpiHouseholds.toLocaleString(),
      color: "from-green-50 to-teal-50",
      tooltip: {
        en: "📘 English:\nTotal number of unique households that worked under MGNREGA during the selected period.",
        hi: "🇮🇳 हिंदी:\nचयनित अवधि के दौरान मनरेगा के अंतर्गत कार्य करने वाले कुल परिवारों की संख्या।",
      },
    },
    {
      label: "👷‍♀️ Person-days",
      value: kpiPersondays.toLocaleString(),
      color: "from-yellow-50 to-orange-50",
      tooltip: {
        en: "📘 English:\nTotal person-days generated under MGNREGA (1 person working for 1 day = 1 person-day).",
        hi: "🇮🇳 हिंदी:\nमनरेगा के अंतर्गत सृजित कुल मानव-दिवस (1 व्यक्ति का 1 दिन का कार्य = 1 मानव-दिवस)।",
      },
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
      className="min-h-screen bg-linear-to-br from-indigo-100 via-blue-50 to-sky-100 p-6 flex flex-col items-center relative"
    >
      {/* Header */}
      <div className="w-full flex justify-center mb-6">
        <div className="flex items-center justify-between w-full max-w-4xl px-4">
          <img src={logo} alt="Soochna Mitra Logo" className="w-10 h-10 sm:w-12 sm:h-12 drop-shadow-lg" />
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-indigo-700 text-center flex-1">
            Soochna Mitra Dashboard
          </h1>
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={detectLocation}
            className="bg-emerald-600 hover:bg-emerald-700 text-white p-2 sm:p-3 rounded-full shadow-lg flex items-center justify-center"
            title="Detect My Location"
          >
            <MapPin size={22} />
          </motion.button>
        </div>
      </div>

      {/* Filters */}
      <div
        className={`${
          isMobile ? "flex flex-col items-center gap-3 w-full max-w-xs" : "flex flex-wrap justify-center gap-4"
        } mb-6`}
      >
        <select
          className="border rounded-lg p-2 w-56"
          value={selectedState}
          onChange={(e) => {
            setSelectedState(e.target.value);
            setSelectedDistrict("");
          }}
          disabled={loadingStates}
        >
          <option value="">{loadingStates ? "Loading states..." : "Select State"}</option>
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

      {/* Results */}
      {dashboardData && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="max-w-4xl w-full bg-white/80 p-6 mt-4 rounded-2xl shadow"
        >
          <h2 className="text-2xl font-semibold text-indigo-700 mb-4 text-center">
            {dashboardData.district}, {dashboardData.state}
          </h2>

          {/* KPI Cards */}
          <div ref={tooltipRef} className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6 relative">
            {kpiInfo.map((item, i) => (
              <div
                key={i}
                className={`relative p-4 rounded-xl bg-linear-to-br ${item.color} shadow text-center cursor-pointer`}
                onClick={() => setActiveTooltip(activeTooltip === i ? null : i)}
                onMouseEnter={() => setActiveTooltip(i)}
                onMouseLeave={() => setActiveTooltip(null)}
              >
                <div className="flex justify-center items-center gap-1 mb-1">
                  <h3 className="font-semibold text-gray-700">{item.label}</h3>
                  <Info size={16} className="text-gray-500" />
                </div>
                <p className="text-xl font-bold mt-1">{item.value}</p>

                {activeTooltip === i && (
                  <div className="absolute z-20 top-full left-1/2 -translate-x-1/2 mt-2 w-72 bg-white text-gray-800 border rounded-lg shadow-lg p-3 text-sm whitespace-pre-wrap">
                    {item.tooltip.en}
                    {"\n\n"}
                    {item.tooltip.hi}
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
                <RechartsTooltip />
                <Legend />
                <Bar dataKey="Expenditure" fill="#4f46e5" name="₹ Expenditure" />
                <Bar dataKey="Households" fill="#f59e0b" name="Families Worked" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Summary */}
          <p className="text-center text-gray-700 font-medium">{summary}</p>
        </motion.div>
      )}
    </motion.div>
  );
}