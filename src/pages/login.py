import streamlit as st
from database import Database
from datetime import datetime, timedelta

def login_page():
    st.title("Entrar")
    st.markdown("---")
    
    # Initialize session manager
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from session_manager import SessionManager
    session_manager = SessionManager()
    
    # Create login form
    with st.form("login_form"):
        username = st.text_input("Usuário", placeholder="Digite seu usuário")
        password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        submit_button = st.form_submit_button("Entrar")
    
    if submit_button:
        if username and password:
            # Verify user credentials
            is_valid, is_admin = session_manager.db.verify_user(username, password)
            
            if is_valid:
                # Create session token
                session_token = session_manager.create_session(username, is_admin, "home")
                
                if session_token:
                    # Store user session
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['is_admin'] = is_admin
                    st.session_state['session_token'] = session_token
                    st.session_state['page'] = "home"
                    
                    st.success(f"Bem-vindo, {username}!")
                    st.rerun()
                else:
                    st.error("Falha ao criar sessão. Tente novamente.")
            else:
                st.error("Usuário ou senha inválidos. Tente novamente.")
        else:
            st.warning("Por favor, digite usuário e senha.")
    
    # Admin login info
    with st.expander("Informações de Login do Admin"):
        st.info("""
        **Credenciais Padrão do Admin:**
        - Usuário: `admin`
        - Senha: `admin123`
        
        Usuários admin podem gerenciar outros usuários e gerar senhas temporárias.
        """)
    
    # User information
    st.markdown("---")
    st.markdown("""
    ### Como usar este aplicativo:
    1. **Usuários Admin**: Faça login com credenciais de admin para gerenciar usuários e gerar senhas
    2. **Usuários Regulares**: Use a senha temporária fornecida pelo admin para fazer login
    3. **Testes**: Após o login, você pode fazer os testes ASK e ADTI
    4. **Perfil**: Visualize seus resultados de teste e progresso
    """)
