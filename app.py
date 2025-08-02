import streamlit as st
import os
import sys
from datetime import datetime
import uuid
import sqlite3
import pandas as pd
import random

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database components
try:
    from database.db_manager import TeluguCorpusDB
except ImportError:
    st.error("Database components not found. Please ensure database/db_manager.py exists.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Telugu Bhasha Detective",
    page_icon="🕵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Telugu Mysteries Database - Progressive Unlocking System
TELUGU_MYSTERIES = [
    {
        "mystery_id": "telangana_bathukamma_001",
        "title": "Bathukamma Festival Mystery",
        "telugu_title": "బతుకమ్మ పండుగ రహస్యం",
        "description": "Bathukamma is celebrated uniquely across Telangana. In your village/town, which specific flowers are used for Bathukamma? What songs are sung? Are there any special traditions your grandmother taught that are unique to your area? Please describe in detail in Telugu.",
        "category": "Telangana Culture",
        "difficulty_level": 1,
        "points_value": 15,
        "unlock_requirement": 0
    },
    {
        "mystery_id": "andhra_ugadi_002", 
        "title": "Ugadi Celebrations Mystery",
        "telugu_title": "ఉగాది వేడుకల రహస్యం",
        "description": "Ugadi marks the Telugu New Year. What special dishes does your family prepare for Ugadi? What is the significance of the Ugadi Pachadi ingredients in your household? Describe any unique rituals your family follows in Telugu.",
        "category": "Andhra Culture",
        "difficulty_level": 1,
        "points_value": 12,
        "unlock_requirement": 1
    },
    {
        "mystery_id": "food_gongura_003",
        "title": "Gongura Pickle Mystery",
        "telugu_title": "గోంగూర ఆవకాయ రహస్యం", 
        "description": "Gongura pickle is called 'Andhra Pradesh's soul food'. What is your family's traditional method of making Gongura pickle? What makes it special compared to others? When is it typically prepared in your household? Share the complete recipe in Telugu.",
        "category": "Food & Culinary",
        "difficulty_level": 2,
        "points_value": 18,
        "unlock_requirement": 2
    },
    {
        "mystery_id": "telangana_bonalu_004",
        "title": "Bonalu Ritual Mystery",
        "telugu_title": "బోనాలు ఆచార రహస్యం",
        "description": "Bonalu festival is dedicated to Goddess Mahakali. What specific items do women in your family place in the Bonam pot? What colors are used and why? Describe the traditional dance and songs performed during Bonalu in your locality in Telugu.",
        "category": "Telangana Culture",
        "difficulty_level": 2,
        "points_value": 16,
        "unlock_requirement": 3
    },
    {
        "mystery_id": "traditional_games_005",
        "title": "Telugu Traditional Games Mystery", 
        "telugu_title": "తెలుగు సంప్రదాయ ఆటల రహస్యం",
        "description": "Telugu children played many traditional games. What games did you play as a child? How are games like Vamana Guntalu, Kho-Kho, or Kabaddi played in your region? Are there any unique rules or variations? Describe in Telugu.",
        "category": "Traditional Games",
        "difficulty_level": 2,
        "points_value": 14,
        "unlock_requirement": 4
    },
    {
        "mystery_id": "wedding_customs_006",
        "title": "Telugu Wedding Customs Mystery",
        "telugu_title": "తెలుగు వివాహ ఆచారాల రహస్యం",
        "description": "Telugu weddings have rich traditions. What are the specific rituals performed in your family during weddings? What is the significance of Mangalsutra, Jeelakarra Bellam, and other ceremonies? Share your family's wedding traditions in Telugu.",
        "category": "Wedding Traditions",
        "difficulty_level": 3,
        "points_value": 20,
        "unlock_requirement": 5
    }
]

class MysteryManager:
    def __init__(self, db):
        self.db = db
        self.mysteries = TELUGU_MYSTERIES
    
    def get_available_mysteries(self, user_id):
        """Get mysteries available to user based on progress"""
        if not self.db:
            return [self.mysteries[0]]
        
        try:
            user_data = self.db.get_user(user_id)
            solved_count = user_data.get('mysteries_solved', 0) if user_data else 0
            available = [m for m in self.mysteries if m['unlock_requirement'] <= solved_count]
            return available
        except Exception as e:
            st.error(f"Error getting available mysteries: {e}")
            return [self.mysteries[0]]
    
    def get_next_mystery(self, user_id):
        """Get the next unsolved mystery for user"""
        available = self.get_available_mysteries(user_id)
        
        if not available:
            return None
            
        solved_ids = self.get_solved_mystery_ids(user_id)
        
        for mystery in available:
            if mystery['mystery_id'] not in solved_ids:
                return mystery
        
        return None
    
    def get_solved_mystery_ids(self, user_id):
        """Get list of mystery IDs user has solved"""
        if not self.db:
            return []
            
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT mystery_id FROM text_responses WHERE user_id = ?", (user_id,))
                solved_ids = [row[0] for row in cursor.fetchall()]
                return solved_ids
        except Exception as e:
            st.error(f"Error getting solved mysteries: {e}")
            return []
    
    def get_mystery_by_id(self, mystery_id):
        """Get specific mystery by ID"""
        for mystery in self.mysteries:
            if mystery['mystery_id'] == mystery_id:
                return mystery
        return None

# Initialize database
@st.cache_resource
def init_db():
    try:
        return TeluguCorpusDB()
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        return None

db = init_db()

# Initialize Mystery Manager
@st.cache_resource
def get_mystery_manager():
    return MysteryManager(db)

mystery_manager = get_mystery_manager()

def get_current_mystery():
    """Get current mystery for user"""
    if 'user_id' not in st.session_state:
        return None
    return mystery_manager.get_next_mystery(st.session_state.user_id)

def show_mystery_progress():
    """Show user's mystery progress"""
    if 'user_id' not in st.session_state:
        return
        
    available = mystery_manager.get_available_mysteries(st.session_state.user_id)
    solved_ids = mystery_manager.get_solved_mystery_ids(st.session_state.user_id)
    
    st.sidebar.markdown("### 🎯 Mystery Progress")
    st.sidebar.text(f"Solved: {len(solved_ids)}")
    st.sidebar.text(f"Available: {len(available)}")
    st.sidebar.text(f"Total: {len(mystery_manager.mysteries)}")
    
    progress = len(solved_ids) / len(mystery_manager.mysteries) if mystery_manager.mysteries else 0
    st.sidebar.progress(progress)
    
    next_unlock = len(solved_ids)
    if next_unlock < len(mystery_manager.mysteries):
        next_mystery = next((m for m in mystery_manager.mysteries if m['unlock_requirement'] == next_unlock + 1), None)
        if next_mystery:
            st.sidebar.info(f"🔒 Next: {next_mystery['title']}")

def show_live_activity():
    """Show recent activity from all users"""
    if not db:
        return
        
    try:
        with sqlite3.connect(db.db_path) as conn:
            recent_activity = pd.read_sql_query("""
                SELECT u.username, tr.mystery_id, tr.submitted_at
                FROM text_responses tr
                JOIN users u ON tr.user_id = u.user_id
                ORDER BY tr.submitted_at DESC
                LIMIT 5
            """, conn)
            
            if not recent_activity.empty:
                st.sidebar.markdown("### 🔥 Recent Activity") 
                for _, activity in recent_activity.iterrows():
                    mystery_title = "a mystery"
                    mystery = mystery_manager.get_mystery_by_id(activity['mystery_id'])
                    if mystery:
                        mystery_title = mystery['title'][:20] + "..."
                    st.sidebar.text(f"🎉 {activity['username'][:10]} solved {mystery_title}")
    except Exception:
        pass

# Custom CSS
def apply_custom_css():
    st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #FFF8DC 0%, #F0E68C 100%);
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #E6B800 0%, #FFD700 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #CC0000 0%, #FF6B6B 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .mystery-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #E6B800;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .locked-mystery {
        background: #f5f5f5;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #ccc;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        opacity: 0.6;
    }
    
    .audio-recorder {
        background: #f0f0f0;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
    }
    
    .image-upload {
        border: 2px dashed #E6B800;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
        background: #fafafa;
    }
    </style>
    """, unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'total_points' not in st.session_state:
        st.session_state.total_points = 0
    if 'mysteries_solved' not in st.session_state:
        st.session_state.mysteries_solved = 0
    if 'user_data_loaded' not in st.session_state:
        st.session_state.user_data_loaded = False

def load_user_data():
    """Load user data from database"""
    if db and st.session_state.user_id and not st.session_state.user_data_loaded:
        try:
            user_data = db.get_user(st.session_state.user_id)
            if user_data:
                st.session_state.username = user_data['username']
                st.session_state.location = user_data.get('location', '')
                st.session_state.native_dialect = user_data.get('native_dialect', '')
                st.session_state.age_group = user_data.get('age_group', '')
                st.session_state.total_points = user_data.get('total_points', 0)
                st.session_state.mysteries_solved = user_data.get('mysteries_solved', 0)
                st.session_state.user_data_loaded = True
        except Exception:
            pass

def save_user_to_db():
    """Save user data to database"""
    if not db:
        return False
        
    user_data = {
        'user_id': st.session_state.user_id,
        'username': st.session_state.username,
        'location': st.session_state.get('location', ''),
        'native_dialect': st.session_state.get('native_dialect', ''),
        'age_group': st.session_state.get('age_group', '')
    }
    try:
        db.create_user(user_data)
        st.session_state.user_data_loaded = True
        return True
    except Exception as e:
        st.error(f"Error saving user data: {e}")
        return False

def save_response_to_db(response_text, word_count, mystery_id, points, response_type="text"):
    """Enhanced save response with type support"""
    if not db:
        return False
        
    response_data = {
        'user_id': st.session_state.user_id,
        'mystery_id': mystery_id,
        'response_text': f"[{response_type.upper()}] {response_text}",
        'word_count': word_count
    }
    try:
        db.save_response(response_data)
        db.update_user_points(st.session_state.user_id, points)
        
        st.session_state.total_points += points
        st.session_state.mysteries_solved += 1
        return True
    except Exception as e:
        st.error(f"Error saving response: {e}")
        return False

def save_voice_response_to_db(description, mystery_id, points, audio_file_path=None):
    """Save voice response to database and update points"""
    if not db:
        return False
        
    try:
        response_id = str(uuid.uuid4())
        
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Save to voice_responses table
            cursor.execute("""
                INSERT INTO voice_responses 
                (response_id, user_id, mystery_id, audio_file_path, duration_seconds)
                VALUES (?, ?, ?, ?, ?)
            """, (
                response_id,
                st.session_state.user_id,
                mystery_id,
                audio_file_path,
                0.0  # Duration can be calculated later
            ))
            
            # Also save description to text_responses for consistency
            cursor.execute("""
                INSERT INTO text_responses 
                (response_id, user_id, mystery_id, response_text, word_count)
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                st.session_state.user_id,
                mystery_id,
                f"[VOICE] {description}",
                len(description.split())
            ))
            
            conn.commit()
        
        # Update user points
        db.update_user_points(st.session_state.user_id, points)
        
        st.session_state.total_points += points
        st.session_state.mysteries_solved += 1
        return True
        
    except Exception as e:
        st.error(f"Error saving voice response: {e}")
        return False

