import streamlit as st
import json
import random
import matplotlib.pyplot as plt
import numpy as np
from database import Database

def load_ask_questions():
    """Load ASK test questions from framework.json and option_sets.json files"""
    try:
        # Load framework.json (metadata and questions)
        with open('framework.json', 'r', encoding='utf-8') as f:
            framework_data = json.load(f)
        
        # Load option_sets.json
        with open('option_sets.json', 'r', encoding='utf-8') as f:
            option_sets_data = json.load(f)
        
        # Combine the data
        combined_data = {
            "metadata": framework_data.get("metadata", {}),
            "questions": framework_data.get("questions", []),
            "option_sets": option_sets_data
        }
        
        return combined_data
        
    except FileNotFoundError as e:
        st.error(f"ASK test file not found: {e}")
        return {}
    except json.JSONDecodeError as e:
        st.error(f"Error parsing JSON: {e}")
        return {}

def convert_old_format_to_new(old_data):
    """Convert old JSON format to new format structure"""
    # Create new format structure
    new_data = {
        "metadata": {
            "pillars": ["Technical", "Product_Strategy", "Behavioral", "Value_Delivery"],
            "likert_scale": {
                "1": "Nenhuma experiência ainda",
                "2": "Básico / tutoriais", 
                "3": "Intermediário / pequenos projetos",
                "4": "Avançado / produção",
                "5": "Referência / mentoro outros"
            },
            "career_tracks": [
                {
                    "name": "Data Analyst",
                    "weights": {"Technical": 50, "Product_Strategy": 20, "Behavioral": 20, "Value_Delivery": 10},
                    "minimums": {"Technical": 60, "Product_Strategy": 40, "Behavioral": 30, "Value_Delivery": 20}
                }
            ]
        },
        "option_sets": {},
        "questions": []
    }
    
    # Convert old questions to new format
    for question_id, question_data in old_data.items():
        if isinstance(question_data, dict) and 'Pergunta' in question_data:
            # Extract options from old format
            options = []
            if 'Opcoes' in question_data:
                for option in question_data['Opcoes']:
                    if isinstance(option, dict) and 'texto' in option:
                        options.append(option['texto'])
            
            # Create option set name
            option_set_name = f"Set_{question_id}"
            new_data["option_sets"][option_set_name] = options
            
            # Create new question format
            new_question = {
                "id": int(question_id.replace('P', '')),
                "pillar": question_data.get('Pilar', 'Technical'),
                "category": question_data.get('Habilidade', 'General'),
                "question": question_data.get('Pergunta', ''),
                "explanation": "Converted from old format",
                "option_set": option_set_name,
                "user_rating": None,
                "manager_rating": None
            }
            new_data["questions"].append(new_question)
    
    return new_data

