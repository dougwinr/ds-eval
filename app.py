import streamlit as st
import sys
import os
from datetime import datetime, timedelta

# Add src/pages directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'pages'))

# Import database and page modules
from database import Database
from session_manager import SessionManager
from src.pages.login import login_page
from src.pages.home import home_page
from src.pages.admin import admin_page
from src.pages.ask_test import ask_test_page

from src.pages.adti_test import adti_test_page
from src.pages.profile import profile_page

# Page configuration
st.set_page_config(
    page_title="Plataforma de Avaliação de IA & Ciência de Dados",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide default Streamlit elements
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    .stApp > header {background-color: transparent;}
    .stApp > footer {background-color: transparent;}
    .stApp > div[data-testid="stDecoration"] {background-image: none;}
    .stApp > div[data-testid="stDecoration"]::before {background-image: none;}
    .stApp > div[data-testid="stDecoration"]::after {background-image: none;}
    
    /* Remove default padding and margins */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Custom background */
    .stApp {
        background-color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    /* Custom sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    /* Hide only the hamburger menu */
    .css-1d391kg > div:first-child {
        display: none;
    }
    .css-1lcbmhc > div:first-child {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize session manager and cleanup expired sessions
    session_manager = SessionManager()
    session_manager.cleanup_expired_sessions()
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    
    # Check for existing session token from file storage
    if not st.session_state.logged_in:
        # Try to restore session from file
        current_session = session_manager.get_current_session()
        if current_session:
            # Restore session
            st.session_state.logged_in = True
            st.session_state.username = current_session['username']
            st.session_state.is_admin = current_session['is_admin']
            st.session_state.session_token = current_session['token']
            # Restore the last page visited
            st.session_state.page = current_session.get('current_page', 'home')
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Plataforma de Avaliação de IA")
        st.markdown("---")
        
        if st.session_state.logged_in:
            st.success(f"Bem-vindo, {st.session_state.username}!")
            
            # Navigation menu
            st.subheader("Navegação")
            
            # Main pages
            if st.button("Início", key="nav_home"):
                st.session_state.page = "home"
                if st.session_state.session_token:
                    session_manager.update_current_page(st.session_state.session_token, "home")
                st.rerun()
            
            if st.button("Teste ASK", key="nav_ask"):
                st.session_state.page = "ask_test"
                if st.session_state.session_token:
                    session_manager.update_current_page(st.session_state.session_token, "ask_test")
                st.rerun()
            
            if st.button("Teste ADTI", key="nav_adt"):
                st.session_state.page = "adti_test"
                if st.session_state.session_token:
                    session_manager.update_current_page(st.session_state.session_token, "adti_test")
                st.rerun()
            
            if st.button("Perfil", key="nav_profile"):
                st.session_state.page = "profile"
                if st.session_state.session_token:
                    session_manager.update_current_page(st.session_state.session_token, "profile")
                st.rerun()
            
            # Admin pages (only for admins)
            if st.session_state.is_admin:
                if st.button("Painel Admin", key="nav_admin"):
                    st.session_state.page = "admin"
                    if st.session_state.session_token:
                        session_manager.update_current_page(st.session_state.session_token, "admin")
                    st.rerun()
                

            
            st.markdown("---")
            
            # Account section
            st.subheader("Conta")
            if st.button("Sair", key="sidebar_logout"):
                # Clear all sessions
                session_manager.clear_all_sessions()
                
                # Clear session state
                for key in ['logged_in', 'username', 'is_admin', 'session_token']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.session_state.page = "login"
                st.rerun()
        
        else:
            st.info("Por favor, faça login para acessar a plataforma.")
            st.markdown("---")
            st.markdown("""
            **Credenciais Padrão do Admin:**
            - Usuário: `admin`
            - Senha: `admin123`
            """)
    
    # Main content area
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "admin":
        admin_page()
    elif st.session_state.page == "ask_test":
        ask_test_page()

    elif st.session_state.page == "adti_test":
        adti_test_page()
    elif st.session_state.page == "profile":
        profile_page()
    else:
        st.error("Página não encontrada!")
        st.session_state.page = "login"
        st.rerun()

if __name__ == "__main__":
    main()
