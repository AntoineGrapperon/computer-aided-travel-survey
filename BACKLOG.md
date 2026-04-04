# 📋 Project Backlog: Computer-Aided Travel Survey (CATS)

This backlog outlines the planned features and improvements for the CATS application, categorized by development phases.

## 🚀 Phase 1: Minimum Viable Product (MVP)
- [ ] **Respondent Landing Page:** A welcoming interface explaining the survey's purpose.
- [ ] **Multi-step Trip Form:** Simple fields for time, mode (e.g., walk, bike, car, transit), and purpose (e.g., work, shop, social).
- [ ] **Origin/Destination Selection:** An interactive map (pydeck or leaflet) to pin or search for start and end locations.
- [ ] **Basic Validation:** Check for mandatory fields and logical travel times (departure < arrival).
- [ ] **Local Data Storage:** Mechanism to save responses to a local CSV or SQLite database for initial testing.

## 🛠️ Phase 2: Enhanced Data Collection & UI
- [ ] **Multi-trip Entries:** Ability for a user to log all trips taken within a single 24-hour period.
- [ ] **Demographic Information:** Optional section for age, gender, occupation, and household characteristics.
- [ ] **Mobile Optimization:** Refining the UI/UX for use on smartphones.
- [ ] **Auto-Geocoding:** Converting typed addresses to latitude/longitude coordinates automatically.
- [ ] **Advanced Validation:** Highlighting unrealistic speeds (e.g., walking 100km/h) or overlapping trips.

## 📊 Phase 3: Admin & Analytics Dashboard
- [ ] **Real-time Monitoring:** A secure dashboard for administrators to track response rates and demographics.
- [ ] **Origin-Destination (O-D) Matrices:** Tables and maps showing travel flows between different city zones.
- [ ] **Modal Split Visualization:** Pie charts and bar graphs detailing the share of each transport mode.
- [ ] **Heatmaps:** Visualizing popular travel corridors and time-of-day peaks.
- [ ] **Data Export:** Secure download of anonymized survey data in CSV, GeoJSON, and XLSX formats.

## 🌟 Phase 4: Advanced Features & Refinement
- [ ] **Multilingual Support:** Localizing the interface for diverse city populations.
- [ ] **Authentication:** Login systems for repeat respondents or authorized city officials.
- [ ] **Automated Routing:** Integration with OpenStreetMap (OSM) to estimate the most likely routes taken.
- [ ] **Public Transport Integration:** Linking reported transit trips with GTFS data for more granular analysis.
- [ ] **Offline Support:** Ability to cache survey entries when data connection is unavailable.
