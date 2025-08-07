import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
from database import Database
from datetime import datetime, timedelta
import json

def create_ask_polar_graph(pillar_scores, career_level):
    """Create a polar graph (radar chart) for ASK test results"""
    # Data for plotting
    pillars = list(pillar_scores.keys())
    scores = list(pillar_scores.values())
    
    # Number of variables
    num_vars = len(pillars)
    
    # Compute angle for each axis
    angles = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
    angles += angles[:1]  # Complete the circle
    
    # Add the first value to the end to close the plot
    scores += scores[:1]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    # Plot data
    ax.plot(angles, scores, 'o-', linewidth=2, label='Your Scores')
    ax.fill(angles, scores, alpha=0.25)
    
    # Fix axis to go in the right order and start at 12 o'clock
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    # Draw axis lines for each angle and label
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(pillars)
    
    # Add labels
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'])
    ax.grid(True)
    
    # Add title
    plt.title(f'ASK Test Results - Career Level: {career_level}', size=16, y=1.1)
    
    return fig

def profile_page():
    st.title("Perfil do Usuário")
    st.markdown("---")
    
    # Check if user is logged in
    if not st.session_state.get('logged_in', False):
        st.error("Por favor, faça login primeiro para visualizar seu perfil.")
        return
    
    # Initialize database
    db = Database()
    username = st.session_state['username']
    is_admin = st.session_state.get('is_admin', False)
    
    # User information
    st.subheader("Informações do Usuário")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Usuário:** {username}")
        st.write(f"**Função:** {'Administrador' if is_admin else 'Usuário'}")
    
    with col2:
        st.write(f"**Status de Login:** {'🟢 Ativo' if st.session_state.get('logged_in') else '🔴 Inativo'}")
        st.write(f"**Sessão:** {'🟢 Válida' if st.session_state.get('session_token') else '🔴 Expirada'}")
    
    # Get test results
    results = db.get_user_test_results(username)
    
    # Fix any old ADTI results that have full names instead of codes
    db.fix_adti_primary_type_codes()
    
    if results:
        # Convert to DataFrame for easier analysis
        test_data = []
        for test_type, score, completed_at, answers in results:
            test_data.append({
                'Test Type': test_type,
                'Score': score,
                'Completed At': completed_at,
                'Answers': answers
            })
        
        df = pd.DataFrame(test_data)
        
        # Overall statistics
        st.subheader("Estatísticas Gerais")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Testes", len(results))
        
        with col2:
            avg_score = df['Score'].mean()
            st.metric("Pontuação Média", f"{avg_score:.1f}")
        
        with col3:
            best_score = df['Score'].max()
            st.metric("Melhor Pontuação", f"{best_score:.1f}")
        
        with col4:
            recent_tests = len([r for r in results if r[0] == 'ADTI'])
            st.metric("Testes ADTI", recent_tests)
        
        # Detailed results section
        st.subheader("Resultados Detalhados dos Testes")
        
        # Group by test type
        ask_results = [r for r in results if r[0] == 'ASK']
        adti_results = [r for r in results if r[0] == 'ADTI']
        
        # ASK Test Results with detailed analysis
        if ask_results:
            st.write("**Resultados do Teste ASK:**")
            
            # Show latest ASK result with detailed analysis
            latest_ask = ask_results[0]  # Most recent result
            test_type, score, completed_at, answers_str = latest_ask
            
            st.write(f"**Último Teste:** {completed_at}")
            
            # Parse detailed results if available
            try:
                detailed_data = json.loads(answers_str)
                if isinstance(detailed_data, dict) and 'pillar_scores' in detailed_data:
                    pillar_scores = detailed_data['pillar_scores']
                    career_level = detailed_data.get('career_level', 'Unknown')
                    
                    st.write(f"**Nível de Carreira:** {career_level}")
                    st.write(f"**Pontuação Geral:** {score:.1f}")
                    
                    # Check if we have separate evaluation scores
                    if 'user_weighted_score' in detailed_data and 'manager_weighted_score' in detailed_data:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Autoavaliação", f"{detailed_data.get('user_weighted_score', 0):.1f}")
                        with col2:
                            manager_score = detailed_data.get('manager_weighted_score', 0)
                            if manager_score > 0:
                                st.metric("Avaliação do Líder", f"{manager_score:.1f}")
                            else:
                                st.metric("Avaliação do Líder", "Não avaliado")
                        with col3:
                            st.metric("Pontuação Combinada", f"{detailed_data.get('combined_weighted_score', 0):.1f}")
                    
                    # Check if we have detailed results
                    if 'meets_current_level' in detailed_data:
                        st.write(f"**Atende ao Nível Atual:** {'✅ Sim' if detailed_data.get('meets_current_level', False) else '❌ Não'}")
                    
                    # Create and display polar graph
                    st.subheader("Análise do Gráfico Polar")
                    fig = create_ask_polar_graph(pillar_scores, career_level)
                    st.pyplot(fig)
                    
                    # Show pillar scores with visual representation
                    st.subheader("Análise dos Pilares")
                    
                    # Check if we have separate pillar scores
                    if 'user_pillar_scores' in detailed_data and 'manager_pillar_scores' in detailed_data:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Pontuações dos Pilares de Autoavaliação:**")
                            for pillar, pillar_score in detailed_data['user_pillar_scores'].items():
                                progress = pillar_score / 100  # Normalize to 0-1
                                st.write(f"**{pillar}:** {pillar_score:.1f}")
                                st.progress(progress)
                        
                        with col2:
                            st.write("**Pontuações dos Pilares de Avaliação do Líder:**")
                            for pillar, pillar_score in detailed_data['manager_pillar_scores'].items():
                                if pillar_score > 0:
                                    progress = pillar_score / 100  # Normalize to 0-1
                                    st.write(f"**{pillar}:** {pillar_score:.1f}")
                                    st.progress(progress)
                                else:
                                    st.write(f"**{pillar}:** Não avaliado")
                                    st.progress(0)
                        
                        # Combined scores
                        st.subheader("Pontuações Combinadas dos Pilares")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            for pillar, pillar_score in pillar_scores.items():
                                progress = pillar_score / 100  # Normalize to 0-1
                                st.write(f"**{pillar}:** {pillar_score:.1f}")
                                st.progress(progress)
                        
                        with col2:
                            # Show score range and strengths/weaknesses
                            min_score = min(pillar_scores.values())
                            max_score = max(pillar_scores.values())
                            st.write(f"**Faixa de Pontuação:** {min_score:.1f} - {max_score:.1f}")
                            st.write(f"**Pontuação Média:** {sum(pillar_scores.values()) / len(pillar_scores):.1f}")
                            
                            # Show strengths and weaknesses
                            sorted_pillars = sorted(pillar_scores.items(), key=lambda x: x[1], reverse=True)
                            st.write("**Principal Ponto Forte:** " + sorted_pillars[0][0])
                            st.write("**Área para Melhorar:** " + sorted_pillars[-1][0])
                    else:
                        # Fallback for old format
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            for pillar, pillar_score in pillar_scores.items():
                                progress = pillar_score / 100  # Normalize to 0-1
                                st.write(f"**{pillar}:** {pillar_score:.1f}")
                                st.progress(progress)
                        
                        with col2:
                            # Show score range and strengths/weaknesses
                            min_score = min(pillar_scores.values())
                            max_score = max(pillar_scores.values())
                            st.write(f"**Score Range:** {min_score:.1f} - {max_score:.1f}")
                            st.write(f"**Average Score:** {sum(pillar_scores.values()) / len(pillar_scores):.1f}")
                            
                            # Show strengths and weaknesses
                            sorted_pillars = sorted(pillar_scores.items(), key=lambda x: x[1], reverse=True)
                            st.write("**🏆 Top Strength:** " + sorted_pillars[0][0])
                            st.write("**📈 Area to Improve:** " + sorted_pillars[-1][0])
                    
                    # Show top 5 gaps if available
                    if 'top5_gaps' in detailed_data and detailed_data['top5_gaps']:
                        st.subheader("Principais Habilidades para Desenvolver")
                        st.write("**Foque em seguida:**")
                        for i, gap in enumerate(detailed_data['top5_gaps'][:5], 1):
                            st.write(f"{i}. **{gap['question']}** ({gap['pillar']}) - Atual: {gap['user_rating']}/5")
                    
                    # Show career progression
                    career_progression = ["Estagiário", "Júnior", "Pleno", "Sênior", "Especialista", "PM", "Gestor"]
                    current_idx = career_progression.index(career_level) if career_level in career_progression else 0
                    next_level = career_progression[min(current_idx + 1, len(career_progression) - 1)]
                    
                    st.subheader("Progressão de Carreira")
                    st.write(f"**Nível Atual:** {career_level}")
                    if career_level != "Gestor":
                        st.write(f"**Próximo Nível:** {next_level}")
                    
                    # Show previous results
                    if len(ask_results) > 1:
                        st.subheader("Evolução de Carreira")
                        st.write("**Resultados Anteriores do ASK:**")
                        for i, result in enumerate(ask_results[1:4], 1):  # Show last 3 previous results
                            prev_test_type, prev_score, prev_completed_at, prev_answers = result
                            st.write(f"Tentativa {i}: {prev_score:.1f} - {prev_completed_at}")
                
                else:
                    st.write("**Nível de Carreira:** Resultado padrão do ASK")
                    st.write(f"**Pontuação:** {score:.1f}")
                    
            except (json.JSONDecodeError, KeyError):
                st.write("**Nível de Carreira:** Resultado padrão do ASK")
                st.write(f"**Pontuação:** {score:.1f}")
        
        # ADTI Test Results with detailed analysis
        if adti_results:
            st.write("**Resultados do Teste ADTI:**")
            
            # Define personality types for reference
            personality_types = {
                "DSTA": {"type": "Data Strategist", "category": "Technical"},
                "DVRT": {"type": "Data Virtuoso", "category": "Technical"},
                "DLOG": {"type": "Data Logician", "category": "Technical"},
                "DVIS": {"type": "Data Visionary", "category": "Technical"},
                "DCOL": {"type": "Data Collaborator", "category": "Collaborative"},
                "DSUP": {"type": "Data Supporter", "category": "Collaborative"},
                "DADV": {"type": "Data Advocate", "category": "Collaborative"},
                "DINT": {"type": "Data Integrator", "category": "Collaborative"},
                "DCOM": {"type": "Data Commander", "category": "Leadership"},
                "DEXE": {"type": "Data Executive", "category": "Leadership"},
                "DINN": {"type": "Data Innovator", "category": "Leadership"},
                "DPRO": {"type": "Data Protagonist", "category": "Leadership"},
                "DCRT": {"type": "Data Creator", "category": "Creative"},
                "DCOMM": {"type": "Data Communicator", "category": "Creative"},
                "DENT": {"type": "Data Entrepreneur", "category": "Creative"},
                "DACT": {"type": "Data Activist", "category": "Creative"}
            }
            
            # Show latest ADTI result with detailed analysis
            latest_adti = adti_results[0]  # Most recent result
            test_type, score, completed_at, answers_str = latest_adti
            
            st.write(f"**Latest Test:** {completed_at}")
            
            # Parse detailed results if available
            try:
                detailed_data = json.loads(answers_str)
                if isinstance(detailed_data, dict) and 'all_scores' in detailed_data:
                    all_scores = detailed_data['all_scores']
                    primary_type = detailed_data.get('primary_type', 'Unknown')
                    
                    # Get the primary type name from the code
                    primary_type_name = personality_types.get(primary_type, {}).get('type', primary_type)
                    
                    st.write(f"**Primary Type:** {primary_type_name}")
                    st.write(f"**Primary Type Score:** {score:.1f}")
                    
                    # Show score range information
                    min_score = min(all_scores.values())
                    max_score = max(all_scores.values())
                    st.write(f"**Score Range:** {min_score:.1f} - {max_score:.1f}")
                    
                    # Sort personalities by score
                    sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
                    top_5 = sorted_scores[:5]
                    least_5 = sorted_scores[-5:]
                    
                    # Display detailed analysis
                    st.subheader("🎯 Personality Analysis")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🏆 Top 5 Personality Matches:**")
                        for i, (code, score_val) in enumerate(top_5, 1):
                            personality = personality_types.get(code, {"type": code, "category": "Unknown"})
                            st.markdown(f"{i}. **{personality['type']}** ({code}) - Score: {score_val:.1f}")
                            st.markdown(f"   Category: {personality['category']}")
                    
                    with col2:
                        st.markdown("**📉 Least 5 Personality Matches:**")
                        for i, (code, score_val) in enumerate(least_5, 1):
                            personality = personality_types.get(code, {"type": code, "category": "Unknown"})
                            st.markdown(f"{i}. **{personality['type']}** ({code}) - Score: {score_val:.1f}")
                            st.markdown(f"   Category: {personality['category']}")
                    
                    # Show category breakdown
                    st.subheader("📈 Category Analysis")
                    category_scores = {}
                    for code, score_val in all_scores.items():
                        personality = personality_types.get(code, {"category": "Unknown"})
                        category = personality['category']
                        if category not in category_scores:
                            category_scores[category] = []
                        category_scores[category].append((code, score_val))
                    
                    for category, scores in category_scores.items():
                        avg_score = sum(score for _, score in scores) / len(scores)
                        max_score = max(scores, key=lambda x: x[1])
                        st.write(f"**{category}:** Average: {avg_score:.1f}, Highest: {personality_types[max_score[0]]['type']} ({max_score[1]:.1f})")
                    
                    # Show personality evolution over time
                    if len(adti_results) > 1:
                        st.subheader("📊 Personality Evolution")
                        st.write("**Previous ADTI Results:**")
                        for i, result in enumerate(adti_results[1:4], 1):  # Show last 3 previous results
                            prev_test_type, prev_score, prev_completed_at, prev_answers = result
                            st.write(f"Attempt {i+1}: {prev_score} - {prev_completed_at}")
                
                else:
                    st.write("**Primary Type:** Standard ADTI result")
                    st.write(f"**Primary Type Score:** {score:.1f}")
                    
            except (json.JSONDecodeError, KeyError):
                st.write("**Primary Type:** Standard ADTI result")
                st.write(f"**Primary Type Score:** {score:.1f}")
        
        # Performance insights
        st.subheader("💡 Performance Insights")
        
        if len(test_data) > 0:
            # Calculate insights
            avg_score = df['Score'].mean()
            best_score = df['Score'].max()
            test_count = len(df)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Average Score", f"{avg_score:.1f}")
            
            with col2:
                st.metric("Best Score", f"{best_score:.1f}")
            
            with col3:
                st.metric("Tests Taken", test_count)
            
            # Recommendations
            st.write("**🎯 Recommendations:**")
            if avg_score < 70:
                st.warning("Consider retaking tests to improve your understanding of AI and Data Science concepts.")
            elif avg_score < 85:
                st.info("Good performance! Consider exploring advanced topics in AI and Data Science.")
            else:
                st.success("Excellent performance! You have a strong foundation in AI and Data Science.")
        
    else:
        st.info("No test results found. Take some tests to see your results here!")
        
        # Quick action buttons
        st.subheader("🚀 Quick Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Take ASK Test"):
                st.session_state.page = "ask_test"
                st.rerun()
        
        with col2:
            if st.button("Take ADTI Test"):
                st.session_state.page = "adti_test"
                st.rerun()
    
    # Account actions
    st.markdown("---")
    st.subheader("⚙️ Account Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Profile"):
            st.rerun()
    
    with col2:
        if st.button("🚪 Logout"):
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
    
    # Navigation
    st.markdown("---")
    if st.button("🏠 Back to Home"):
        st.session_state.page = "home"
        st.rerun()