def calculate_ask_scores(answers, questions_data):
    """Calculate ASK test scores with separate career track and level determination"""
    
    # Extract metadata
    metadata = questions_data.get('metadata', {})
    career_tracks = metadata.get('career_tracks', [])
    
    # Default career track (first one)
    selected_track = career_tracks[0] if career_tracks else None
    
    # Calculate separate scores for user and manager evaluations
    user_pillar_scores = {}
    manager_pillar_scores = {}
    combined_pillar_scores = {}
    pillar_questions = {}
    
    # Group questions by pillar
    for question in questions_data.get('questions', []):
        pillar = question.get('pillar')
        if pillar not in pillar_questions:
            pillar_questions[pillar] = []
        pillar_questions[pillar].append(question)
    
    # Calculate scores for each pillar
    for pillar, questions in pillar_questions.items():
        user_pillar_total = 0
        manager_pillar_total = 0
        pillar_count = 0
        
        for question in questions:
            question_id = str(question.get('id'))
            if question_id in answers:
                answer_data = answers[question_id]
                
                # Get Likert ratings (convert 1-5 to 0-4)
                user_rating = answer_data.get('user_rating', 0) - 1  # Convert to 0-4
                manager_rating = answer_data.get('manager_rating', None)  # Keep as None if not evaluated
                
                # Calculate separate totals
                if user_rating > 0:
                    user_pillar_total += user_rating
                if manager_rating is not None and manager_rating > 0:
                    manager_pillar_total += manager_rating
                
                if user_rating > 0:
                    pillar_count += 1
        
        # Calculate separate pillar scores (0-100)
        if pillar_count > 0:
            user_pillar_scores[pillar] = (user_pillar_total / pillar_count) * 25  # Convert to 0-100
            manager_pillar_scores[pillar] = (manager_pillar_total / pillar_count) * 25  # Convert to 0-100
            # Combined score: if manager has evaluated, use average; otherwise use user score
            if manager_pillar_total > 0:
                combined_pillar_scores[pillar] = (user_pillar_scores[pillar] + manager_pillar_scores[pillar]) / 2
            else:
                combined_pillar_scores[pillar] = user_pillar_scores[pillar]
        else:
            user_pillar_scores[pillar] = 0
            manager_pillar_scores[pillar] = 0
            combined_pillar_scores[pillar] = 0
    
    # Calculate weighted scores for selected career track
    user_weighted_score = 0
    manager_weighted_score = 0
    combined_weighted_score = 0
    
    if selected_track:
        weights = selected_track.get('weights', {})
        for pillar in combined_pillar_scores.keys():
            weight = weights.get(pillar, 0)
            user_weighted_score += (user_pillar_scores[pillar] * weight) / 100
            manager_weighted_score += (manager_pillar_scores[pillar] * weight) / 100
            combined_weighted_score += (combined_pillar_scores[pillar] * weight) / 100
    
    # Determine career level based on combined scores
    career_level = determine_career_level(combined_weighted_score, combined_pillar_scores, selected_track)
    
    # Determine if meets current level
    meets_current_level = True
    if selected_track:
        minimums = selected_track.get('minimums', {})
        for pillar, score in combined_pillar_scores.items():
            minimum = minimums.get(pillar, 0)
            if score < minimum:
                meets_current_level = False
                break
    
    # Calculate delta to next level
    delta_to_next_level = {}
    if selected_track and not meets_current_level:
        minimums = selected_track.get('minimums', {})
        for pillar, score in combined_pillar_scores.items():
            minimum = minimums.get(pillar, 0)
            delta_to_next_level[pillar] = max(0, minimum - score)
    
    # Find top 5 gaps (skills with user_rating < 3)
    top5_gaps = []
    for question in questions_data.get('questions', []):
        question_id = str(question.get('id'))
        if question_id in answers:
            answer_data = answers[question_id]
            user_rating = answer_data.get('user_rating', 0)
            
            if user_rating < 3:  # Gap identified
                pillar = question.get('pillar')
                weight = selected_track.get('weights', {}).get(pillar, 0) if selected_track else 0
                gap_magnitude = 3 - user_rating
                
                top5_gaps.append({
                    'question_id': question_id,
                    'question': question.get('question'),
                    'pillar': pillar,
                    'user_rating': user_rating,
                    'gap_magnitude': gap_magnitude,
                    'pillar_weight': weight,
                    'priority_score': gap_magnitude * weight
                })
    
    # Sort by priority score and take top 5
    top5_gaps.sort(key=lambda x: x['priority_score'], reverse=True)
    top5_gaps = top5_gaps[:5]
    
    return {
        "user_pillar_scores": user_pillar_scores,
        "manager_pillar_scores": manager_pillar_scores,
        "combined_pillar_scores": combined_pillar_scores,
        "user_weighted_score": user_weighted_score,
        "manager_weighted_score": manager_weighted_score,
        "combined_weighted_score": combined_weighted_score,
        "career_level": career_level,
        "meets_current_level": meets_current_level,
        "delta_to_next_level": delta_to_next_level,
        "top5_gaps": top5_gaps,
        "selected_track": selected_track.get('name', 'Unknown') if selected_track else 'Unknown',
        "answers": answers
    }

