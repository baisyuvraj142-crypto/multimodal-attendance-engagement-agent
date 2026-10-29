import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

st.set_page_config(
    page_title="EduSense AI — Streamlit Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark/Modern Theme)
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        padding: 1.2rem;
        border-radius: 0.6rem;
        border: 1px solid #334155;
        margin-bottom: 1rem;
    }
    .metric-val {
        font-size: 2rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-lbl {
        color: #94a3b8;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-present {
        background-color: #065f46;
        color: #34d399;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-partial {
        background-color: #854d0e;
        color: #fde047;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🎓 EduSense AI")
st.sidebar.caption("Multimodal Classroom Intelligence Agent")
api_base = st.sidebar.text_input("Backend API URL", value="http://localhost:8000")

# Check Health
try:
    health_resp = requests.get(f"{api_base}/health", timeout=2)
    is_online = health_resp.status_code == 200
except Exception:
    is_online = False

if is_online:
    st.sidebar.success("● Backend Connected")
else:
    st.sidebar.error("○ Backend Disconnected (Ensure FastAPI is running)")

# Navigation
page = st.sidebar.radio("Navigation", ["Active Session Monitor", "Attendance Ledger", "Analytics & Reports", "Teacher Profile"])

# Fetch active or past sessions
sessions = []
if is_online:
    try:
        sess_resp = requests.get(f"{api_base}/api/sessions", timeout=2)
        if sess_resp.status_code == 200:
            sessions = sess_resp.json()
    except Exception:
        pass

session_options = {f"{s['title']} ({s['id']})": s['id'] for s in sessions}
selected_session_label = st.sidebar.selectbox(
    "Select Session",
    options=list(session_options.keys()) if session_options else ["No sessions found"]
)
current_session_id = session_options.get(selected_session_label)

# ----------------- PAGE 1: ACTIVE SESSION MONITOR -----------------
if page == "Active Session Monitor":
    st.title("Live Classroom Intelligence Monitor")
    st.write("Real-time multimodal fusion of visual attention, participant tracking, and acoustic dynamics.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-lbl">Students Present</div>
            <div class="metric-val">12 <span style="font-size: 1rem; color: #94a3b8;">/ 14</span></div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-lbl">Engagement Index</div>
            <div class="metric-val" style="color: #4ade80;">78.5%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-lbl">Acoustic Level</div>
            <div class="metric-val" style="color: #fbbf24;">-24.0 dB</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-lbl">Audio Mode</div>
            <div class="metric-val" style="color: #c084fc; font-size: 1.5rem;">Active Speech</div>
        </div>
        """, unsafe_allow_html=True)

    c_left, c_right = st.columns([3, 2])
    with c_left:
        st.subheader("Live Multi-Face Detection & Tracking View")
        st.info("Browser webcam frames and audio stream via WebSocket to backend vision and audio modules.")
        st.image("https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=800&q=80", caption="Video Stream with DeepSORT persistent ID overlays", use_container_width=True)

    with c_right:
        st.subheader("Real-Time Pedagogical Suggestions")
        st.warning("**[WARNING] Attention Drop Detected**: Engagement dipped in the back row. Consider prompting a student for a brief code review or thought summary.")
        st.success("**[INFO] High Interaction Peak**: Collaborative dialogue observed. Good timing to synthesize main formulas before moving to hands-on exercises.")
        st.info("**[ADVISORY] Micro-Lecture Notice**: Sustained 12-minute quiet segment. A 30-second poll will reactivate peer attention.")

# ----------------- PAGE 2: ATTENDANCE LEDGER -----------------
elif page == "Attendance Ledger":
    st.title("Presence-Based Attendance Ledger")
    st.write("Attendance is credited strictly via cumulative presence duration (configurable threshold >= 60s), resisting single-frame false positives.")

    if current_session_id and is_online:
        try:
            att_resp = requests.get(f"{api_base}/api/sessions/{current_session_id}/attendance")
            if att_resp.status_code == 200:
                data = att_resp.json().get("attendance", [])
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No participants tracked yet in this session.")
        except Exception as e:
            st.error(f"Error fetching attendance: {e}")
    else:
        # Demo preview table
        demo_data = [
            {"Participant": "Student_01", "Presence Duration": "142.4s", "First Seen": "14:02:10", "Last Seen": "14:18:25", "Attendance Status": "Present"},
            {"Participant": "Student_02", "Presence Duration": "135.0s", "First Seen": "14:02:11", "Last Seen": "14:18:20", "Attendance Status": "Present"},
            {"Participant": "Student_03", "Presence Duration": "24.5s", "First Seen": "14:05:00", "Last Seen": "14:07:30", "Attendance Status": "Partial"},
            {"Participant": "Student_04", "Presence Duration": "110.2s", "First Seen": "14:03:15", "Last Seen": "14:17:40", "Attendance Status": "Present"},
        ]
        st.dataframe(pd.DataFrame(demo_data), use_container_width=True)

# ----------------- PAGE 3: ANALYTICS & REPORTS -----------------
elif page == "Analytics & Reports":
    st.title("Multimodal Session Analytics & Student Summaries")

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if current_session_id:
            st.link_button("📥 Download PDF Report", f"{api_base}/api/sessions/{current_session_id}/report.pdf")
    with col_btn2:
        if current_session_id:
            st.link_button("📊 Export CSV Data", f"{api_base}/api/sessions/{current_session_id}/export.csv")

    st.subheader("Temporal Engagement Profile")
    chart_data = pd.DataFrame({
        "Minute": [f"14:{i:02d}" for i in range(10, 25)],
        "Visual Attention": [75, 78, 82, 85, 80, 62, 54, 70, 88, 92, 86, 79, 81, 84, 85],
        "Audio Noise (dB + 80)": [30, 32, 35, 48, 52, 28, 25, 45, 60, 58, 55, 38, 42, 44, 40],
        "Fused Engagement": [72, 75, 79, 81, 77, 58, 50, 68, 86, 89, 83, 76, 78, 81, 82]
    })
    st.line_chart(chart_data.set_index("Minute"))

    st.subheader("Reflective Student Session Summaries (Non-Punitive)")
    st.caption("Ethical compliance NFR-2: No grades, marks, or peer ranking.")
    
    st.markdown("""
    - **Student_01**: Demonstrates strong focus during algorithmic breakdowns; consistent visual presence noted throughout live coding.
    - **Student_02**: Steady attention observed across all lecture segments; active non-verbal engagement during group Q&A.
    - **Student_03**: Joined during key concept demonstrations; reviewing slide recap 4 will reinforce intermittent portions.
    """)

# ----------------- PAGE 4: TEACHER PROFILE -----------------
elif page == "Teacher Profile":
    st.title("Teacher Effectiveness & Historical Insights")
    st.write("Aggregated longitudinal metrics and pedagogical strengths benchmarked across sessions.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Teacher Effectiveness Score", "84.5 / 100", "+6.5% vs Dept Average")
    c2.metric("Total Sessions Conducted", "38")
    c3.metric("Avg Presence Retention", "91.2%")

    st.subheader("Identified Teaching Strengths")
    st.success("✔ **High Student Dialogue**: Sustains interactive discussion segments with low monologue fatigue.")
    st.success("✔ **Responsive Pacing**: Proactively adapts slide transitions following attention cues.")
    st.success("✔ **Consistent Engagement**: Demonstrates above-average retention in 60+ minute instructional blocks.")

    st.subheader("Actionable Growth Opportunities")
    st.info("💡 Schedule a 60-second comprehension check around minute 25 when passive listening naturally peaks.")
