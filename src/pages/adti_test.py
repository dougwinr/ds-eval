import streamlit as st
from database import Database
import json
import os
import random

def load_adti_questions():
    """Load questions from the JSON file"""
    try:
        with open('adti_test.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data[0]  # The questions are in the first element
    except Exception as e:
        st.error(f"Error loading questions: {e}")
        return {}

def adti_test_page():
    st.title("Teste ADTI - Indicador de Tipo de Equipes de IA & Dados")
    st.markdown("---")
    
    # Check if user is logged in
    if not st.session_state.get('logged_in', False):
        st.error("Por favor, faça login primeiro para fazer o teste.")
        return
    
    # Initialize database
    db = Database()
    username = st.session_state['username']
    
    # Load questions from JSON file
    questions_data = load_adti_questions()
    
    # Convert JSON structure to our format with Likert scale
    questions = []
    for key, question_data in questions_data.items():
        if key.startswith('P') and question_data.get('Dicotomias') and len(question_data['Dicotomias']) == 2:
            questions.append({
                "question": question_data['Pergunta'],
                "options": [
                    "Discordo totalmente",
                    "Discordo", 
                    "Indiferente (neutro)",
                    "Concordo",
                    "Concordo totalmente"
                ],
                "dicotomies": question_data['Dicotomias'],
                "category": f"question_{len(questions) + 1}"
            })
    
    # Define the 16 ADTI personality types with their characteristics
    personality_types = {
        # Technical Personalities
        "DSTA": {
            "type": "Data Strategist",
            "description": "Analytical, organized, pragmatic. Solves business problems based on data and evidence. Focuses on strategic planning and structured approaches.",
            "score": 85,
            "category": "Technical",
            "strengths": ["Strategic thinking", "Business acumen", "Analytical approach", "Structured methodology"],
            "ideal_role": "Senior Data Scientist, Data Strategy Consultant"
        },
        "DVRT": {
            "type": "Data Virtuoso", 
            "description": "Practical, adaptable, specialist in techniques and tools. Optimizes data pipelines and focuses on technical execution.",
            "score": 80,
            "category": "Technical",
            "strengths": ["Technical expertise", "Practical problem-solving", "Tool mastery", "Execution focus"],
            "ideal_role": "Data Engineer, Infrastructure Specialist"
        },
        "DLOG": {
            "type": "Data Logician",
            "description": "Investigative, logical, creative in solving complex technical problems. Excels at algorithmic thinking and systematic analysis.",
            "score": 82,
            "category": "Technical",
            "strengths": ["Logical reasoning", "Algorithmic thinking", "Systematic analysis", "Technical creativity"],
            "ideal_role": "ML Engineer, Research Scientist"
        },
        "DVIS": {
            "type": "Data Visionary",
            "description": "Imaginative, idealistic, disruptive. Innovator in research and experimentation. Focuses on future possibilities and creative solutions.",
            "score": 78,
            "category": "Technical",
            "strengths": ["Innovation", "Future thinking", "Creative solutions", "Research focus"],
            "ideal_role": "AI Research Scientist, Innovation Specialist"
        },
        
        # Collaborative Personalities
        "DCOL": {
            "type": "Data Collaborator",
            "description": "Supports colleagues, creates harmony, works well in teams. Excellent at building relationships and facilitating collaboration.",
            "score": 75,
            "category": "Collaborative",
            "strengths": ["Team collaboration", "Relationship building", "Harmony creation", "Support facilitation"],
            "ideal_role": "Data Analyst, Team Facilitator"
        },
        "DSUP": {
            "type": "Data Supporter",
            "description": "Empathetic, offers emotional and technical support, creates visualizations. Focuses on helping others succeed.",
            "score": 72,
            "category": "Collaborative",
            "strengths": ["Empathy", "Support provision", "Visualization skills", "Team support"],
            "ideal_role": "Data Visualization Specialist, Support Analyst"
        },
        "DADV": {
            "type": "Data Advocate",
            "description": "Defends data quality and governance, aligned with rules and ethics. Ensures responsible data practices.",
            "score": 70,
            "category": "Collaborative",
            "strengths": ["Governance focus", "Ethical awareness", "Quality assurance", "Compliance knowledge"],
            "ideal_role": "Data Governance Analyst, Compliance Specialist"
        },
        "DINT": {
            "type": "Data Integrator",
            "description": "Integrates systems and teams, ensures data flow. Connects different parts of the organization.",
            "score": 73,
            "category": "Collaborative",
            "strengths": ["System integration", "Cross-team coordination", "Data flow management", "Bridge building"],
            "ideal_role": "Integration Engineer, Solution Architect"
        },
        
        # Leadership Personalities
        "DCOM": {
            "type": "Data Commander",
            "description": "Assertive leader, results-oriented, focused on deadlines and decisions. Drives projects to completion.",
            "score": 88,
            "category": "Leadership",
            "strengths": ["Assertive leadership", "Results focus", "Decision making", "Project driving"],
            "ideal_role": "Technical Lead, Engineering Manager"
        },
        "DEXE": {
            "type": "Data Executive",
            "description": "Organized, efficient, focuses on goal alignment and results. Manages data initiatives strategically.",
            "score": 85,
            "category": "Leadership",
            "strengths": ["Strategic management", "Goal alignment", "Process optimization", "Resource organization"],
            "ideal_role": "Data Product Manager, Data Director"
        },
        "DINN": {
            "type": "Data Innovator",
            "description": "Explores emerging technologies, disruptive and strategic. Pushes boundaries and explores new possibilities.",
            "score": 80,
            "category": "Leadership",
            "strengths": ["Innovation focus", "Emerging tech exploration", "Disruptive thinking", "Strategic vision"],
            "ideal_role": "Innovation Specialist, Emerging Tech Lead"
        },
        "DPRO": {
            "type": "Data Protagonist",
            "description": "Charismatic, drives data-driven culture. Inspires others and communicates vision effectively.",
            "score": 83,
            "category": "Leadership",
            "strengths": ["Charismatic leadership", "Culture building", "Vision communication", "Inspiration"],
            "ideal_role": "Head of Analytics, Strategic Director"
        },
        
        # Creative and Entrepreneurial Personalities
        "DCRT": {
            "type": "Data Creator",
            "description": "Creative, enthusiastic, develops new solutions and data products. Innovates and builds new capabilities.",
            "score": 77,
            "category": "Creative",
            "strengths": ["Creative problem-solving", "Product development", "Innovation", "Enthusiasm"],
            "ideal_role": "Creative Data Scientist, Product Developer"
        },
        "DCOMM": {
            "type": "Data Communicator",
            "description": "Translates data into impactful stories, excellent at storytelling. Makes complex data accessible.",
            "score": 75,
            "category": "Creative",
            "strengths": ["Storytelling", "Communication skills", "Data translation", "Engagement"],
            "ideal_role": "Data Storyteller, Communication Specialist"
        },
        "DENT": {
            "type": "Data Entrepreneur",
            "description": "Fast, opportunistic, creates innovation and data-driven businesses. Moves quickly and seizes opportunities.",
            "score": 78,
            "category": "Creative",
            "strengths": ["Opportunity recognition", "Fast execution", "Business creation", "Risk taking"],
            "ideal_role": "Data Startup Founder, Business Developer"
        },
        "DACT": {
            "type": "Data Activist",
            "description": "Ethical, defends privacy, justice, social impact in data. Ensures responsible and fair data use.",
            "score": 72,
            "category": "Creative",
            "strengths": ["Ethical awareness", "Privacy advocacy", "Social impact", "Responsible practices"],
            "ideal_role": "Ethics Specialist, Privacy Advocate"
        }
    }
    
    # Initialize session state for test
    if 'adti_test_started' not in st.session_state:
        st.session_state.adti_test_started = False
    if 'adti_answers' not in st.session_state:
        st.session_state.adti_answers = {}
    if 'adti_test_completed' not in st.session_state:
        st.session_state.adti_test_completed = False
    if 'adti_current_question' not in st.session_state:
        st.session_state.adti_current_question = 0
    if 'adti_random_selection' not in st.session_state:
        st.session_state.adti_random_selection = None
    
    # Start test button
    if not st.session_state.adti_test_started and not st.session_state.adti_test_completed:
        st.info("Este teste contém 60 perguntas para determinar seu tipo de personalidade em equipes de IA e Dados usando uma escala Likert de 5 pontos.")
        st.markdown("**Escala:** 1 = Discordo totalmente, 2 = Discordo, 3 = Indiferente, 4 = Concordo, 5 = Concordo totalmente")
        st.markdown("**O teste identificará seu tipo de personalidade primário entre 16 tipos diferentes em equipes de dados e IA.**")
        if st.button("Iniciar Teste ADTI"):
            st.session_state.adti_test_started = True
            st.session_state.adti_current_question = 0
            st.session_state.adti_answers = {}
            st.session_state.adti_random_selection = None
            st.rerun()
    
    # Test interface
    elif st.session_state.adti_test_started and not st.session_state.adti_test_completed:
        current_question_idx = st.session_state.adti_current_question
        
        # Ensure we don't exceed the question limit
        if current_question_idx >= len(questions):
            st.error("Erro: Índice da pergunta excede o número total de perguntas.")
            st.session_state.adti_test_completed = True
            st.rerun()
        
        st.subheader("Pergunta {}/{}".format(current_question_idx + 1, len(questions)))
        
        # Progress bar
        progress = current_question_idx / len(questions)
        st.progress(progress)
        
        question = questions[current_question_idx]
        
        st.write(f"**{question['question']}**")
        
        # Show random selection feedback if available
        if st.session_state.adti_random_selection and current_question_idx == len(st.session_state.adti_answers) - 1:
            st.info(f"Selecionado aleatoriamente: **{st.session_state.adti_random_selection}**")
            st.session_state.adti_random_selection = None  # Clear after showing
        
        # Display Likert scale options
        # Get previous answer if it exists, otherwise default to neutral
        previous_answer = st.session_state.adti_answers.get(current_question_idx, 2)
        selected_option = st.radio(
            "Selecione seu nível de concordância:",
            question['options'],
            index=previous_answer,  # Use previous answer or default to "Indiferente (neutro)"
            key=f"adti_question_{current_question_idx}"
        )
        
        # Show Likert scale visualization
        st.markdown("**Escala (1-5 → 0-1000):**")
        st.markdown("1️⃣ **Discordo totalmente** | 2️⃣ **Discordo** | 3️⃣ **Indiferente** | 4️⃣ **Concordo** | 5️⃣ **Concordo totalmente**")
        st.markdown("*As pontuações são normalizadas para escala 0-1000 para fácil comparação*")
        
        # Navigation buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            # Previous button (disabled on first question)
            if st.button("Pergunta Anterior", disabled=current_question_idx == 0):
                if current_question_idx > 0:
                    st.session_state.adti_answers[current_question_idx] = question['options'].index(selected_option)
                    st.session_state.adti_current_question = current_question_idx - 1
                    st.rerun()
        
        with col2:
            # Random answer button
            if st.button("Resposta Aleatória", disabled=current_question_idx == len(questions) - 1):
                # Generate random answer (0-4 for the 5 options)
                random_answer = random.randint(0, 4)
                st.session_state.adti_answers[current_question_idx] = random_answer
                st.session_state.adti_current_question = current_question_idx + 1
                st.session_state.adti_random_selection = question['options'][random_answer]
                st.rerun()
        
        with col3:
            # Next button (disabled on last question)
            if st.button("Próxima Pergunta", disabled=current_question_idx == len(questions) - 1):
                st.session_state.adti_answers[current_question_idx] = question['options'].index(selected_option)
                st.session_state.adti_current_question = current_question_idx + 1
                st.rerun()
        
        with col4:
            # Submit button (only enabled on last question)
            if st.button("Enviar Teste", disabled=current_question_idx != len(questions) - 1):
                st.session_state.adti_answers[current_question_idx] = question['options'].index(selected_option)
                st.session_state.adti_test_completed = True
                st.rerun()
    
    # Show results
    elif st.session_state.adti_test_completed:
        st.subheader("Resultados do Teste ADTI")
        
        # Calculate personality type based on answers
        personality_type, all_scores = calculate_personality_type(st.session_state.adti_answers, questions, personality_types)
        
        # Display primary result
        st.success(f"Seu Tipo Primário de Equipe de IA & Dados: **{personality_type['type']}**")
        st.info(f"**{personality_type['description']}**")
        
        # Show score range information
        min_score = min(all_scores.values())
        max_score = max(all_scores.values())
        st.info(f"📊 **Faixa de Pontuação:** {min_score:.1f} - {max_score:.1f} (escala 0-1000)")
        
        # Show top 5 and least 5 personalities
        st.subheader("Análise Detalhada de Personalidade")
        
        # Sort personalities by score
        sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        top_5 = sorted_scores[:5]
        least_5 = sorted_scores[-5:]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top 5 Correspondências de Personalidade:**")
            for i, (code, score) in enumerate(top_5, 1):
                personality = personality_types[code]
                st.markdown(f"{i}. **{personality['type']}** ({code}) - Pontuação: {score:.1f}")
                st.markdown(f"   *{personality['description'][:100]}...*")
        
        with col2:
            st.markdown("**Menores 5 Correspondências de Personalidade:**")
            for i, (code, score) in enumerate(least_5, 1):
                personality = personality_types[code]
                st.markdown(f"{i}. **{personality['type']}** ({code}) - Pontuação: {score:.1f}")
                st.markdown(f"   *{personality['description'][:100]}...*")
        
        # Show detailed breakdown by category
        st.subheader("Análise por Categoria")
        
        # Group by category
        category_scores = {}
        for code, score in all_scores.items():
            category = personality_types[code]['category']
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append((code, score))
        
        # Display category insights
        for category, scores in category_scores.items():
            avg_score = sum(score for _, score in scores) / len(scores)
            max_score = max(scores, key=lambda x: x[1])
            st.write(f"**{category}:** Pontuação média: {avg_score:.1f}, Maior: {personality_types[max_score[0]]['type']} ({max_score[1]:.1f})")
        
        # Show strengths and ideal role for primary type
        st.subheader("Seus Pontos Fortes & Papel Ideal")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Seus Pontos Fortes Principais:**")
            for strength in personality_type['strengths']:
                st.markdown(f"• {strength}")
        
        with col2:
            st.markdown("**Papel Ideal:**")
            st.markdown(f"**{personality_type['ideal_role']}**")
        
        # Save detailed results to database
        # Find the primary type code from the personality_types dictionary
        primary_type_code = None
        for code, ptype in personality_types.items():
            if ptype['type'] == personality_type['type']:
                primary_type_code = code
                break
        
        if primary_type_code is None:
            # Fallback: use the first key if not found
            primary_type_code = list(personality_types.keys())[0]
        
        db.save_adti_detailed_result(username, primary_type_code, all_scores, st.session_state.adti_answers)
        
        # Reset button
        if st.button("Fazer Teste Novamente"):
            st.session_state.adti_test_started = False
            st.session_state.adti_answers = {}
            st.session_state.adti_test_completed = False
            st.session_state.adti_current_question = 0
            st.session_state.adti_random_selection = None
            st.rerun()
    
    # Navigation
    st.markdown("---")
    if st.button("Voltar ao Início"):
        st.session_state.page = "home"
        st.rerun()

def calculate_personality_type(answers, questions, personality_types):
    """Calculate personality type based on answers using the ADTI framework with Likert scale"""
    
    # Calculate scores for each personality type based on dicotomies and Likert scale
    type_scores = {code: 0.0 for code in personality_types.keys()}
    
    for q_idx, answer in answers.items():
        question = questions[q_idx]
        if 'dicotomies' in question and len(question['dicotomies']) == 2:
            # Convert Likert scale (0-4) to weighted scores
            # 0 = Strongly Disagree, 1 = Disagree, 2 = Neutral, 3 = Agree, 4 = Strongly Agree
            likert_value = answer + 1  # Convert 0-4 to 1-5 scale
            
            # Calculate weighted scores for each dichotomy
            # First dichotomy gets positive weight, second gets negative weight
            first_dichotomy = question['dicotomies'][0]
            second_dichotomy = question['dicotomies'][1]
            
            # Simplified weight calculation for better 0-1000 conversion
            if likert_value == 1:  # Strongly Disagree
                type_scores[second_dichotomy] += 2.0  # Strong negative
            elif likert_value == 2:  # Disagree
                type_scores[second_dichotomy] += 1.0  # Negative
            elif likert_value == 3:  # Neutral
                type_scores[first_dichotomy] += 0.5   # Slight positive
                type_scores[second_dichotomy] += 0.5   # Slight positive
            elif likert_value == 4:  # Agree
                type_scores[first_dichotomy] += 1.0    # Positive
            elif likert_value == 5:  # Strongly Agree
                type_scores[first_dichotomy] += 2.0    # Strong positive
    
    # Calculate maximum possible score for each personality type
    # Count how many questions each personality type can receive points from
    personality_question_counts = {code: 0 for code in personality_types.keys()}
    
    for q_idx, answer in answers.items():
        question = questions[q_idx]
        if 'dicotomies' in question and len(question['dicotomies']) == 2:
            first_dichotomy = question['dicotomies'][0]
            second_dichotomy = question['dicotomies'][1]
            personality_question_counts[first_dichotomy] += 1
            personality_question_counts[second_dichotomy] += 1
    
    # Debug: Print question counts for each personality
    print(f"Debug - Questions per personality type:")
    for code, count in personality_question_counts.items():
        print(f"  {code}: {count} questions")
    
    # Debug: Print raw scores before normalization
    print(f"Debug - Raw scores before normalization:")
    for code, score in type_scores.items():
        print(f"  {code}: {score:.1f}")
    
    # Normalize each score to 0-100 scale based on individual maximums
    for code in type_scores:
        # Calculate maximum possible score for this personality type
        # Each question can contribute up to 2.0 points (Strongly Agree/Disagree)
        max_possible_for_type = personality_question_counts[code] * 2.0
        
        # Ensure score is non-negative
        score = max(0, type_scores[code])
        
        # Normalize to 0-100 scale based on this type's maximum, then multiply by 10
        if max_possible_for_type > 0:
            type_scores[code] = (score / max_possible_for_type) * 100 * 10
        else:
            type_scores[code] = 0
    
    # Ensure all scores are bounded between 0 and 1000 (after multiplying by 10)
    for code in type_scores:
        type_scores[code] = max(0, min(1000, type_scores[code]))
    
    # Debug: Print normalized scores
    print(f"Debug - Normalized scores (0-1000 scale):")
    for code, score in type_scores.items():
        max_for_type = personality_question_counts[code] * 2.0
        print(f"  {code}: {score:.1f} (max possible: {max_for_type * 10:.1f})")
    
    # Find the personality type with the highest score
    max_score = max(type_scores.values())
    max_types = [code for code, score in type_scores.items() if score == max_score]
    
    # Return the primary personality type (first if tied) and all scores
    primary_type = max_types[0]
    
    return personality_types[primary_type], type_scores

def get_category_insight(category, avg_score):
    """Get insight for each category"""
    insights = {
        "technical_planning": {
            0: "Prefers strategic planning",
            1: "Prefers immediate execution"
        },
        "technical_execution": {
            0: "Comfortable with step-by-step execution",
            1: "Prefers strategic overview"
        },
        "technical_focus": {
            0: "Focuses on metrics and KPIs",
            1: "Focuses on technical processes"
        },
        "team_collaboration": {
            0: "Strong team collaborator",
            1: "More independent worker"
        },
        "leadership_style": {
            0: "Natural leader and decision maker",
            1: "Prefers supportive role"
        },
        "creative_innovation": {
            0: "Creative and innovative thinker",
            1: "More practical and systematic"
        },
        "entrepreneurial_spirit": {
            0: "Entrepreneurial and opportunity-driven",
            1: "More cautious and ethical-focused"
        }
    }
    
    if category in insights:
        score_key = int(avg_score)
        if score_key in insights[category]:
            return insights[category][score_key]
    
    return f"Moderate preference (score: {avg_score:.1f})"