def determine_career_level(weighted_score, pillar_scores, selected_track):
    """Determine career level based on scores and track requirements"""
    
    # Career level thresholds
    level_thresholds = {
        'Intern': 20,
        'Junior': 40,
        'Mid': 60,
        'Senior': 80,
        'Specialist': 90,
        'Manager': 85,  # Different track
        'PM': 80  # Different track
    }
    
    # Determine level based on weighted score
    if weighted_score >= level_thresholds['Specialist']:
        level = 'Specialist'
    elif weighted_score >= level_thresholds['Senior']:
        level = 'Senior'
    elif weighted_score >= level_thresholds['Mid']:
        level = 'Mid'
    elif weighted_score >= level_thresholds['Junior']:
        level = 'Junior'
    elif weighted_score >= level_thresholds['Intern']:
        level = 'Intern'
    else:
        level = 'Intern'
    
    # Check if meets minimum requirements for the level
    if selected_track:
        minimums = selected_track.get('minimums', {})
        for pillar, score in pillar_scores.items():
            minimum = minimums.get(pillar, 0)
            if score < minimum:
                # Downgrade level if doesn't meet minimums
                if level == 'Specialist':
                    level = 'Senior'
                elif level == 'Senior':
                    level = 'Mid'
                elif level == 'Mid':
                    level = 'Junior'
                elif level == 'Junior':
                    level = 'Intern'
                break
    
    return level

def create_polar_graph(pillar_scores, career_level):
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

