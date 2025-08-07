import streamlit as st
import json
from database import Database

def ask_evaluation_page():
    """Admin page for evaluating ASK tests"""
    st.title("Avaliação do Teste ASK")
    st.subheader("Interface de Avaliação do Gerente")
    
    db = Database()
    
    # Get all ASK tests
    try:
        ask_tests = db.get_all_ask_tests_for_evaluation()
        
        if not ask_tests:
            st.info("Nenhum teste ASK encontrado para avaliação.")
            return
    except Exception as e:
        st.error(f"Erro ao carregar testes ASK: {e}")
        return
    
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
                    
                    # Get selected skills names
                    selected_skills_text = "None"
                    if selected_options:
                        try:
                            selected_indices = json.loads(selected_options)
                            option_set_name = question.get('option_set', '')
                            if selected_indices and option_set_name in option_sets:
                                options_list = option_sets[option_set_name]
                                selected_skills = []
                                for index in selected_indices:
                                    if isinstance(index, int) and 0 <= index < len(options_list):
                                        selected_skills.append(options_list[index])
                                if selected_skills:
                                    selected_skills_text = ", ".join(selected_skills[:3])  # Show first 3 skills
                                    if len(selected_skills) > 3:
                                        selected_skills_text += f" (+{len(selected_skills)-3} more)"
                        except:
                            selected_skills_text = "Error parsing"
                    
                    # Evaluation status - only show as evaluated if manager_rating is not None and not 0
                    status = "✅ Evaluated" if manager_rating and manager_rating > 0 else "⚠️ Pending"
                    
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
                
                # Display table
                import pandas as pd
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True)
                
                # Evaluation progress
                total_questions = len(answers)
                # Calculate evaluated questions based on database format
                evaluated_questions = 0
                for answer in answers:
                    if len(answer) >= 8:  # New format
                        manager_rating = answer[4]  # manager_rating at index 4
                    else:  # Old format
                        manager_rating = answer[3]  # manager_rating at index 3
                    # Only count as evaluated if manager_rating is not None and greater than 0
                    if manager_rating is not None and manager_rating > 0:
                        evaluated_questions += 1
                progress_percentage = (evaluated_questions / total_questions * 100) if total_questions > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Perguntas", total_questions)
                with col2:
                    st.metric("Avaliadas", evaluated_questions)
                with col3:
                    st.metric("Progresso", f"{progress_percentage:.1f}%")
                
                st.progress(progress_percentage / 100)
                
                # Question selection for detailed evaluation
                st.subheader("Avaliação Detalhada da Pergunta")
                
                # Create question selector
                question_options = [f"Q{answer[0]} - {question_map.get(answer[0], {}).get('question', 'Unknown')[:50]}..." for answer in answers]
                selected_question_idx = st.selectbox(
                    "Selecione uma pergunta para avaliação detalhada:",
                    options=range(len(answers)),
                    format_func=lambda x: question_options[x],
                    key="question_selector"
                )
                
                # Show detailed evaluation for selected question
                if selected_question_idx is not None:
                    answer = answers[selected_question_idx]
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
                    explanation = question.get('explanation', '')
                    option_set_name = question.get('option_set', '')
                    
                    st.markdown("---")
                    
                    # Show evaluation status - only show as evaluated if manager_rating is not None and not 0
                    if manager_rating and manager_rating > 0:
                        st.success(f"**Question {question_id}** (Evaluated)")
                    else:
                        st.warning(f"**Question {question_id}** (Pending Evaluation)")
                    
                    st.write(f"**Pergunta:** {question_text}")
                    st.write(f"**Pilar:** {pillar} | **Categoria:** {category}")
                    st.write(f"**Conjunto de Opções:** {option_set_name}")
                    st.write(f"**Explicação:** {explanation}")
                    
                    # Display selected options
                    if selected_options:
                        try:
                            selected_indices = json.loads(selected_options)
                            if selected_indices and option_set_name in option_sets:
                                options_list = option_sets[option_set_name]
                                selected_skills = []
                                
                                for index in selected_indices:
                                    if isinstance(index, int) and 0 <= index < len(options_list):
                                        selected_skills.append(options_list[index])
                                    else:
                                        selected_skills.append(f"Skill {index}")
                                
                                if selected_skills:
                                    st.write(f"**Habilidades Selecionadas ({len(selected_skills)}):**")
                                    cols = st.columns(3)
                                    for i, skill_name in enumerate(selected_skills):
                                        col_idx = i % 3
                                        with cols[col_idx]:
                                            st.write(f"• {skill_name}")
                                else:
                                    st.write("**Habilidades Selecionadas:** Nenhuma")
                            else:
                                st.write("**Habilidades Selecionadas:** Nenhuma habilidade selecionada")
                        except Exception as e:
                            st.write(f"**Opções Selecionadas:** {selected_options}")
                            st.write(f"*Erro ao analisar opções: {e}*")
                    
                    # Display user rating and notes
                    st.write(f"**Autoavaliação do Usuário:** {user_rating}/5")
                    
                    if user_notes:
                        st.write("**Observações do Usuário:**")
                        st.info(user_notes)
                    
                    # Manager evaluation
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        new_manager_rating = st.selectbox(
                            f"Avaliação do Gerente (Q{question_id})",
                            options=[1, 2, 3, 4, 5],
                            index=(manager_rating - 1) if manager_rating else 2,
                            key=f"rating_{test_id}_{question_id}"
                        )
                    
                    with col2:
                        new_manager_notes = st.text_area(
                            f"Observações do Gerente (Q{question_id})",
                            value=manager_notes or "",
                            placeholder="Adicione notas de avaliação...",
                            key=f"notes_{test_id}_{question_id}"
                        )
                    
                    # Save evaluation for this specific question only
                    if st.button(f"Salvar Avaliação para Pergunta {question_id}", key=f"save_{test_id}_{question_id}"):
                        success = db.update_ask_answer_evaluation(
                            test_id, question_id, new_manager_rating, 
                            new_manager_notes, st.session_state.get('username', 'admin')
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