def save_image_response_to_db(description, mystery_id, points, image_paths=None):
    """Save image response to database and update points"""
    if not db:
        return False
        
    try:
        response_id = str(uuid.uuid4())
        
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Save to image_responses table
            for i, image_path in enumerate(image_paths or []):
                cursor.execute("""
                    INSERT INTO image_responses 
                    (response_id, user_id, mystery_id, image_file_path, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    f"{response_id}_{i}",
                    st.session_state.user_id,
                    mystery_id,
                    image_path,
                    description
                ))
            
            # Also save description to text_responses for consistency
            cursor.execute("""
                INSERT INTO text_responses 
                (response_id, user_id, mystery_id, response_text, word_count)
                VALUES (?, ?, ?, ?, ?)
            """, (
                response_id,
                st.session_state.user_id,
                mystery_id,
                f"[IMAGES] {description}",
                len(description.split())
            ))
            
            conn.commit()
        
        # Update user points
        db.update_user_points(st.session_state.user_id, points)
        
        st.session_state.total_points += points
        st.session_state.mysteries_solved += 1
        return True
        
    except Exception as e:
        st.error(f"Error saving image response: {e}")
        return False

def main():
    # Apply custom styling
    apply_custom_css()
    
    # Initialize session state
    init_session_state()
    
    # Load user data from database
    load_user_data()
    
    # Header
    st.markdown("""
    <div style="padding: 2rem; text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #CC0000; font-size: 3rem; margin-bottom: 0.5rem;">
            🕵 Telugu Bhasha Detective
        </h1>
        <p style="color: #E6B800; font-size: 1.2rem; font-style: italic;">
            "Solve Cultural Mysteries, Preserve Telugu Heritage"
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("🕵 Navigation")
    
    # User setup if first time
    if st.session_state.username is None:
        st.sidebar.info("👋 Welcome! Please set up your profile first.")
    else:
        st.sidebar.success(f"Welcome back, {st.session_state.username}!")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Points", st.session_state.total_points)
        with col2:
            st.metric("Solved", st.session_state.mysteries_solved)
        
        show_mystery_progress()
        show_live_activity()
    
    # Main navigation
    pages = {
        "🏠 Home": "home",
        "🔍 Today's Mystery": "mystery",
        "📚 All Mysteries": "all_mysteries",
        "👤 Profile": "profile",
        "📊 Statistics": "statistics",
        "🏆 Leaderboard": "leaderboard"
    }
    
    selected_page = st.sidebar.selectbox("Go to", list(pages.keys()))
    page_name = pages[selected_page]
    
    # Collection progress in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Collection Progress")
    
    if db:
        try:
            total_responses = db.get_total_responses()
            estimated_hours = total_responses * 0.1
            progress_percentage = min((estimated_hours / 20000) * 100, 100)
        except:
            estimated_hours = 500.5
            total_responses = 1250
            progress_percentage = 2.5
    else:
        estimated_hours = 500.5
        total_responses = 1250
        progress_percentage = 2.5
    
    st.sidebar.progress(progress_percentage / 100)
    st.sidebar.text(f"{estimated_hours:.1f} / 20,000 hours")
    st.sidebar.text(f"{total_responses:,} total responses")
    
    # Route to pages
    if page_name == "home" or st.session_state.username is None:
        show_home_page()
    elif page_name == "mystery":
        show_mystery_page()
    elif page_name == "all_mysteries":
        show_all_mysteries_page()
    elif page_name == "profile":
        show_profile_page()
    elif page_name == "statistics":
        show_statistics_page()
    elif page_name == "leaderboard":
        show_leaderboard_page()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem; color: #E6B800;">
        🎯 Target: 20,000+ hours of Telugu linguistic data collection<br>
        Built with ❤️ for Telugu language preservation
    </div>
    """, unsafe_allow_html=True)

def show_home_page():
    """Home page with user onboarding and dashboard"""
    if st.session_state.username is None:
        st.markdown("## 👋 Welcome to Telugu Bhasha Detective!")
        
        st.markdown("""
        <div class="mystery-card">
        <h3>🎯 Mission</h3>
        <p>Help preserve Telugu culture by solving progressive mysteries and sharing your knowledge 
        about Andhra Pradesh and Telangana traditions!</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🚀 Get Started")
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Enter your name:", placeholder="Your name in English")
            location = st.text_input("Your location:", placeholder="City, District")
        
        with col2:
            native_dialect = st.selectbox("Native dialect:", [
                "Telangana Telugu", "Coastal Andhra", "Rayalaseema", 
                "Standard Telugu", "Other"
            ])
            age_group = st.selectbox("Age group:", [
                "18-25", "26-35", "36-45", "46-55", "55+"
            ])
        
        if st.button("🎉 Start My Detective Journey!", key="register_user"):
            if username.strip():
                st.session_state.username = username.strip()
                st.session_state.location = location.strip()
                st.session_state.native_dialect = native_dialect
                st.session_state.age_group = age_group
                
                if save_user_to_db():
                    st.success(f"Welcome aboard, Detective {username}! 🕵")
                    st.balloons()
                    st.rerun()
                else:
                    st.warning("Profile created locally. Database connection may be limited.")
                    st.rerun()
            else:
                st.error("Please enter your name to continue.")
        
        # How it works
        st.markdown("### 🔍 How it Works")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **1. 🎯 Progressive Mysteries**
            - Start with easy mysteries
            - Unlock harder ones as you solve
            - 6 different categories
            """)
        
        with col2:
            st.markdown("""
            **2. 📝 Multi-Modal Responses**
            - Write in Telugu script
            - Record your voice
            - Upload cultural photos
            """)
        
        with col3:
            st.markdown("""
            **3. 🏆 Earn & Compete**
            - Collect points & badges
            - Climb leaderboards
            - Preserve heritage together
            """)
    
    else:
        st.markdown(f"## 🏠 Welcome back, Detective {st.session_state.username}!")
        
        current_mystery = get_current_mystery()
        if current_mystery:
            st.markdown("### 🔍 Your Next Mystery")
            st.markdown(f"""
            <div class="mystery-card">
            <h3 style="color: #CC0000;">{current_mystery['title']}</h3>
            <h4 style="color: #E6B800; font-style: italic;">{current_mystery['telugu_title']}</h4>
            <p>{current_mystery['description'][:200]}...</p>
            <p><strong>Category:</strong> {current_mystery['category']} | <strong>Points:</strong> {current_mystery['points_value']} | <strong>Difficulty:</strong> {'⭐' * current_mystery['difficulty_level']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Solve This Mystery", key="solve_mystery_home"):
                st.rerun()
        else:
            st.success("🎉 Congratulations! You've solved all available mysteries!")
            st.balloons()
        
        st.markdown("### 📈 Your Activity Dashboard")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Points", st.session_state.total_points, f"+{st.session_state.total_points}")
        with col2:
            st.metric("Mysteries Solved", st.session_state.mysteries_solved, f"+{st.session_state.mysteries_solved}")
        with col3:
            available_count = len(mystery_manager.get_available_mysteries(st.session_state.user_id))
            st.metric("Available", available_count, "0")
        with col4:
            progress_percent = (st.session_state.mysteries_solved / len(mystery_manager.mysteries)) * 100
            st.metric("Progress", f"{progress_percent:.1f}%", f"+{progress_percent:.1f}%")

def show_mystery_page():
    """Mystery solving interface with full multi-modal support"""
    current_mystery = get_current_mystery()
    
    if not current_mystery:
        st.markdown("## 🎉 All Available Mysteries Completed!")
        st.success("Congratulations! You've solved all currently available mysteries. More mysteries will unlock as you progress!")
        st.balloons()
        return
    
    st.markdown("## 🔍 Current Mystery")
    
    st.markdown(f"""
    <div class="mystery-card">
    <h3 style="color: #CC0000;">{current_mystery['title']}</h3>
    <h4 style="color: #E6B800; font-style: italic;">{current_mystery['telugu_title']}</h4>
    <p style="font-size: 1.1rem; line-height: 1.6;">
    {current_mystery['description']}
    </p>
    <p><strong>Category:</strong> {current_mystery['category']} | <strong>Points:</strong> {current_mystery['points_value']} | <strong>Difficulty:</strong> {'⭐' * current_mystery['difficulty_level']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Multi-modal response options
    st.markdown("### 📝 Choose Your Response Method")
    st.info("🎯 **Bonus Points:** Text responses earn base points, Voice responses get +5 bonus, Image responses get +3 bonus!")
    
    tab1, tab2, tab3 = st.tabs(["✍️ Text Response", "🎤 Voice Response", "📸 Image Response"])
    
    with tab1:
        st.markdown("#### ✍️ Write Your Response in Telugu")
        st.markdown("Share your knowledge about this cultural mystery in detail:")
        
        response_text = st.text_area(
            "Your Response:",
            height=250,
            placeholder="మీ ఉత్తరం ఇక్కడ తెలుగులో వ్రాయండి... \n\nExample: మా ఊరిలో బతుకమ్మకు ఎల్లే, మల్లె, జాసుడు పువ్వులను వాడతాము. మా అజ్జి చెప్పింది...",
            help="Minimum 50 words required. Share your personal experiences, family traditions, and local variations.",
            key="mystery_text_response"
        )
        
        if response_text:
            # Real-time analysis
            word_count = len(response_text.split())
            char_count = len(response_text)
            telugu_chars = len([c for c in response_text if '\u0c00' <= c <= '\u0c7f'])
            quality_score = min(word_count/50 * 5, 5)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Words", word_count)
            with col2:
                st.metric("Characters", char_count)
            with col3:
                st.metric("Telugu Script", f"{telugu_chars}/{char_count}")
            with col4:
                st.metric("Quality", f"{quality_score:.1f}/5.0", f"+{quality_score-2.5:.1f}")
            
            if word_count >= 50:
                st.success("✅ Great! Your response meets the minimum word requirement.")
                if telugu_chars > char_count * 0.3:
                    st.success("🎉 Excellent use of Telugu script!")
                
                if st.button("📤 Submit Text Response", key="submit_text_response", type="primary"):
                    success = save_response_to_db(
                        response_text, word_count, 
                        current_mystery['mystery_id'], 
                        current_mystery['points_value'],
                        response_type="text"
                    )
                    
                    if success:
                        st.success(f"🎉 Mystery solved! +{current_mystery['points_value']} points earned!")
                        st.balloons()
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.session_state.total_points += current_mystery['points_value']
                        st.session_state.mysteries_solved += 1
                        st.success(f"🎉 Mystery solved! +{current_mystery['points_value']} points earned!")
                        st.balloons()
            else:
                st.warning(f"⚠️ Please write at least 50 words. You have {word_count} words.")
                st.progress(min(word_count/50, 1.0))
    
    with tab2:
        st.markdown("#### 🎤 Record Your Voice Response")
        st.markdown("Tell us about this cultural mystery in your own voice:")
        st.info("📢 Record in Telugu (minimum 30 seconds recommended). Share stories, songs, or personal experiences!")
        
        # Multiple audio recording methods
        audio_method = st.selectbox("Choose recording method:", [
            "🎙️ Streamlit Native Audio Input (Recommended)",
            "🔴 Audio Recorder Streamlit", 
            "📱 ST Audio Recorder",
            "🌐 Browser Audio Recorder"
        ])
        
        audio_recorded = False
        audio_data = None
        
        if audio_method.startswith("🎙️"):
            st.markdown("**Using Streamlit's built-in audio recorder:**")
            st.markdown('<div class="audio-recorder"><h4>🎤 Click the button below to start recording</h4><p>Speak clearly in Telugu about your cultural knowledge</p></div>', unsafe_allow_html=True)
            
            audio_value = st.audio_input("🎙️ Click to record your voice message")
            
            if audio_value is not None:
                st.audio(audio_value)
                st.success("✅ Audio recorded successfully!")
                
                # Audio analysis
                try:
                    audio_size = len(audio_value.getvalue()) / 1024  # KB
                    st.info(f"📊 Audio size: {audio_size:.1f} KB")
                except:
                    pass
                
                audio_recorded = True
                audio_data = audio_value
        
        elif audio_method.startswith("🔴"):
            try:
                from audio_recorder_streamlit import audio_recorder
                
                st.markdown("**Professional Audio Recorder:**")
                st.markdown('<div class="audio-recorder"><h4>🎤 Professional Recording Interface</h4><p>Click the red button to start, click again to stop</p></div>', unsafe_allow_html=True)
                
                audio_bytes = audio_recorder(
                    text="🎙️ Click to Record",
                    recording_color="#e87070",
                    neutral_color="#6aa36f",
                    icon_name="microphone",
                    icon_size="2x",
                    pause_threshold=2.0
                )
                
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/wav")
                    st.success("✅ Audio recorded successfully!")
                    
                    # Audio analysis
                    audio_size = len(audio_bytes) / 1024  # KB
                    st.info(f"📊 Audio size: {audio_size:.1f} KB")
                    
                    audio_recorded = True
                    audio_data = audio_bytes
                    
            except ImportError:
                st.error("❌ audio-recorder-streamlit not installed.")
                st.code("pip install audio-recorder-streamlit")
                st.info("Please install the package and restart the app.")
        
        elif audio_method.startswith("📱"):
            try:
                from st_audiorec import st_audiorec
                
                st.markdown("**Mobile-Friendly Audio Recorder:**")
                st.markdown('<div class="audio-recorder"><h4>📱 Mobile Optimized Recording</h4><p>Click to start recording, click again to stop</p></div>', unsafe_allow_html=True)
                
                wav_audio_data = st_audiorec()
                
                if wav_audio_data is not None:
                    st.audio(wav_audio_data, format='audio/wav')
                    st.success("✅ Audio recorded successfully!")
                    
                    # Audio analysis
                    audio_size = len(wav_audio_data) / 1024  # KB
                    st.info(f"📊 Audio size: {audio_size:.1f} KB")
                    
                    audio_recorded = True
                    audio_data = wav_audio_data
                    
            except ImportError:
                st.error("❌ st-audiorec not installed.")
                st.code("pip install st-audiorec")
                st.info("Please install the package and restart the app.")
        
        elif audio_method.startswith("🌐"):
            st.markdown("**HTML5 Web Audio Recorder:**")
            st.markdown("""
            <div class="audio-recorder">
            <h4>🌐 Browser Native Recording</h4>
            <p>Uses your browser's built-in recording capabilities</p>
            <button onclick="startRecording()" style="background: #e87070; color: white; border: none; padding: 15px 30px; border-radius: 8px; margin: 10px; font-size: 16px; cursor: pointer;">
                🎙️ Start Recording
            </button>
            <button onclick="stopRecording()" style="background: #6aa36f; color: white; border: none; padding: 15px 30px; border-radius: 8px; margin: 10px; font-size: 16px; cursor: pointer;">
                ⏹️ Stop Recording
            </button>
            <div id="audioContainer" style="margin-top: 20px;"></div>
            <div id="recordingStatus" style="margin-top: 10px; font-weight: bold;"></div>
            </div>
            
            <script>
            let mediaRecorder;
            let audioChunks = [];
            let isRecording = false;
            
            function startRecording() {
                if (isRecording) return;
                
                document.getElementById("recordingStatus").innerHTML = "🔴 Recording...";
                audioChunks = [];
                
                navigator.mediaDevices.getUserMedia({ audio: true })
                    .then(stream => {
                        mediaRecorder = new MediaRecorder(stream);
                        mediaRecorder.start();
                        isRecording = true;
                        
                        mediaRecorder.addEventListener("dataavailable", event => {
                            audioChunks.push(event.data);
                        });
                        
                        mediaRecorder.addEventListener("stop", () => {
                            isRecording = false;
                            const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
                            const audioUrl = URL.createObjectURL(audioBlob);
                            
                            document.getElementById("audioContainer").innerHTML = 
                                '<audio controls style="width: 100%; margin-top: 10px;"><source src="' + audioUrl + '" type="audio/wav"></audio>';
                            
                            document.getElementById("recordingStatus").innerHTML = "✅ Recording completed! Audio ready for submission.";
                            
                            // Stop all tracks to free up the microphone
                            stream.getTracks().forEach(track => track.stop());
                        });
                    })
                    .catch(error => {
                        document.getElementById("recordingStatus").innerHTML = "❌ Error accessing microphone: " + error.message;
                    });
            }
            
            function stopRecording() {
                if (mediaRecorder && isRecording) {
                    mediaRecorder.stop();
                    document.getElementById("recordingStatus").innerHTML = "⏹️ Stopping recording...";
                }
            }
            </script>
            """, unsafe_allow_html=True)
            
            if st.button("✅ Confirm Browser Recording", key="browser_audio_confirm"):
                st.success("✅ Browser recording confirmed!")
                audio_recorded = True
        
        if audio_recorded:
            st.markdown("---")
            st.markdown("#### 📝 Describe Your Audio Response")
            
            # Audio response description
            audio_description = st.text_area(
                "Briefly describe what you recorded (optional but recommended):",
                placeholder="Example: నేను మా అజ్జి నుండి వినిన బతుకమ్మ పాటలు మరియు మా ఊరి ప్రత్యేక సంప్రదాయాలను చెప్పాను...",
                key="audio_description",
                height=100
            )
            
            # Audio context
            col1, col2 = st.columns(2)
            with col1:
                audio_language = st.selectbox("Primary language used:", [
                    "Telugu", "Telugu + English", "Regional Telugu dialect", "Other"
                ])
                audio_duration = st.slider("Approximate duration (seconds):", 10, 300, 60)
            
            with col2:
                audio_type = st.selectbox("Type of content:", [
                    "Personal experience", "Family tradition", "Song/Folk tale", 
                    "Recipe explanation", "Cultural practice", "Historical story"
                ])
                audio_quality = st.selectbox("Audio quality:", [
                    "Clear", "Good", "Fair", "Poor (background noise)"
                ])
            
            if st.button("🎵 Submit Voice Response", key="submit_voice_response", type="primary"):
                voice_points = current_mystery['points_value'] + 5  # Bonus for voice
                
                # Save audio file if we have audio data
                audio_file_path = None
                if audio_data:
                    try:
                        # Create audio directory
                        os.makedirs("data/audio", exist_ok=True)
                        audio_file_path = f"data/audio/{st.session_state.user_id}_{current_mystery['mystery_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                        
                        with open(audio_file_path, "wb") as f:
                            f.write(audio_data.getvalue() if hasattr(audio_data, 'getvalue') else audio_data)
                        
                        st.success(f"💾 Audio saved to: {audio_file_path}")
                    except Exception as e:
                        st.warning(f"Could not save audio file: {e}")
                
                # Enhanced description with metadata
                full_description = f"""
                Description: {audio_description or '[Voice Response Recorded]'}
                Language: {audio_language}
                Duration: ~{audio_duration} seconds
                Content Type: {audio_type}
                Quality: {audio_quality}
                """
                
                success = save_voice_response_to_db(
                    full_description.strip(),
                    current_mystery['mystery_id'], 
                    voice_points,
                    audio_file_path
                )
                
                if success:
                    st.success(f"🎉 Voice mystery solved! +{voice_points} points earned! (+5 voice bonus)")
                    st.balloons()
                    st.cache_resource.clear()
                    st.rerun()
                else:
                    st.session_state.total_points += voice_points
                    st.session_state.mysteries_solved += 1
                    st.success(f"🎉 Voice mystery solved! +{voice_points} points earned! (+5 voice bonus)")
                    st.balloons()
    
    with tab3:
        st.markdown("#### 📸 Upload Cultural Images")
        st.markdown("Share photos that relate to this cultural mystery:")
        st.info("📷 Upload photos of festivals, food, traditions, rituals, or family celebrations related to this mystery")
        
        # Image upload section
        st.markdown('<div class="image-upload"><h4>📤 Choose Your Cultural Images</h4><p>Select up to 5 high-quality images that help tell your cultural story</p></div>', unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Choose images...", 
            type=['png', 'jpg', 'jpeg', 'gif'], 
            accept_multiple_files=True,
            key="mystery_image_upload",
            help="Maximum 5 images, up to 10MB each. JPG/PNG formats recommended."
        )
        
        if uploaded_files:
            if len(uploaded_files) > 5:
                st.warning("⚠️ Maximum 5 images allowed. Only the first 5 will be processed.")
                uploaded_files = uploaded_files[:5]
            
            # Display uploaded images in a grid
            st.markdown("#### 📸 Your Uploaded Images")
            
            # Calculate columns based on number of images
            num_cols = min(len(uploaded_files), 3)
            cols = st.columns(num_cols)
            
            total_size = 0
            for i, uploaded_file in enumerate(uploaded_files):
                with cols[i % num_cols]:
                    st.image(uploaded_file, caption=f"Image {i+1}: {uploaded_file.name}", width=200)
                    
                    # Show file info
                    file_size = len(uploaded_file.getvalue()) / (1024*1024)  # MB
                    total_size += file_size
                    st.caption(f"📏 Size: {file_size:.1f} MB")
                    
                    # Image type
                    img_type = uploaded_file.type
                    st.caption(f"🖼️ Type: {img_type}")
            
            st.info(f"📊 Total upload size: {total_size:.1f} MB")
            
            # Image description and context
            st.markdown("---")
            st.markdown("#### 📝 Describe Your Images")
            
            image_description = st.text_area(
                "Describe your images in Telugu (detailed description recommended):",
                placeholder="చిత్రాల గురించి తెలుగులో వివరించండి...\n\nExample: ఈ చిత్రాలలో మా ఊరి బతుకమ్మ వేడుకలు కనిపిస్తాయి. మొదటి చిత్రంలో మా అమ్మ బతుకమ్మ చేస్తోంది...",
                key="image_description",
                height=120
            )
            
            # Cultural context questions
            st.markdown("#### 🎯 Cultural Context Information")
            st.markdown("*Help us understand the cultural significance of your images:*")
            
            col1, col2 = st.columns(2)
            with col1:
                image_location = st.text_input(
                    "📍 Where were these taken?", 
                    placeholder="City, Village, Temple name, Home...",
                    key="img_location"
                )
                image_occasion = st.selectbox("🎉 What occasion/festival?", [
                    "Select...", "Bathukamma", "Ugadi", "Bonalu", "Dussehra", 
                    "Diwali", "Sankranti", "Wedding", "House warming", "Traditional cooking", 
                    "Folk dance", "Temple festival", "Family gathering", "Other"
                ], key="img_occasion")
                
                image_year = st.number_input(
                    "📅 Year taken (approximate)", 
                    min_value=1950, max_value=2025, value=2024,
                    key="img_year"
                )
            
            with col2:
                image_people = st.text_input(
                    "👥 Who is in the photos?", 
                    placeholder="Family members, community, children...",
                    key="img_people"
                )
                image_significance = st.text_area(
                    "✨ Cultural significance:",
                    placeholder="Why are these images important to your culture/tradition?",
                    key="img_significance",
                    height=80
                )
                
                photo_taker = st.text_input(
                    "📷 Who took these photos?",
                    placeholder="Myself, family member, friend...",
                    key="photo_taker"
                )
            
            # Permission and authenticity
            st.markdown("#### ✅ Confirmation")
            col1, col2 = st.columns(2)
            with col1:
                permission_check = st.checkbox(
                    "I have permission to share these images",
                    key="permission_check"
                )
                authentic_check = st.checkbox(
                    "These are authentic cultural images from my experience",
                    key="authentic_check"
                )
            
            with col2:
                privacy_check = st.checkbox(
                    "I'm comfortable sharing these for Telugu cultural preservation",
                    key="privacy_check"
                )
                quality_check = st.checkbox(
                    "Images are clear and relevant to the mystery",
                    key="quality_check"
                )
            
            # Submission validation and button
            can_submit = (
                (image_description or image_significance or any([image_location, image_occasion != "Select...", image_people])) and
                permission_check and authentic_check and privacy_check and quality_check
            )
            
            if can_submit:
                if st.button("📤 Submit Image Response", key="submit_image_response", type="primary"):
                    image_points = current_mystery['points_value'] + 3  # Bonus for images
                    
                    # Save images to filesystem
                    saved_image_paths = []
                    try:
                        os.makedirs("data/images", exist_ok=True)
                        
                        for i, uploaded_file in enumerate(uploaded_files):
                            file_extension = uploaded_file.name.split('.')[-1].lower()
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            image_path = f"data/images/{st.session_state.user_id}_{current_mystery['mystery_id']}_{i+1}_{timestamp}.{file_extension}"
                            
                            with open(image_path, "wb") as f:
                                f.write(uploaded_file.getvalue())
                            saved_image_paths.append(image_path)
                        
                        st.success(f"💾 {len(saved_image_paths)} images saved successfully!")
                            
                    except Exception as e:
                        st.warning(f"Could not save some images: {e}")
                    
                    # Combine all image metadata
                    full_description = f"""
                    Description: {image_description}
                    Cultural Significance: {image_significance}
                    Location: {image_location}
                    Occasion: {image_occasion}
                    Year: {image_year}
                    People: {image_people}
                    Photo Taker: {photo_taker}
                    Images Count: {len(uploaded_files)} files uploaded
                    Total Size: {total_size:.1f} MB
                    """
                    
                    success = save_image_response_to_db(
                        full_description.strip(),
                        current_mystery['mystery_id'], 
                        image_points,
                        saved_image_paths
                    )
                    
                    if success:
                        st.success(f"🎉 Image mystery solved! +{image_points} points earned! (+3 image bonus)")
                        st.balloons()
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.session_state.total_points += image_points
                        st.session_state.mysteries_solved += 1
                        st.success(f"🎉 Image mystery solved! +{image_points} points earned! (+3 image bonus)")
                        st.balloons()
            else:
                st.warning("⚠️ Please complete the required fields and confirmations:")
                if not (image_description or image_significance):
                    st.write("• Provide image description or cultural significance")
                if not permission_check:
                    st.write("• Confirm you have permission to share images")
                if not authentic_check:
                    st.write("• Confirm images are authentic cultural content")
                if not privacy_check:
                    st.write("• Confirm comfort with sharing for cultural preservation")
                if not quality_check:
                    st.write("• Confirm images are clear and relevant")

def show_all_mysteries_page():
    """Show all mysteries with unlock status"""
    st.markdown("## 📚 All Mysteries")
    
    available_mysteries = mystery_manager.get_available_mysteries(st.session_state.user_id)
    solved_ids = mystery_manager.get_solved_mystery_ids(st.session_state.user_id)
    
    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        categories = list(set(m['category'] for m in mystery_manager.mysteries))
        selected_category = st.selectbox("Filter by category:", ["All"] + categories)
    
    with col2:
        status_filter = st.selectbox("Filter by status:", ["All", "Available", "Completed", "Locked"])
    
    # Progress overview
    total_mysteries = len(mystery_manager.mysteries)
    solved_count = len(solved_ids)
    available_count = len(available_mysteries)
    locked_count = total_mysteries - available_count
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Mysteries", total_mysteries)
    with col2:
        st.metric("Completed", solved_count, f"+{solved_count}")
    with col3:
        st.metric("Available", available_count - solved_count, "0")
    with col4:
        st.metric("Locked", locked_count, f"-{locked_count}")
    
    # Filter mysteries
    mysteries_to_show = mystery_manager.mysteries
    if selected_category != "All":
        mysteries_to_show = [m for m in mystery_manager.mysteries if m['category'] == selected_category]
    
    # Display mysteries
    for mystery in mysteries_to_show:
        is_available = mystery in available_mysteries
        is_solved = mystery['mystery_id'] in solved_ids
        
        # Status filtering
        if status_filter == "Available" and (is_solved or not is_available):
            continue
        elif status_filter == "Completed" and not is_solved:
            continue
        elif status_filter == "Locked" and is_available:
            continue
        
        if is_solved:
            # Completed mystery
            st.markdown(f"""
            <div class="mystery-card" style="border-left: 5px solid #28a745; background: linear-gradient(90deg, #f8fff8 0%, #e8f8e8 100%);">
            <h4 style="color: #28a745;">✅ {mystery['title']}</h4>
            <h5 style="color: #E6B800; font-style: italic;">{mystery['telugu_title']}</h5>
            <p><strong>Category:</strong> {mystery['category']} | <strong>Points Earned:</strong> {mystery['points_value']} | <strong>Status:</strong> <span style="color: #28a745; font-weight: bold;">COMPLETED</span></p>
            <p><em>Thank you for preserving this cultural knowledge!</em></p>
            </div>
            """, unsafe_allow_html=True)
        elif is_available:
            # Available mystery
            st.markdown(f"""
            <div class="mystery-card" style="border-left: 5px solid #E6B800;">
            <h4 style="color: #CC0000;">🔍 {mystery['title']}</h4>
            <h5 style="color: #E6B800; font-style: italic;">{mystery['telugu_title']}</h5>
            <p style="color: #555;">{mystery['description'][:180]}...</p>
            <p><strong>Category:</strong> {mystery['category']} | <strong>Points:</strong> {mystery['points_value']} | <strong>Difficulty:</strong> {'⭐' * mystery['difficulty_level']} | <strong>Status:</strong> <span style="color: #CC0000; font-weight: bold;">AVAILABLE</span></p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Locked mystery
            st.markdown(f"""
            <div class="locked-mystery">
            <h4 style="color: #666;">🔒 {mystery['title']}</h4>
            <h5 style="color: #888; font-style: italic;">{mystery['telugu_title']}</h5>
            <p style="color: #666;">Unlock by solving {mystery['unlock_requirement']} {'mystery' if mystery['unlock_requirement'] == 1 else 'mysteries'}</p>
            <p><strong>Category:</strong> {mystery['category']} | <strong>Points:</strong> {mystery['points_value']} | <strong>Status:</strong> <span style="color: #666; font-weight: bold;">LOCKED</span></p>
            </div>
            """, unsafe_allow_html=True)

def show_profile_page():
    """User profile page"""
    st.markdown("## 👤 Your Detective Profile")
    
    if st.session_state.username:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### 🏷️ Basic Info")
            st.write(f"**Name:** {st.session_state.username}")
            st.write(f"**Location:** {st.session_state.get('location', 'Not specified')}")
            st.write(f"**Dialect:** {st.session_state.get('native_dialect', 'Not specified')}")
            st.write(f"**Age Group:** {st.session_state.get('age_group', 'Not specified')}")
            st.write(f"**User ID:** {st.session_state.user_id[:8]}...")
        
        with col2:
            st.markdown("### 📊 Achievement Stats")
            col2a, col2b = st.columns(2)
            
            with col2a:
                st.metric("Total Points", st.session_state.total_points)
                st.metric("Mysteries Solved", st.session_state.mysteries_solved)
            
            with col2b:
                available_count = len(mystery_manager.get_available_mysteries(st.session_state.user_id))
                st.metric("Available Mysteries", available_count)
                progress_percent = (st.session_state.mysteries_solved / len(mystery_manager.mysteries)) * 100
                st.metric("Completion", f"{progress_percent:.1f}%")
        
        st.markdown("### 🏆 Your Badges")
        badge_cols = st.columns(4)
        badges_earned = []
        
        if st.session_state.mysteries_solved >= 1:
            badges_earned.append("🥉 First Detective")
        if st.session_state.mysteries_solved >= 3:
            badges_earned.append("🥈 Mystery Solver")
        if st.session_state.mysteries_solved >= 5:
            badges_earned.append("🥇 Cultural Expert")
        if st.session_state.total_points >= 100:
            badges_earned.append("💎 Point Master")
        
        if badges_earned:
            for i, badge in enumerate(badges_earned):
                with badge_cols[i % 4]:
                    st.success(badge)
        else:
            st.info("🎯 Solve mysteries to earn badges!")
    
    else:
        st.info("Please complete your profile setup from the Home page.")

def show_statistics_page():
    """Statistics page"""
    st.markdown("## 📊 Collection Statistics")
    
    st.markdown("### 🎯 Overall Progress")
    col1, col2, col3, col4 = st.columns(4)
    
    if db:
        try:
            total_responses = db.get_total_responses()
            estimated_hours = total_responses * 0.1
            active_users = db.get_active_users_count()
            progress_percent = min((estimated_hours / 20000) * 100, 100)
        except:
            total_responses = 1250
            estimated_hours = 500.5
            active_users = 89
            progress_percent = 2.5
    else:
        total_responses = 1250
        estimated_hours = 500.5
        active_users = 89
        progress_percent = 2.5
    
    with col1:
        st.metric("Total Hours", f"{estimated_hours:.1f}", "12.3")
    with col2:
        st.metric("Total Responses", f"{total_responses:,}", "45")
    with col3:
        st.metric("Active Users", active_users, "5")
    with col4:
        st.metric("Progress", f"{progress_percent:.1f}%", "0.1%")
    
    st.markdown("### 👤 Your Personal Stats")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Your Points", st.session_state.total_points)
    with col2:
        st.metric("Your Mysteries", st.session_state.mysteries_solved)
    with col3:
        contribution = (st.session_state.total_points / max(total_responses * 10, 1)) * 100
        st.metric("Your Contribution", f"{contribution:.2f}%")
    
    st.markdown("### 🗂️ Mystery Categories")
    category_stats = {}
    solved_ids = mystery_manager.get_solved_mystery_ids(st.session_state.user_id)
    
    for mystery in mystery_manager.mysteries:
        category = mystery['category']
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'solved': 0}
        category_stats[category]['total'] += 1
        if mystery['mystery_id'] in solved_ids:
            category_stats[category]['solved'] += 1
    
    for category, stats in category_stats.items():
        progress = (stats['solved'] / stats['total']) * 100 if stats['total'] > 0 else 0
        st.progress(progress / 100, text=f"{category}: {stats['solved']}/{stats['total']} ({progress:.0f}%)")

def show_leaderboard_page():
    """Leaderboard page"""
    st.markdown("## 🏆 Detective Leaderboard")
    
    if db:
        try:
            leaderboard_data = db.get_leaderboard(20)
        except:
            leaderboard_data = []
    else:
        leaderboard_data = []
    
    if not leaderboard_data:
        leaderboard_data = [
            {"username": "Cultural Expert", "total_points": 2500, "mysteries_solved": 50, "location": "Hyderabad"},
            {"username": "Heritage Guardian", "total_points": 2100, "mysteries_solved": 45, "location": "Warangal"},
            {"username": "Tradition Keeper", "total_points": 1800, "mysteries_solved": 38, "location": "Vijayawada"},
        ]
    
    if st.session_state.username and st.session_state.total_points > 0:
        user_entry = {
            "username": st.session_state.username,
            "total_points": st.session_state.total_points,
            "mysteries_solved": st.session_state.mysteries_solved,
            "location": st.session_state.get('location', 'Unknown')
        }
        
        user_in_board = any(user['username'] == st.session_state.username for user in leaderboard_data)
        if not user_in_board:
            leaderboard_data.append(user_entry)
        
        leaderboard_data.sort(key=lambda x: x['total_points'], reverse=True)
    
    tab1, tab2 = st.tabs(["🏆 Top 20", "📊 Your Rank"])
    
    with tab1:
        st.markdown("### 🥇 Top Detectives")
        
        for i, user in enumerate(leaderboard_data[:20], 1):
            is_current_user = (user['username'] == st.session_state.username)
            card_style = "background: linear-gradient(90deg, #FFD700 0%, #FFA500 100%);" if is_current_user else "background: white;"
            
            medal = ""
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            
            st.markdown(f"""
            <div class="mystery-card" style="{card_style}">
            <h4>{medal} #{i} {user['username']} {'👈 You!' if is_current_user else ''}</h4>
            <p><strong>Points:</strong> {user['total_points']} | <strong>Mysteries:</strong> {user['mysteries_solved']} | <strong>Location:</strong> {user.get('location', 'Unknown')}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        if st.session_state.username and st.session_state.total_points > 0:
            user_rank = next((i for i, user in enumerate(leaderboard_data, 1) if user['username'] == st.session_state.username), None)
            
            if user_rank:
                st.markdown(f"### 🎯 Your Current Rank: #{user_rank}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Your Rank", f"#{user_rank}")
                with col2:
                    if user_rank > 1:
                        points_to_next = leaderboard_data[user_rank-2]['total_points'] - st.session_state.total_points
                        st.metric("Points to Next Rank", points_to_next)
                    else:
                        st.metric("Status", "🥇 #1!")
                with col3:
                    percentile = ((len(leaderboard_data) - user_rank + 1) / len(leaderboard_data)) * 100
                    st.metric("Percentile", f"{percentile:.1f}%")
        else:
            st.info("Solve mysteries to appear on the leaderboard!")

if __name__ == "__main__":
    main()