def ask_test_page():
    st.title("Teste ASK - Avaliação de Habilidades & Conhecimento")
    
    # Check if user is logged in
    if not st.session_state.get('logged_in', False):
        st.error("Por favor, faça login primeiro para fazer o teste.")
        return
    
    # Initialize session state
    if 'ask_test_started' not in st.session_state:
        st.session_state.ask_test_started = False
    if 'ask_current_question' not in st.session_state:
        st.session_state.ask_current_question = 0
    if 'ask_answers' not in st.session_state:
        st.session_state.ask_answers = {}
    if 'ask_random_selection' not in st.session_state:
        st.session_state.ask_random_selection = None
    
    # Load questions
    questions_data = load_ask_questions()
    
    if not questions_data:
        st.error("Failed to load ASK test questions!")
        return
    
    # Get questions and metadata
    questions = questions_data.get('questions', [])
    option_sets = questions_data.get('option_sets', {})
    metadata = questions_data.get('metadata', {})
    likert_scale = metadata.get('likert_scale', {})
    
    if not st.session_state.ask_test_started:
        st.info("""
        **Instruções do Teste ASK:**
        
        Este teste avalia suas habilidades em 4 pilares:
        - **Technical**: Programação, ML, MLOps, Engenharia de Dados
        - **Product_Strategy**: Formulação de problemas, experimentos, métricas, roadmap
        - **Behavioral**: Comunicação, colaboração, mentoria, propriedade
        - **Value_Delivery**: Geração de valor, proatividade, liderança, escalabilidade
        
        **Como funciona:**
        - Selecione as habilidades que você tem experiência na lista
        - Avalie sua proficiência (escala 1-5) para autoavaliação e perspectiva do gerente
        - As pontuações determinam seu nível de carreira e identificam lacunas de habilidades
        
        **Pontuação:**
        - Cada pilar pontuado de 0-100 baseado em suas avaliações
        - Nível de carreira determinado por atender requisitos mínimos
        - Análise de lacunas mostra as 5 principais habilidades para desenvolver
        """)
        
        if st.button("Iniciar Teste ASK"):
            st.session_state.ask_test_started = True
            st.session_state.ask_current_question = 0
            st.session_state.ask_answers = {}
            st.session_state.ask_random_selection = None
            st.rerun()
    
    else:
        current_question_idx = st.session_state.ask_current_question
        
        # Check if we've completed all questions
        if current_question_idx >= len(questions):
            # Calculate and display results
            results = calculate_ask_scores(st.session_state.ask_answers, questions_data)
            
            # Save to database with proper structure for manager evaluation
            db = Database()
            test_result_id = db.save_ask_detailed_result(
                st.session_state.username,
                results["career_level"],
                results["combined_pillar_scores"],
                results["answers"]
            )
            
            st.success(f"Teste concluído e salvo! ID do Teste: {test_result_id}")
            
            # Display comprehensive results
            st.success(f"**Sua Trilha de Carreira: {results['selected_track']}**")
            st.write(f"**Nível de Carreira:** {results['career_level']}")
            st.write(f"**Atende ao Nível Atual:** {'Sim' if results['meets_current_level'] else 'Não'}")
            
            # Display separate scores
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Pontuação de Autoavaliação", f"{results['user_weighted_score']:.1f}")
            with col2:
                st.metric("Pontuação de Avaliação do Líder", f"{results['manager_weighted_score']:.1f}")
            with col3:
                st.metric("Pontuação Combinada", f"{results['combined_weighted_score']:.1f}")
            
            # Create and display polar graph
            st.subheader("Análise do Gráfico Polar")
            fig = create_polar_graph(results["combined_pillar_scores"], results["career_level"])
            st.pyplot(fig)
            
            # Pillar scores with visual representation
            st.subheader("Análise dos Pilares")
            
            # Display separate pillar scores
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Pontuações dos Pilares de Autoavaliação:**")
                for pillar, score in results["user_pillar_scores"].items():
                    progress = score / 100  # Normalize to 0-1
                    st.write(f"**{pillar}:** {score:.1f}")
                    st.progress(progress)
            
            with col2:
                st.write("**Pontuações dos Pilares de Avaliação do Líder:**")
                for pillar, score in results["manager_pillar_scores"].items():
                    progress = score / 100  # Normalize to 0-1
                    st.write(f"**{pillar}:** {score:.1f}")
                    st.progress(progress)
            
            # Combined scores
            st.subheader("🔄 Pontuações Combinadas dos Pilares")
            col1, col2 = st.columns(2)
            
            with col1:
                for pillar, score in results["combined_pillar_scores"].items():
                    progress = score / 100  # Normalize to 0-1
                    st.write(f"**{pillar}:** {score:.1f}")
                    st.progress(progress)
            
            with col2:
                # Show score range
                min_score = min(results["combined_pillar_scores"].values())
                max_score = max(results["combined_pillar_scores"].values())
                st.write(f"**Faixa de Pontuação:** {min_score:.1f} - {max_score:.1f}")
                st.write(f"**Pontuação Média:** {sum(results['combined_pillar_scores'].values()) / len(results['combined_pillar_scores']):.1f}")
            
            # Show strengths and weaknesses based on combined scores
            st.subheader("Pontos Fortes & Fraquezas")
            sorted_pillars = sorted(results["combined_pillar_scores"].items(), key=lambda x: x[1], reverse=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Principais Pontos Fortes:**")
                for pillar, score in sorted_pillars[:2]:
                    st.write(f"• {pillar}: {score:.1f}")
            
            with col2:
                st.write("**Áreas para Melhorar:**")
                for pillar, score in sorted_pillars[-2:]:
                    st.write(f"• {pillar}: {score:.1f}")
            
            # Progress to next level
            if results["delta_to_next_level"]:
                st.subheader("Progresso para o Próximo Nível")
                for pillar, delta in results["delta_to_next_level"].items():
                    if delta > 0:
                        st.write(f"**{pillar}:** Precisa de {delta:.1f} pontos a mais")
            
            # Top 5 gaps
            if results["top5_gaps"]:
                st.subheader("Top 5 Habilidades para Desenvolver")
                st.write("**Foque em seguida:**")
                for i, gap in enumerate(results["top5_gaps"], 1):
                    st.write(f"{i}. **{gap['question']}** ({gap['pillar']}) - Atual: {gap['user_rating']}/5")
            
            # Reset for new test
            if st.button("Fazer Teste Novamente"):
                st.session_state.ask_test_started = False
                st.session_state.ask_current_question = 0
                st.session_state.ask_answers = {}
                st.session_state.ask_random_selection = None
                st.rerun()
            
            return
        
        # Get current question
        question = questions[current_question_idx]
        question_id = str(question.get('id'))
        
        # Progress bar
        progress = (current_question_idx + 1) / len(questions)
        st.progress(progress)
        st.write(f"**Pergunta {current_question_idx + 1}/{len(questions)}**")
        
        # Display question
        st.subheader(f"📝 {question.get('question')}")
        st.write(f"**Pilar:** {question.get('pillar')}")
        st.write(f"**Categoria:** {question.get('category')}")
        st.write(f"**Explicação:** {question.get('explanation')}")
        
        # Get option set
        option_set_name = question.get('option_set')
        options = option_sets.get(option_set_name, [])
        
        # Get previous answers for this question
        previous_answers = st.session_state.ask_answers.get(question_id, {
            'selected_options': [],
            'user_rating': 3,
            'manager_rating': 3
        })
        
        # Display options as checkboxes in columns for better visualization
        st.write("**Selecione TODAS as habilidades que você tem experiência:**")
        
        # Determine number of columns based on number of options
        num_columns = 3 if len(options) > 15 else 2 if len(options) > 8 else 1
        
        # Create columns
        cols = st.columns(num_columns)
        
        selected_options = []
        for i, option in enumerate(options):
            col_idx = i % num_columns
            with cols[col_idx]:
                is_selected = st.checkbox(
                    option,
                    value=i in previous_answers.get('selected_options', []),
                    key=f"ask_option_{question_id}_{i}"
                )
                if is_selected:
                    selected_options.append(i)
        
        # Likert scale ratings
        st.subheader("Avaliações de Proficiência")
        
        st.write("**Sua Autoavaliação:**")
        user_rating = st.selectbox(
            "Avalie sua proficiência:",
            options=[1, 2, 3, 4, 5],
            index=previous_answers.get('user_rating', 3) - 1,
            format_func=lambda x: f"{x} - {likert_scale.get(str(x), 'Unknown')}",
            key=f"user_rating_{question_id}"
        )
        
        # User notes section
        st.subheader("Suas Observações")
        user_notes = st.text_area(
            f"Adicione seus comentários sobre esta área de habilidade (opcional):",
            value=previous_answers.get('user_notes', ''),
            placeholder="Compartilhe seus pensamentos, experiências ou contexto sobre essas habilidades...",
            key=f"user_notes_{question_id}"
        )
        
        # Save answers with proper structure for manager evaluation
        # Note: manager_rating should only be set by actual manager evaluation, not user self-assessment
        st.session_state.ask_answers[question_id] = {
            'selected_options': selected_options,
            'user_rating': user_rating,
            'user_notes': user_notes,
            'manager_rating': None,  # Will be set by manager evaluation
            'manager_notes': '',
            'evaluated_by': None,
            'evaluated_at': None
        }
        
        # Navigation buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if current_question_idx > 0:
                if st.button("Pergunta Anterior"):
                    st.session_state.ask_current_question -= 1
                    st.rerun()
        
        with col2:
            if st.button("Seleção Aleatória"):
                # Randomly select 3-8 options and set random ratings
                num_selections = random.randint(3, 8)
                random_options = random.sample(range(len(options)), num_selections)
                random_user_rating = random.randint(2, 5)
                random_manager_rating = random.randint(2, 5)
                
                st.session_state.ask_answers[question_id] = {
                    'selected_options': random_options,
                    'user_rating': random_user_rating,
                    'manager_rating': random_manager_rating
                }
                st.session_state.ask_random_selection = f"Selecionadas aleatoriamente {num_selections} habilidades e avaliações"
                st.session_state.ask_current_question += 1
                st.rerun()
        
        with col3:
            if current_question_idx < len(questions) - 1:
                if st.button("Próxima Pergunta"):
                    st.session_state.ask_current_question += 1
                    st.rerun()
        
        with col4:
            if current_question_idx == len(questions) - 1:
                if st.button("Enviar Teste"):
                    st.session_state.ask_current_question += 1
                    st.rerun()
        
        # Show random selection info
        if st.session_state.ask_random_selection:
            st.info(f"{st.session_state.ask_random_selection}")
