Soochna Mitra – MGNREGA Insights Dashboard

🧭 Overview :-
      Soochna Mitra is an interactive web application that helps citizens and officials visualize MGNREGA (Mahatma Gandhi National Rural Employment Guarantee Act) data for any state and district in India.
      
It provides a simple interface that highlights how government funds are being utilized showing total expenditure, families who worked, and person-days generated, with clear explanations and visual charts for better public understanding.

---

🎯 Objectives

  - Bridge the information gap between government data and citizens.
  - Present complex MGNREGA data in an accessible, meaningful, and visual format.
  - Ensure transparency and trust through real-time data updates and tooltips explaining key metrics in both languages.
  - Provide fallbacks and resilience, ensuring the app remains usable even if the primary API is unavailable.

---

💡 Key Features

✅ Auto Location Detection:
      Automatically detects user’s location (State & District) using the browser’s geolocation.
      
✅ Manual Selection Fallback:
      If location access fails (e.g., iOS/Apple users), dropdowns and a “Detect My Location” button allow manual access.
      
✅ Interactive Charts:
      Shows monthly MGNREGA expenditure trends for the selected district.

✅ Bilingual Tooltips:
      Each KPI card includes an easy-to-understand tooltip in English and Hindi.

✅ Resilient Data Handling:
    If APIs fail, the app uses cached data to ensure continuity.

✅ Responsive UI:
    Fully optimized for mobile, tablet, and desktop devices.

---

⚙️ Tech Stack

Frontend - React + Vite + TailwindCSS

Backend - FastAPI (Python)

Database - PostgreSQL

Caching - Redis

Hosting - Render (Backend), Vercel (Frontend)

APIs Used - Government Open Data APIs for MGNREGA

---

🧩 Installation (Local Setup)
1. Clone the repository -

      git clone https://github.com/your-username/soochna-mitra.git

      cd soochna-mitra

2. Setup Backend -
   
      cd backend

      pip install -r requirements.txt

      uvicorn app.main:app --reload

3. Setup Frontend - 
      cd frontend
      npm install
      npm run dev

4. Environment Variables -

      Create a .env file in backend/:

      DATABASE_URL=postgresql://postgres:postgres@localhost:5432/soochna_db

      REDIS_URL=redis://localhost:6379/0

      API_KEY=your_api_key_here

      DATASET_URL=https://data.gov.in/api/mgnrega


---

🚀 Hosting

Backend: Deployed on Render

Frontend: Hosted on Vercel

Uses HTTPS and CORS setup for secure API communication.


---

🔮 Future Advancements

  - Dockerization (soon):
      The entire stack (FastAPI, PostgreSQL, Redis, and Frontend) is Docker-ready and can be containerized for smoother deployment and scaling.

  - Accessibility Enhancements:
      Add voice-based data explanation for visually impaired users.

---

🌍 Impact Statement

Soochna Mitra isn’t just a data dashboard, it’s a step toward **transparent governance**.  
By visualizing how MGNREGA funds are used across districts, it empowers citizens with the clarity and awareness they deserve.  

---

If this project resonates with you or your organization, I’d love to connect and collaborate on similar **tech-for-social-good** initiatives.

**– Vijesh Krishna**
[Portfolio](https://vijeshkrishna.netlify.app) | [LinkedIn](https://www.linkedin.com/in/vijesh-krishna/) | [GitHub](https://github.com/Vijesh-Krishna)

