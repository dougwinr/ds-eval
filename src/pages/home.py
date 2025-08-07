import streamlit as st
from datetime import datetime, timedelta

def home_page():
    st.title("Bem-vindo à Plataforma de Avaliação de IA & Ciência de Dados")
    st.markdown("---")
    
    # Check if user is logged in
    if not st.session_state.get('logged_in', False):
        st.error("Por favor, faça login primeiro para acessar a plataforma.")
        return
    
    username = st.session_state['username']
    is_admin = st.session_state.get('is_admin', False)
    
    # Welcome message
    if is_admin:
        st.success(f"Bem-vindo, Admin {username}!")
    else:
        st.success(f"Bem-vindo, {username}!")
    
    st.markdown("---")
    
    # Main navigation
    st.subheader("Funcionalidades Disponíveis")
    
    # Create feature cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Teste ASK
        **Teste de Conhecimento em IA e Ciência de Dados**
        
        Teste seu conhecimento em:
        - Conceitos de Machine Learning
        - Fundamentos de IA
        - Princípios de Ciência de Dados
        - Compreensão de algoritmos
        
        *Duração: ~10 minutos*
        """)
        
        if st.button("Fazer Teste ASK", key="ask_home"):
            st.session_state.page = "ask_test"
            st.rerun()
    
    with col2:
        st.markdown("""
        ### Teste ADTI
        **Indicador de Tipo de IA e Dados**
        
        Descubra seu:
        - Tipo de personalidade em IA
        - Preferências em ciência de dados
        - Estilo de aprendizado
        - Orientação de carreira
        
        *Duração: ~10 minutos*
        """)
        
        if st.button("Fazer Teste ADTI", key="adt_home"):
            st.session_state.page = "adti_test"
            st.rerun()
    
    st.markdown("---")
    
    # Additional features
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("""
        ### Perfil
        **Visualize Seus Resultados**
        
        - Histórico de testes
        - Análise de performance
        - Acompanhamento de progresso
        - Insights detalhados
        
        *Acompanhe sua jornada de aprendizado*
        """)
        
        if st.button("Ver Perfil", key="profile_home"):
            st.session_state.page = "profile"
            st.rerun()
    
    with col4:
        if is_admin:
            st.markdown("""
            ### Painel Admin
            **Gerenciamento de Usuários**
            
            - Criar novos usuários
            - Gerar senhas
            - Monitorar atividade de usuários
            - Gerenciar acesso
            
            *Recurso exclusivo para admin*
            """)
            
            if st.button("Painel Admin", key="admin_home"):
                st.session_state.page = "admin"
                st.rerun()
        else:
            st.markdown("""
            ### Estatísticas Rápidas
            **Seu Progresso**
            
            - Pontuações recentes de testes
            - Tendências de performance
            - Recomendações de aprendizado
            - Acompanhamento de conquistas
            
            *Insights personalizados*
            """)
            
            if st.button("Ver Estatísticas", key="stats_home"):
                st.session_state.page = "profile"
                st.rerun()
    
    st.markdown("---")
    
    # Information section
    st.subheader("Sobre a Plataforma")
    
    st.markdown("""
    Esta plataforma fornece ferramentas abrangentes de avaliação para profissionais de IA e Ciência de Dados:
    
    **Teste ASK (Conhecimento em IA e Ciência de Dados)**
    - Avalia conhecimento teórico
    - Testa compreensão de conceitos fundamentais
    - Mede proficiência técnica
    - Fornece feedback detalhado
    
    **Teste ADTI (Indicador de Tipo de IA e Dados)**
    - Avalia preferências de personalidade
    - Identifica estilos de aprendizado
    - Sugere caminhos de carreira
    - Personaliza recomendações
    
    **Acompanhamento de Progresso**
    - Monitore sua melhoria ao longo do tempo
    - Compare diferentes tentativas de teste
    - Obtenha recomendações personalizadas
    - Acompanhe marcos de aprendizado
    """)
    
    # Quick tips
    st.subheader("Dicas Rápidas")
    
    tips = [
        "Faça ambos os testes para obter uma avaliação completa do seu perfil de IA e Ciência de Dados",
        "Revise seus resultados na seção Perfil para entender seus pontos fortes e áreas de melhoria",
        "Refaça os testes periodicamente para acompanhar seu progresso e aprendizado",
        "Use o feedback detalhado para focar seus esforços de aprendizado"
    ]
    
    for i, tip in enumerate(tips, 1):
        st.write(f"{i}. {tip}")
    
    # Logout section
    st.markdown("---")
    st.subheader("Conta")
    
    col5, col6 = st.columns([3, 1])
    
    with col5:
        st.info(f"Conectado como: **{username}** ({'Admin' if is_admin else 'Usuário'})")
    
    with col6:
        if st.button("Sair"):
            # Clear all sessions
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from session_manager import SessionManager
            session_manager = SessionManager()
            session_manager.clear_all_sessions()
            
            # Clear session state
            for key in ['logged_in', 'username', 'is_admin', 'session_token']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
