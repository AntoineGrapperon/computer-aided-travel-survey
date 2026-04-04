# Computer-Aided Travel Survey (CATS)

A Streamlit-based application designed to help cities conduct digital travel surveys, gathering essential data for urban planning and mobility analysis.

## 🚀 Overview
The Computer-Aided Travel Survey (CATS) provides an interactive, modern interface for citizens to report their daily travel habits. It streamlines data collection for city officials, offering real-time insights into origin-destination patterns, modal splits, and travel purposes.

## 🛠️ Tech Stack
- **Framework:** [Streamlit](https://streamlit.io/)
- **Data Handling:** [Pandas](https://pandas.pydata.org/)
- **Visualization:** [Pydeck](https://deckgl.readthedocs.io/en/latest/), [Plotly](https://plotly.com/python/)
- **Mapping:** OpenStreetMap (OSM) integration via [Streamlit components](https://streamlit.io/components)

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd computer-aided-travel-survey
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install streamlit pandas pydeck plotly
   ```

## 🚦 Usage

To start the application locally:
```bash
streamlit run app.py
```

## 📈 Key Features
- **Intuitive Trip Entry:** Simple multi-step forms for recording trips.
- **Interactive Mapping:** Drag-and-drop or search for origins and destinations on a map.
- **Real-time Validation:** Ensuring data consistency and accuracy at the point of entry.
- **Admin Dashboard:** Tools for visualizing and exporting aggregated survey results.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
