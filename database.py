import sqlite3
import bcrypt
from datetime import datetime, timedelta
import secrets
import string
import json
import hashlib

class Database:
    def __init__(self, db_path="app.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create passwords table for temporary passwords
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temp_passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_used BOOLEAN DEFAULT 0,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        
        # Create test results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                test_type TEXT NOT NULL,
                score INTEGER,
                answers TEXT,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        
        # Create ASK test answers table for detailed tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ask_test_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_result_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                selected_options TEXT,
                user_rating INTEGER,
                user_notes TEXT,
                manager_rating INTEGER,
                manager_notes TEXT,
                evaluated_by TEXT,
                evaluated_at TIMESTAMP,
                FOREIGN KEY (test_result_id) REFERENCES test_results (id),
                FOREIGN KEY (evaluated_by) REFERENCES users (username)
            )
        ''')
        
        # Add user_notes column if it doesn't exist (migration)
        try:
            cursor.execute('SELECT user_notes FROM ask_test_answers LIMIT 1')
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            cursor.execute('ALTER TABLE ask_test_answers ADD COLUMN user_notes TEXT')
            print("Added user_notes column to ask_test_answers table")
        
        # Create sessions table for persistent login
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_token TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        
        # Create admin user if not exists
        cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
        if not cursor.fetchone():
            admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)',
                         ('admin', admin_password.decode('utf-8'), True))
        
        conn.commit()
        conn.close()
    
    def verify_user(self, username, password):
        """Verify user login with either permanent or temporary password"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check permanent password first
        cursor.execute('SELECT password_hash, is_admin FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if user:
            password_hash, is_admin = user
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                conn.close()
                return True, is_admin
        
        # Check temporary password
        cursor.execute('''
            SELECT username FROM temp_passwords 
            WHERE username = ? AND password = ? AND expires_at > ? AND is_used = 0
        ''', (username, password, datetime.now()))
        
        temp_user = cursor.fetchone()
        conn.close()
        
        if temp_user:
            return True, False  # Temporary user is not admin
        return False, False
    
    def get_all_users(self):
        """Get all users for admin view"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.username, u.created_at, tp.password, tp.expires_at, tp.is_used
            FROM users u
            LEFT JOIN temp_passwords tp ON u.username = tp.username
            WHERE u.is_admin = 0
            ORDER BY u.username
        ''')
        
        users = cursor.fetchall()
        conn.close()
        return users
    
    def generate_temp_password(self, username):
        """Generate a temporary password for a user"""
        # Generate a random password
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(8))
        
        # Set expiration to 1 week from now
        expires_at = datetime.now() + timedelta(weeks=1)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete any existing password for this user
        cursor.execute('DELETE FROM temp_passwords WHERE username = ?', (username,))
        
        # Insert new temporary password
        cursor.execute('''
            INSERT INTO temp_passwords (username, password, expires_at)
            VALUES (?, ?, ?)
        ''', (username, password, expires_at))
        
        conn.commit()
        conn.close()
        
        return password
    
    def create_user(self, username):
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create user with a dummy password (they'll use temp password)
            dummy_password = bcrypt.hashpw('dummy'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                         (username, dummy_password.decode('utf-8')))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def delete_user(self, username):
        """Delete a user and all associated data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete user's test results first
            cursor.execute('DELETE FROM test_results WHERE username = ?', (username,))
            
            # Delete user's temporary passwords
            cursor.execute('DELETE FROM temp_passwords WHERE username = ?', (username,))
            
            # Delete the user (only if not admin)
            cursor.execute('DELETE FROM users WHERE username = ? AND is_admin = 0', (username,))
            user_deleted = cursor.rowcount
            
            # Commit the changes
            conn.commit()
            conn.close()
            
            # Return True if user was actually deleted
            return user_deleted > 0
            
        except Exception as e:
            conn.close()
            return False
    
    def update_user(self, old_username, new_username):
        """Update a user's username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if new username already exists
            cursor.execute('SELECT username FROM users WHERE username = ?', (new_username,))
            if cursor.fetchone():
                conn.close()
                return False, "Username already exists"
            
            # Update username in users table
            cursor.execute('UPDATE users SET username = ? WHERE username = ? AND is_admin = 0', 
                         (new_username, old_username))
            
            if cursor.rowcount > 0:
                # Update username in related tables
                cursor.execute('UPDATE test_results SET username = ? WHERE username = ?', 
                             (new_username, old_username))
                cursor.execute('UPDATE temp_passwords SET username = ? WHERE username = ?', 
                             (new_username, old_username))
                
                conn.commit()
                conn.close()
                return True, "User updated successfully"
            else:
                conn.close()
                return False, "User not found or is admin"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def save_test_result(self, username, test_type, score, answers):
        """Save test results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_results (username, test_type, score, answers)
            VALUES (?, ?, ?, ?)
        ''', (username, test_type, score, str(answers)))
        
        conn.commit()
        conn.close()
    
    def save_adti_detailed_result(self, username, primary_type, all_scores, answers):
        """Save detailed ADTI test results with all personality scores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store the primary type as the main score
        score = all_scores.get(primary_type, 0)
        
        # Create detailed result data
        detailed_result = {
            'primary_type': primary_type,
            'all_scores': all_scores,
            'answers': answers
        }
        
        cursor.execute('''
            INSERT INTO test_results (username, test_type, score, answers)
            VALUES (?, ?, ?, ?)
        ''', (username, 'ADTI', score, json.dumps(detailed_result)))
        
        conn.commit()
        conn.close()
    
    def save_ask_detailed_result(self, username, career_level, pillar_scores, answers):
        """Save detailed ASK test results with career level, pillar scores, and answers"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create detailed result object with separate scores
        detailed_result = {
            "career_level": career_level,
            "pillar_scores": pillar_scores,
            "answers": answers
        }
        
        # Calculate overall score (average of pillar scores)
        overall_score = sum(pillar_scores.values()) / len(pillar_scores) if pillar_scores else 0
        
        # Serialize to JSON
        answers_json = json.dumps(detailed_result)
        
        # Save to database
        cursor.execute('''
            INSERT INTO test_results (username, test_type, score, answers, completed_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, "ASK", overall_score, answers_json, datetime.now()))
        
        # Get the test result ID
        test_result_id = cursor.lastrowid
        
        # Save individual answers for manager evaluation
        for question_id, answer_data in answers.items():
            selected_options = json.dumps(answer_data.get('selected_options', []))
            user_rating = answer_data.get('user_rating')
            user_notes = answer_data.get('user_notes', '')
            manager_rating = answer_data.get('manager_rating')
            manager_notes = answer_data.get('manager_notes', '')
            evaluated_by = answer_data.get('evaluated_by')
            evaluated_at = answer_data.get('evaluated_at')
            
            cursor.execute('''
                INSERT INTO ask_test_answers 
                (test_result_id, question_id, selected_options, user_rating, user_notes,
                 manager_rating, manager_notes, evaluated_by, evaluated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (test_result_id, question_id, selected_options, user_rating, user_notes,
                  manager_rating, manager_notes, evaluated_by, evaluated_at))
        
        conn.commit()
        conn.close()
        
        return test_result_id
    
    def get_user_test_results(self, username):
        """Get test results for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT test_type, score, completed_at, answers
            FROM test_results
            WHERE username = ?
            ORDER BY completed_at DESC
        ''', (username,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_ask_test_for_evaluation(self, test_result_id):
        """Get ASK test answers for manager evaluation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the main test result
        cursor.execute('''
            SELECT username, test_type, score, answers, completed_at
            FROM test_results
            WHERE id = ?
        ''', (test_result_id,))
        
        test_result = cursor.fetchone()
        if not test_result:
            conn.close()
            return None
        
        # Format the completed_at field
        username, test_type, score, answers, completed_at = test_result
        
        # Handle completed_at formatting
        if isinstance(completed_at, str):
            try:
                # Try to parse the datetime string
                from datetime import datetime
                parsed_date = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M')
            except:
                formatted_date = completed_at
        else:
            formatted_date = completed_at.strftime('%Y-%m-%d %H:%M') if hasattr(completed_at, 'strftime') else str(completed_at)
        
        test_result = (username, test_type, score, answers, formatted_date)
        
        # Get individual answers (handle migration)
        try:
            cursor.execute('''
                SELECT question_id, selected_options, user_rating, user_notes,
                       manager_rating, manager_notes, evaluated_by, evaluated_at
                FROM ask_test_answers
                WHERE test_result_id = ?
                ORDER BY question_id
            ''', (test_result_id,))
        except sqlite3.OperationalError:
            # Fallback for old database format
            cursor.execute('''
                SELECT question_id, selected_options, user_rating,
                       manager_rating, manager_notes, evaluated_by, evaluated_at
                FROM ask_test_answers
                WHERE test_result_id = ?
                ORDER BY question_id
            ''', (test_result_id,))
        
        answers = cursor.fetchall()
        conn.close()
        
        return {
            'test_result': test_result,
            'answers': answers
        }
    
    def get_all_ask_tests_for_evaluation(self):
        """Get all ASK tests that need manager evaluation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT tr.id, tr.username, tr.score, tr.completed_at,
                   COUNT(ata.question_id) as total_questions,
                   COUNT(CASE WHEN ata.manager_rating IS NOT NULL THEN 1 END) as evaluated_questions
            FROM test_results tr
            LEFT JOIN ask_test_answers ata ON tr.id = ata.test_result_id
            WHERE tr.test_type = 'ASK'
            GROUP BY tr.id
            ORDER BY tr.completed_at DESC
        ''')
        
        tests = cursor.fetchall()
        conn.close()
        
        # Convert datetime strings to proper format if needed
        formatted_tests = []
        for test in tests:
            test_id, username, score, completed_at, total_questions, evaluated_questions = test
            
            # Handle completed_at formatting
            if isinstance(completed_at, str):
                try:
                    # Try to parse the datetime string
                    from datetime import datetime
                    parsed_date = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M')
                except:
                    formatted_date = completed_at
            else:
                formatted_date = completed_at.strftime('%Y-%m-%d %H:%M') if hasattr(completed_at, 'strftime') else str(completed_at)
            
            formatted_tests.append((test_id, username, score, formatted_date, total_questions, evaluated_questions))
        
        return formatted_tests
    
    def update_ask_answer_evaluation(self, test_result_id, question_id, manager_rating, manager_notes, evaluated_by):
        """Update manager evaluation for a specific answer and recalculate overall scores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update the specific answer
        cursor.execute('''
            UPDATE ask_test_answers
            SET manager_rating = ?, manager_notes = ?, evaluated_by = ?, evaluated_at = ?
            WHERE test_result_id = ? AND question_id = ?
        ''', (manager_rating, manager_notes, evaluated_by, datetime.now(), test_result_id, question_id))
        
        # Get all answers for this test to recalculate scores
        cursor.execute('''
            SELECT question_id, user_rating, manager_rating
            FROM ask_test_answers
            WHERE test_result_id = ?
            ORDER BY question_id
        ''', (test_result_id,))
        
        answers = cursor.fetchall()
        
        # Recalculate scores with manager evaluations
        if answers:
            # Load framework data for questions
            try:
                with open('framework.json', 'r', encoding='utf-8') as f:
                    import json
                    framework_data = json.load(f)
                questions = framework_data.get('questions', [])
                question_map = {q['id']: q for q in questions}
            except:
                # If framework.json not available, use basic calculation
                question_map = {}
            
            # Calculate new pillar scores
            pillar_scores = {}
            pillar_questions = {}
            
            # Group questions by pillar
            for question in questions:
                pillar = question.get('pillar')
                if pillar not in pillar_questions:
                    pillar_questions[pillar] = []
                pillar_questions[pillar].append(question)
            
            # Calculate scores for each pillar
            for pillar, pillar_question_list in pillar_questions.items():
                pillar_total = 0
                pillar_count = 0
                
                for question in pillar_question_list:
                    question_id = question.get('id')
                    
                    # Find corresponding answer
                    for answer in answers:
                        if answer[0] == question_id:
                            user_rating = answer[1] - 1 if answer[1] else 0  # Convert to 0-4
                            manager_rating = answer[2] - 1 if answer[2] else 0  # Convert to 0-4
                            
                            # Use manager rating if available, otherwise user rating
                            if manager_rating > 0:
                                rating = manager_rating
                            else:
                                rating = user_rating
                            
                            if rating > 0:
                                pillar_total += rating
                                pillar_count += 1
                            break
                
                # Calculate pillar score (0-100)
                if pillar_count > 0:
                    pillar_scores[pillar] = (pillar_total / pillar_count) * 25  # Convert to 0-100
                else:
                    pillar_scores[pillar] = 0
            
            # Calculate overall score
            overall_score = sum(pillar_scores.values()) / len(pillar_scores) if pillar_scores else 0
            
            # Update the test result with new scores
            detailed_result = {
                "career_level": "Updated",  # Will be recalculated
                "pillar_scores": pillar_scores,
                "answers": "Updated with manager evaluations"
            }
            
            cursor.execute('''
                UPDATE test_results
                SET score = ?, answers = ?
                WHERE id = ?
            ''', (overall_score, json.dumps(detailed_result), test_result_id))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def user_exists(self, username):
        """Check if a user exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        return user is not None
    
    def get_all_usernames(self):
        """Get all usernames for debugging"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT username, is_admin FROM users')
        users = cursor.fetchall()
        conn.close()
        
        return users
    
    def create_session(self, username, is_admin):
        """Create a new session for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate session token
        session_data = f"{username}_{datetime.now().timestamp()}_{secrets.token_hex(16)}"
        session_token = hashlib.sha256(session_data.encode()).hexdigest()
        
        # Set expiration to 24 hours from now
        expires_at = datetime.now() + timedelta(hours=24)
        
        try:
            cursor.execute('''
                INSERT INTO user_sessions (session_token, username, is_admin, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (session_token, username, is_admin, expires_at))
            
            conn.commit()
            conn.close()
            return session_token
        except Exception as e:
            conn.close()
            return None
    
    def validate_session(self, session_token):
        """Validate a session token and return user info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, is_admin FROM user_sessions 
            WHERE session_token = ? AND expires_at > ?
        ''', (session_token, datetime.now()))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {'username': result[0], 'is_admin': result[1]}
        return None
    
    def delete_session(self, session_token):
        """Delete a session token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))
        conn.commit()
        conn.close()
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM user_sessions WHERE expires_at <= ?', (datetime.now(),))
        conn.commit()
        conn.close()
    
    def fix_adti_primary_type_codes(self):
        """Fix ADTI test results that have full names instead of codes for primary_type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all ADTI results
        cursor.execute('SELECT id, answers FROM test_results WHERE test_type = "ADTI"')
        results = cursor.fetchall()
        
        # Define personality types mapping
        personality_types = {
            "Data Strategist": "DSTA",
            "Data Virtuoso": "DVRT", 
            "Data Logician": "DLOG",
            "Data Visionary": "DVIS",
            "Data Collaborator": "DCOL",
            "Data Supporter": "DSUP",
            "Data Advocate": "DADV",
            "Data Integrator": "DINT",
            "Data Commander": "DCOM",
            "Data Executive": "DEXE",
            "Data Innovator": "DINN",
            "Data Protagonist": "DPRO",
            "Data Creator": "DCRT",
            "Data Communicator": "DCOMM",
            "Data Entrepreneur": "DENT",
            "Data Activist": "DACT"
        }
        
        fixed_count = 0
        for result_id, answers_str in results:
            try:
                data = json.loads(answers_str)
                if isinstance(data, dict) and 'primary_type' in data and 'all_scores' in data:
                    old_primary_type = data['primary_type']
                    
                    # Check if it's a full name that needs to be converted to code
                    if old_primary_type in personality_types:
                        new_primary_type = personality_types[old_primary_type]
                        data['primary_type'] = new_primary_type
                        
                        # Update the score based on the correct primary type code
                        new_score = data['all_scores'].get(new_primary_type, 0)
                        
                        # Update the database
                        cursor.execute('''
                            UPDATE test_results 
                            SET score = ?, answers = ? 
                            WHERE id = ?
                        ''', (new_score, json.dumps(data), result_id))
                        
                        fixed_count += 1
                        print(f"Fixed result {result_id}: {old_primary_type} -> {new_primary_type}, score: {new_score}")
                        
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error processing result {result_id}: {e}")
                continue
        
        conn.commit()
        conn.close()
        print(f"Fixed {fixed_count} ADTI results")
        return fixed_count
