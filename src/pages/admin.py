import streamlit as st
import pandas as pd
import json
from database import Database
from datetime import datetime, timedelta

def admin_page():
    st.title("Painel de Administração")
    st.markdown("---")
    
    # Initialize database
    db = Database()
    
    # Check if user is admin
    if not st.session_state.get('is_admin', False):
        st.error("Acesso negado. Privilégios de administrador necessários.")
        return
    
    # Welcome message
    st.success(f"Bem-vindo, Admin {st.session_state['username']}!")
    
    # Create tabs for different admin functions
    tab1, tab2 = st.tabs(["Gerenciamento de Usuários", "Avaliação ASK"])
    
    with tab1:
        # Create new user section
        st.subheader("Criar Novo Usuário")
        with st.form("create_user_form"):
            new_username = st.text_input("Usuário", placeholder="Digite o nome de usuário")
            create_button = st.form_submit_button("Criar Usuário")
        
        if create_button and new_username:
            if db.create_user(new_username):
                st.success(f"Usuário '{new_username}' criado com sucesso!")
            else:
                st.error(f"Usuário '{new_username}' já existe ou a criação falhou.")
        
        st.markdown("---")
        
        # User management section
        st.subheader("Gerenciamento de Usuários")
        
        # Get all users
        users = db.get_all_users()
        
        if users:
            # Convert to DataFrame for better display
            user_data = []
            for user in users:
                username, created_at, temp_password, expires_at, is_used = user
                
                # Format dates
                created_str = created_at if isinstance(created_at, str) else created_at.strftime('%Y-%m-%d %H:%M')
                expires_str = "N/A" if not expires_at else (expires_at if isinstance(expires_at, str) else expires_at.strftime('%Y-%m-%d %H:%M'))
                
                # Password status
                if temp_password:
                    if is_used:
                        password_status = "Usado"
                    elif expires_at:
                        # Convert string to datetime if needed
                        if isinstance(expires_at, str):
                            try:
                                expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                            except:
                                expires_dt = datetime.now() - timedelta(days=1)  # Default to expired
                        else:
                            expires_dt = expires_at
                        
                        if datetime.now() > expires_dt:
                            password_status = "Expirado"
                        else:
                            password_status = "Ativo"
                    else:
                        password_status = "Ativo"
                else:
                    password_status = "Sem senha"
                
                user_data.append({
                    'Usuário': username,
                    'Criado': created_str,
                    'Senha Temporária': temp_password if temp_password else "N/A",
                    'Expira': expires_str,
                    'Status': password_status
                })
            
            df = pd.DataFrame(user_data)
            
            # Display users table
            st.dataframe(df, use_container_width=True)
            
            # User actions section
            st.subheader("Ações de Usuário")
            
            # Get list of users for actions
            user_list = [user[0] for user in users]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Editar Usuário**")
                selected_user_edit = st.selectbox(
                    "Selecione o usuário para editar:",
                    user_list,
                    key="edit_user"
                )
                
                with st.form("edit_user_form"):
                    new_username_edit = st.text_input(
                        "Novo nome de usuário:", 
                        value=selected_user_edit,
                        key="new_username_edit"
                    )
                    edit_button = st.form_submit_button("Atualizar Usuário")
                
                if edit_button and new_username_edit:
                    if new_username_edit != selected_user_edit:
                        success, message = db.update_user(selected_user_edit, new_username_edit)
                        if success:
                            st.success(f"Usuário atualizado: '{selected_user_edit}' → '{new_username_edit}'")
                            st.rerun()
                        else:
                            st.error(f"Falha na atualização: {message}")
                    else:
                        st.warning("O novo nome de usuário é igual ao atual.")
            
            with col2:
                st.write("**Excluir Usuário**")
                selected_user_delete = st.selectbox(
                    "Selecione o usuário para excluir:",
                    user_list,
                    key="delete_user"
                )
                
                if st.button("Excluir Usuário", key="delete_button"):
                    if selected_user_delete == "admin":
                        st.error("Não é possível excluir o usuário admin!")
                    else:
                        st.info(f"Excluindo usuário '{selected_user_delete}' e todos os dados associados...")
                        
                        if db.delete_user(selected_user_delete):
                            st.success(f"Usuário '{selected_user_delete}' excluído com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"Falha ao excluir usuário '{selected_user_delete}'. O usuário pode não existir ou ser admin.")
                            
                            # Debug information
                            with st.expander("Informações de Debug"):
                                all_users = db.get_all_usernames()
                                st.write("Todos os usuários no banco de dados:")
                                for username, is_admin in all_users:
                                    st.write(f"- {username} (admin: {is_admin})")
            
            with col3:
                st.write("**Gerar Senha**")
                selected_user_password = st.selectbox(
                    "Selecione o usuário para senha:",
                    user_list,
                    key="password_user"
                )
                
                # Check if user already has a password
                user_info = next((user for user in users if user[0] == selected_user_password), None)
                has_password = user_info and user_info[2] and not user_info[4]
                
                if has_password:
                    st.warning(f"Usuário já possui senha ativa")
                
                if st.button("Gerar Senha", key="generate_password"):
                    new_password = db.generate_temp_password(selected_user_password)
                    st.success(f"Nova senha para {selected_user_password}: **{new_password}**")
                    st.info("Esta senha é válida por 1 semana e substitui qualquer senha existente.")
                    st.rerun()
            

        
        else:
            st.info("Nenhum usuário encontrado. Crie alguns usuários primeiro!")
    
    with tab2:
        # ASK Evaluation section
        st.subheader("Avaliação do Teste ASK")
        st.write("Interface de Avaliação do Gerente")
        
        # Get all ASK tests
        try:
            ask_tests = db.get_all_ask_tests_for_evaluation()
            
            if not ask_tests:
                st.info("Nenhum teste ASK encontrado para avaliação.")
            else:
                # Display test list
                st.subheader("Testes Disponíveis para Avaliação")
                
                for test in ask_tests:
                    test_id, username, score, completed_at, total_questions, evaluated_questions = test
                    
                    # Calculate evaluation progress
                    progress = (evaluated_questions / total_questions * 100) if total_questions > 0 else 0
                    
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**{username}** - {completed_at}")
                        st.write(f"Score: {score:.1f}")
                    
                    with col2:
                        st.write(f"Progresso: {evaluated_questions}/{total_questions}")
                    
                    with col3:
                        st.progress(progress / 100)
                    
                    with col4:
                        if st.button(f"Avaliar", key=f"eval_{test_id}"):
                            st.session_state.selected_test_id = test_id
                            st.rerun()
                
                # Evaluation interface
                if 'selected_test_id' in st.session_state:
                    test_id = st.session_state.selected_test_id
                    
                    try:
                        test_data = db.get_ask_test_for_evaluation(test_id)
                        
                        if test_data:
                            test_result = test_data['test_result']
                            answers = test_data['answers']
                            
                            username, test_type, score, answers_json, completed_at = test_result
                            
                            st.subheader(f"Avaliando: {username}")
                            st.write(f"**Data do Teste:** {completed_at}")
                            st.write(f"**Pontuação Atual:** {score:.1f}")
                            
                            # Load framework data for questions
                            try:
                                with open('framework.json', 'r', encoding='utf-8') as f:
                                    framework_data = json.load(f)
                                questions = framework_data.get('questions', [])
                                question_map = {q['id']: q for q in questions}
                            except:
                                st.error("Não foi possível carregar framework.json")
                                return
                            
                            # Load option sets
                            try:
                                with open('option_sets.json', 'r', encoding='utf-8') as f:
                                    option_sets = json.load(f)
                            except:
                                st.error("Não foi possível carregar option_sets.json")
                                return
                            
                            # Create overview table
                            st.subheader("Visão Geral das Perguntas")
                            
                            # Prepare table data
                            table_data = []
                            for answer in answers:
                                # Handle both old and new database formats
                                if len(answer) >= 8:  # New format with user_notes
                                    question_id, selected_options, user_rating, user_notes, manager_rating, manager_notes, evaluated_by, evaluated_at = answer
                                else:  # Old format without user_notes
                                    question_id, selected_options, user_rating, manager_rating, manager_notes, evaluated_by, evaluated_at = answer
                                    user_notes = ""  # Default empty string for old records
                                
                                question = question_map.get(question_id, {})
                                question_text = question.get('question', f'Question {question_id}')
                                pillar = question.get('pillar', 'Unknown')
                                category = question.get('category', 'Unknown')
                                
                                # Convert selected options to skill names
                                try:
                                    selected_options_list = json.loads(selected_options) if selected_options else []
                                    option_set_name = question.get('option_set', '')
                                    option_list = option_sets.get(option_set_name, [])
                                    selected_skills = [option_list[i] for i in selected_options_list if i < len(option_list)]
                                    selected_skills_text = ", ".join(selected_skills[:3]) + ("..." if len(selected_skills) > 3 else "")
                                except:
                                    selected_skills_text = f"Opções: {selected_options}"
                                
                                # Determine status
                                status = "Avaliado" if manager_rating and manager_rating > 0 else "Pendente"
                                
                                table_data.append({
                                    "ID da Pergunta": question_id,
                                    "Pergunta": question_text[:50] + "..." if len(question_text) > 50 else question_text,
                                    "Pilar": pillar,
                                    "Categoria": category,
                                    "Habilidades Selecionadas": selected_skills_text,
                                    "Avaliação do Usuário": f"{user_rating}/5",
                                    "Avaliação do Gerente": f"{manager_rating}/5" if manager_rating else "Não avaliado",
                                    "Status": status
                                })
                            
                            # Display metrics
                            total_questions = len(answers)
                            evaluated_questions = sum(1 for answer in answers if len(answer) >= 6 and answer[4] and answer[4] > 0)
                            progress_percentage = (evaluated_questions / total_questions * 100) if total_questions > 0 else 0
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total de Perguntas", total_questions)
                            with col2:
                                st.metric("Avaliadas", evaluated_questions)
                            with col3:
                                st.metric("Progresso", f"{progress_percentage:.1f}%")
                            
                            st.progress(progress_percentage / 100)
                            
                            # Display table
                            df = pd.DataFrame(table_data)
                            st.dataframe(df, use_container_width=True)
                            
                            # Question selection for detailed evaluation
                            st.subheader("Avaliação Detalhada da Pergunta")
                            
                            # Create question selector
                            question_ids = [answer[0] for answer in answers]
                            selected_question_id = st.selectbox(
                                "Selecione uma pergunta para avaliação detalhada:",
                                question_ids,
                                key="question_selector"
                            )
                            
                            # Show detailed question evaluation
                            if selected_question_id:
                                # Find the answer for selected question
                                selected_answer = next((answer for answer in answers if answer[0] == selected_question_id), None)
                                
                                if selected_answer:
                                    # Handle both old and new database formats
                                    if len(selected_answer) >= 8:  # New format with user_notes
                                        question_id, selected_options, user_rating, user_notes, manager_rating, manager_notes, evaluated_by, evaluated_at = selected_answer
                                    else:  # Old format without user_notes
                                        question_id, selected_options, user_rating, manager_rating, manager_notes, evaluated_by, evaluated_at = selected_answer
                                        user_notes = ""  # Default empty string for old records
                                    
                                    question = question_map.get(question_id, {})
                                    question_text = question.get('question', f'Question {question_id}')
                                    pillar = question.get('pillar', 'Unknown')
                                    category = question.get('category', 'Unknown')
                                    option_set_name = question.get('option_set', '')
                                    explanation = question.get('explanation', '')
                                    
                                    # Show evaluation status - only show as evaluated if manager_rating is not None and not 0
                                    if manager_rating and manager_rating > 0:
                                        st.success(f"**Question {question_id}** (Evaluated)")
                                    else:
                                        st.warning(f"**Question {question_id}** (Pending Evaluation)")
                                    
                                    st.write(f"**Pergunta:** {question_text}")
                                    st.write(f"**Pilar:** {pillar} | **Categoria:** {category}")
                                    st.write(f"**Conjunto de Opções:** {option_set_name}")
                                    st.write(f"**Explicação:** {explanation}")
                                    
                                    # Display selected skills
                                    try:
                                        selected_options_list = json.loads(selected_options) if selected_options else []
                                        option_list = option_sets.get(option_set_name, [])
                                        selected_skills = [option_list[i] for i in selected_options_list if i < len(option_list)]
                                        
                                        if selected_skills:
                                            st.write(f"**Habilidades Selecionadas ({len(selected_skills)}):**")
                                            
                                            # Display in 3 columns
                                            cols = st.columns(3)
                                            for i, skill in enumerate(selected_skills):
                                                col_idx = i % 3
                                                with cols[col_idx]:
                                                    st.write(f"• {skill}")
                                        else:
                                            st.write("**Habilidades Selecionadas:** Nenhuma")
                                    except Exception as e:
                                        st.write(f"**Opções Selecionadas:** {selected_options}")
                                        st.write(f"*Erro ao analisar opções: {e}*")
                                    
                                    st.write(f"**Autoavaliação do Usuário:** {user_rating}/5")
                                    
                                    if user_notes:
                                        st.write("**Observações do Usuário:**")
                                        st.info(user_notes)
                                    
                                    # Manager evaluation form
                                    st.markdown("---")
                                    st.write("**Avaliação do Gerente:**")
                                    
                                    new_manager_rating = st.selectbox(
                                        f"Avaliação do Gerente (Q{question_id})",
                                        [1, 2, 3, 4, 5],
                                        index=2,  # Default to 3
                                        key=f"manager_rating_{question_id}"
                                    )
                                    
                                    new_manager_notes = st.text_area(
                                        f"Observações do Gerente (Q{question_id})",
                                        value=manager_notes if manager_notes else "",
                                        placeholder="Adicione notas de avaliação...",
                                        key=f"manager_notes_{question_id}"
                                    )
                                    
                                    if st.button(f"Salvar Avaliação para Pergunta {question_id}", key=f"save_eval_{question_id}"):
                                        success = db.update_ask_answer_evaluation(
                                            test_id, question_id, new_manager_rating, 
                                            new_manager_notes, st.session_state['username']
                                        )
                                        
                                        if success:
                                            st.success(f"Avaliação salva com sucesso para Pergunta {question_id}!")
                                            st.info(f"Avaliação do Gerente: {new_manager_rating}/5 | Observações: {new_manager_notes[:50]}{'...' if len(new_manager_notes) > 50 else ''}")
                                            st.rerun()
                                        else:
                                            st.error("Falha ao salvar avaliação")
                                
                                # Back button
                                if st.button("Voltar à Lista de Testes"):
                                    del st.session_state.selected_test_id
                                    st.rerun()
                        else:
                            st.error("Teste não encontrado")
                            if st.button("Voltar à Lista de Testes"):
                                del st.session_state.selected_test_id
                                st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao carregar dados do teste: {e}")
                        if st.button("Voltar à Lista de Testes"):
                            del st.session_state.selected_test_id
                            st.rerun()
        except Exception as e:
            st.error(f"Erro ao carregar testes ASK: {e}")
    
    # Admin actions
    st.markdown("---")
    st.subheader("Ações de Administrador")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Atualizar Dados"):
            st.rerun()
    
    with col2:
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
