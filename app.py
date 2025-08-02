# Fix Streamlit permission issues BEFORE importing streamlit
import os
import tempfile
import sys
from pathlib import Path

# Set Streamlit environment variables to use temp directory
temp_dir = tempfile.gettempdir()
os.environ['STREAMLIT_HOME'] = temp_dir
os.environ['STREAMLIT_CONFIG_DIR'] = temp_dir
os.environ['STREAMLIT_STATIC_PATH'] = temp_dir

# Create .streamlit directory in temp location
try:
    streamlit_dir = Path(temp_dir) / '.streamlit'
    streamlit_dir.mkdir(exist_ok=True)
    
    # Create basic config files
    config_file = streamlit_dir / 'config.toml'
    if not config_file.exists():
        with open(config_file, 'w') as f:
            f.write("""[server]
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
""")
            
    credentials_file = streamlit_dir / 'credentials.toml'
    if not credentials_file.exists():
        with open(credentials_file, 'w') as f:
            f.write('[general]\nemail = ""\n')
            
except Exception as e:
    # If we can't create config files, continue anyway
    pass

# NOW import streamlit and other modules
import streamlit as st
import pandas as pd
import uuid
import sqlite3
import random
from datetime import datetime

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

# Custom CSS - Dark Theme
def apply_custom_css():
    st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #2C1810 0%, #1A0F0A 100%);
        color: #F5F5DC;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%);
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
        box-shadow: 0 4px 8px rgba(255,107,53,0.3);
    }
    
    .mystery-card {
        background: linear-gradient(135deg, #3D2817 0%, #2A1B0F 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #FF6B35;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin: 1rem 0;
        color: #F5F5DC;
    }
    
    .locked-mystery {
        background: linear-gradient(135deg, #4A4A4A 0%, #2D2D2D 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #666;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin: 1rem 0;
        opacity: 0.6;
        color: #CCCCCC;
    }
    
    .image-upload {
        border: 2px dashed #FF6B35;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
        background: linear-gradient(135deg, #3D2817 0%, #2A1B0F 100%);
        color: #F5F5DC;
    }
    
    .stSidebar {
        background: linear-gradient(180deg, #1A0F0A 0%, #2C1810 100%);
    }
    
    .stSidebar .stMarkdown {
        color: #F5F5DC;
    }
    
    .stTextArea textarea {
        background-color: #3D2817;
        color: #F5F5DC;
        border: 2px solid #FF6B35;
    }
    
    .stTextInput input {
        background-color: #3D2817;
        color: #F5F5DC;
        border: 2px solid #FF6B35;
    }
    
    .stSelectbox select {
        background-color: #3D2817;
        color: #F5F5DC;
        border: 2px solid #FF6B35;
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
    """Save response with type support"""
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
            **2. 📝 Share Your Knowledge**
            - Write detailed responses in Telugu
            - Upload cultural photos
            - Share family traditions
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
            <h3 style="color: #FF6B35;">{current_mystery['title']}</h3>
            <h4 style="color: #F7931E; font-style: italic;">{current_mystery['telugu_title']}</h4>
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
    """Mystery solving interface with mobile-friendly forms"""
    current_mystery = get_current_mystery()
    
    if not current_mystery:
        st.markdown("## 🎉 All Available Mysteries Completed!")
        st.success("Congratulations! You've solved all currently available mysteries. More mysteries will unlock as you progress!")
        st.balloons()
        return
    
    st.markdown("## 🔍 Current Mystery")
    
    st.markdown(f"""
    <div class="mystery-card">
    <h3 style="color: #FF6B35;">{current_mystery['title']}</h3>
    <h4 style="color: #F7931E; font-style: italic;">{current_mystery['telugu_title']}</h4>
    <p style="font-size: 1.1rem; line-height: 1.6;">
    {current_mystery['description']}
    </p>
    <p><strong>Category:</strong> {current_mystery['category']} | <strong>Points:</strong> {current_mystery['points_value']} | <strong>Difficulty:</strong> {'⭐' * current_mystery['difficulty_level']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Response options
    st.markdown("### 📝 Choose Your Response Method")
    st.info("🎯 **Bonus Points:** Text responses earn base points, Image responses get +3 bonus points!")
    
    tab1, tab2 = st.tabs(["✍️ Text Response", "📸 Image Response"])
    
    with tab1:
        st.markdown("#### ✍️ Write Your Response in Telugu")
        st.markdown("Share your knowledge about this cultural mystery:")
        
        # Mobile-optimized form
        with st.form("telugu_response_form", border=True):
            response_text = st.text_area(
                "Your Cultural Knowledge:",
                height=300,
                placeholder="మీ ఉత్తరం ఇక్కడ తెలుగులో వ్రాయండి...\n\nExample: మా ఊరిలో బతుకమ్మకు ఎల్లె, మల్లె, జాసుడు పువ్వులను వాడతాము. మా అజ్జి చెప్పింది...",
                help="Share your personal experiences, family traditions, and local variations. Minimum 50 words required.",
                key="mobile_mystery_response"
            )
            
            # Mobile-friendly analytics
            if response_text:
                word_count = len(response_text.split())
                char_count = len(response_text)
                telugu_chars = len([c for c in response_text if '\u0c00' <= c <= '\u0c7f'])
                
                # Simple mobile layout
                col1, col2 = st.columns(2)
                with col1:
                    st.text(f"📝 Words: {word_count}")
                    st.text(f"🔤 Characters: {char_count}")
                with col2:
                    st.text(f"తె Telugu: {telugu_chars}")
                    quality = min(word_count/50 * 5, 5)
                    st.text(f"⭐ Quality: {quality:.1f}/5")
                
                # Status indicator
                if word_count >= 50:
                    st.success("✅ Great! Your response meets the minimum requirement.")
                    if telugu_chars > char_count * 0.3:
                        st.success("🎉 Excellent use of Telugu script!")
            
            # Large submit button
            submitted = st.form_submit_button(
                "📤 Submit Text Response",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                if response_text and len(response_text.split()) >= 50:
                    success = save_response_to_db(
                        response_text, len(response_text.split()), 
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
                        st.rerun()
                else:
                    if not response_text:
                        st.error("⚠️ Please enter your response before submitting.")
                    else:
                        word_count = len(response_text.split())
                        st.error(f"⚠️ Please write at least 50 words. You have {word_count} words.")
                        st.progress(min(word_count/50, 1.0))
    
    with tab2:
        st.markdown("#### 📸 Upload Cultural Images")
        st.markdown("Share photos that relate to this cultural mystery:")
        st.info("📷 Upload photos of festivals, food, traditions, rituals, or family celebrations")
        
        # Image upload with simplified interface for mobile
        uploaded_files = st.file_uploader(
            "Choose images...", 
            type=['png', 'jpg', 'jpeg'], 
            accept_multiple_files=True,
            key="mystery_image_upload",
            help="Maximum 5 images, JPG/PNG formats"
        )
        
        if uploaded_files:
            if len(uploaded_files) > 5:
                st.warning("⚠️ Maximum 5 images allowed. Only the first 5 will be processed.")
                uploaded_files = uploaded_files[:5]
            
            # Display images
            for i, uploaded_file in enumerate(uploaded_files):
                st.image(uploaded_file, caption=f"Image {i+1}", width=300)
            
            # Simple description
            image_description = st.text_area(
                "Describe your images in Telugu:",
                placeholder="చిత్రాల గురించి తెలుగులో వివరించండి...",
                key="image_description",
                height=120
            )
            
            # Simple metadata
            col1, col2 = st.columns(2)
            with col1:
                image_location = st.text_input("📍 Location:", placeholder="City, Village...")
                image_occasion = st.selectbox("🎉 Occasion:", [
                    "Select...", "Bathukamma", "Ugadi", "Bonalu", "Wedding", "Festival"
                ])
            
            with col2:
                image_year = st.number_input("📅 Year:", min_value=1950, max_value=2025, value=2024)
                image_significance = st.text_area("✨ Why important?", height=60)
            
            # Confirmations
            permission_ok = st.checkbox("I have permission to share these images")
            authentic_ok = st.checkbox("These are authentic cultural images")
            
            if image_description and permission_ok and authentic_ok:
                if st.button("📤 Submit Images", type="primary", use_container_width=True):
                    image_points = current_mystery['points_value'] + 3
                    
                    # Simple description combining all info
                    full_description = f"""
                    Description: {image_description}
                    Location: {image_location}
                    Occasion: {image_occasion}
                    Year: {image_year}
                    Significance: {image_significance}
                    """
                    
                    success = save_image_response_to_db(
                        full_description.strip(),
                        current_mystery['mystery_id'], 
                        image_points,
                        []  # Not saving files for simplicity
                    )
                    
                    if success:
                        st.success(f"🎉 Images submitted! +{image_points} points (+3 bonus)")
                        st.balloons()
                        st.rerun()

def show_all_mysteries_page():
    """Show all mysteries with unlock status"""
    st.markdown("## 📚 All Mysteries")
    
    available_mysteries = mystery_manager.get_available_mysteries(st.session_state.user_id)
    solved_ids = mystery_manager.get_solved_mystery_ids(st.session_state.user_id)
    
    # Progress overview
    total_mysteries = len(mystery_manager.mysteries)
    solved_count = len(solved_ids)
    available_count = len(available_mysteries)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", total_mysteries)
    with col2:
        st.metric("Completed", solved_count)
    with col3:
        st.metric("Available", available_count - solved_count)
    
    # Display mysteries
    for mystery in mystery_manager.mysteries:
        is_available = mystery in available_mysteries
        is_solved = mystery['mystery_id'] in solved_ids
        
        if is_solved:
            st.markdown(f"""
            <div class="mystery-card" style="border-left: 5px solid #90EE90;">
            <h4 style="color: #90EE90;">✅ {mystery['title']}</h4>
            <h5 style="color: #F7931E;">{mystery['telugu_title']}</h5>
            <p><strong>Status:</strong> COMPLETED | <strong>Points:</strong> {mystery['points_value']}</p>
            </div>
            """, unsafe_allow_html=True)
        elif is_available:
            st.markdown(f"""
            <div class="mystery-card">
            <h4 style="color: #FF6B35;">🔍 {mystery['title']}</h4>
            <h5 style="color: #F7931E;">{mystery['telugu_title']}</h5>
            <p>{mystery['description'][:100]}...</p>
            <p><strong>Status:</strong> AVAILABLE | <strong>Points:</strong> {mystery['points_value']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="locked-mystery">
            <h4>🔒 {mystery['title']}</h4>
            <p>Unlock by solving {mystery['unlock_requirement']} mysteries</p>
            </div>
            """, unsafe_allow_html=True)

def show_profile_page():
    """User profile page"""
    st.markdown("## 👤 Your Detective Profile")
    
    if st.session_state.username:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏷️ Info")
            st.write(f"**Name:** {st.session_state.username}")
            st.write(f"**Location:** {st.session_state.get('location', 'Not set')}")
            st.write(f"**Dialect:** {st.session_state.get('native_dialect', 'Not set')}")
        
        with col2:
            st.markdown("### 📊 Stats")
            st.metric("Points", st.session_state.total_points)
            st.metric("Solved", st.session_state.mysteries_solved)
            progress = (st.session_state.mysteries_solved / len(mystery_manager.mysteries)) * 100
            st.metric("Progress", f"{progress:.1f}%")

def show_statistics_page():
    """Statistics page"""
    st.markdown("## 📊 Statistics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Collection Hours", "187.5", "+12.3")
    with col2:
        st.metric("Total Responses", "1,250", "+45")
    with col3:
        st.metric("Active Users", "89", "+5")
    
    st.progress(0.009, text="Progress towards 20,000 hours: 0.9%")

def show_leaderboard_page():
    """Leaderboard page"""
    st.markdown("## 🏆 Leaderboard")
    
    # Sample leaderboard data
    leaderboard = [
        {"username": "Cultural Guardian", "points": 2500, "mysteries": 48},
        {"username": "Heritage Keeper", "points": 2100, "mysteries": 45},
        {"username": "Tradition Bearer", "points": 1800, "mysteries": 38},
    ]
    
    # Add current user if they have points
    if st.session_state.username and st.session_state.total_points > 0:
        leaderboard.append({
            "username": st.session_state.username,
            "points": st.session_state.total_points,
            "mysteries": st.session_state.mysteries_solved
        })
        leaderboard.sort(key=lambda x: x['points'], reverse=True)
    
    for i, user in enumerate(leaderboard[:10], 1):
        is_current = user['username'] == st.session_state.username
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
        
        style = "background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%);" if is_current else "background: linear-gradient(135deg, #3D2817 0%, #2A1B0F 100%);"
        
        st.markdown(f"""
        <div style="padding: 1rem; margin: 0.5rem 0; border-radius: 8px; {style} color: #FFF;">
        <h4>{medal} #{i} {user['username']} {'👈 YOU!' if is_current else ''}</h4>
        <p>Points: {user['points']} | Mysteries: {user['mysteries']}</p>
        </div>
        """, unsafe_allow_html=True)

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
        <h1 style="color: #FF6B35; font-size: 3rem; margin-bottom: 0.5rem;">
            🕵 Telugu Bhasha Detective
        </h1>
        <p style="color: #F7931E; font-size: 1.2rem; font-style: italic;">
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
    st.sidebar.progress(0.025, text="500.5 / 20,000 hours")
    st.sidebar.text("1,250 total responses")
    
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
    <div style="text-align: center; padding: 1rem; color: #F7931E;">
        🎯 Target: 20,000+ hours of Telugu linguistic data collection<br>
        Built with ❤️ for Telugu language preservation
    </div>
    """, unsafe_allow_html=True)

# This is the critical main function call that was missing!
if __name__ == "__main__":
    main()
