import streamlit as st
from supabase import create_client, Client

# ✅ Supabase credentials
SUPABASE_URL = "https://ekxnjobnjnkajjeuxxge.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVreG5qb2Juam5rYWpqZXV4eGdlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ0NjUwNTksImV4cCI6MjA3MDA0MTA1OX0.lExIqsvHPtbI0L3gfa-X24tA_TRvKydbfjtKwf7RmnE"
if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'signup_success' not in st.session_state:
    st.session_state.signup_success = False
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ Session setup
if 'user' not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

# ✅ Signup function
def signup():
    st.title("Sign Up")

    # ✅ Show success message only once after rerun
    if st.session_state.get("signup_success", False):
        st.success("✅ Signup successful! Now log in.")
        return

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    full_name = st.text_input("Full Name")
    role = st.selectbox("Select Role", ["student", "admin"])

    if st.button("Create Account"):
        try:
            # Step 1: Create user in Supabase Auth
            auth_res = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            user = auth_res.user
            if not user:
                st.error("❌ Signup failed: Auth response has no user.")
                return

            user_id = user.id

            # Step 2: Insert user into the users table
            insert_response = supabase.table("users").insert({
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "role": role
            }).execute()

            if insert_response.data:
                st.session_state.signup_success = True
                st.rerun()
            else:
                st.error("❌ Signup failed: Insert returned no data.")

        except Exception as e:
            st.error(f"❌ Signup failed: {e}")




# ✅ Login function
def login():
    st.title("Log In")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            auth_res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            user = auth_res.user

            if user:
                st.session_state.user = user
                st.session_state.user_id = user.id  # ✅ REQUIRED for dashboard access

                # Fetch user role from DB
                user_data = supabase.table("users").select("*").eq("id", user.id).execute()

                if user_data.data and len(user_data.data) > 0:
                    st.session_state.role = user_data.data[0]["role"]
                else:
                    # If user not in 'users' table, insert with default 'student' role
                    default_role = "student"
                    supabase.table("users").insert({
                        "id": user.id,
                        "email": email,
                        "full_name": "Unknown",
                        "role": default_role
                    }).execute()
                    st.session_state.role = default_role

                st.session_state.logged_in = True
                st.success(f"✅ Logged in as {st.session_state.role}.")

                # 🚀 Go directly to respective dashboard
                if st.session_state.role == "admin":
                    admin_dashboard()
                elif st.session_state.role == "student":
                    student_dashboard()

                return

            else:
                st.error("❌ Login failed: invalid credentials.")

        except Exception as e:
            st.error(f"❌ Login error: {e}")




import uuid
import streamlit as st
import streamlit as st
from datetime import datetime

def admin_dashboard():
    st.title("📊 Admin Dashboard")

    tabs = st.tabs(["📄 Exams", "➕ Add Question", "📝 View Feedback"])

    # -----------------------
    # Exams Tab
    # -----------------------
    with tabs[0]:
        st.header("Exams List")

        # Create Exam form
        with st.form("create_exam_form"):
            exam_title = st.text_input("Exam Title")
            exam_description = st.text_area("Exam Description")
            duration = st.number_input("Duration (minutes)", min_value=1, step=1)
            start_time = st.date_input("Start Date")
            start_time_time = st.time_input("Start Time")
            end_time = st.date_input("End Date")
            end_time_time = st.time_input("End Time")
            submitted = st.form_submit_button("Create Exam")

            if submitted:
                from datetime import datetime
                start_datetime = datetime.combine(start_time, start_time_time)
                end_datetime = datetime.combine(end_time, end_time_time)

                data = {
                    "title": exam_title,
                    "description": exam_description,
                    "duration_minutes": duration,
                    "start_time": start_datetime.isoformat(),
                    "end_time": end_datetime.isoformat(),
                    "created_by": st.session_state.user.id,
                    "created_at": datetime.utcnow().isoformat()
                }
                res = supabase.table("exams").insert(data).execute()
                if res.data:
                    st.success("✅ Exam created successfully!")
                else:
                    st.error(f"❌ Error creating exam: {res}")

        exams_data = supabase.table("exams").select("*").execute()
        if exams_data.data:
            for exam in exams_data.data:
                st.write(f"**{exam['title']}** - {exam['description']}")
        else:
            st.info("No exams found.")

    # -----------------------
    # Add Question Tab
    # -----------------------
    with tabs[1]:
        st.header("Add a Question")
        exam_id = st.text_input("Exam ID")
        question_text = st.text_area("Question Text")
        options = []
        for i in range(4):
            options.append(st.text_input(f"Option {chr(65+i)}"))
        correct_answer = st.selectbox("Correct Answer", options)
        q_type = st.selectbox("Question Type", ["mcq", "msq", "true/false", "text"])

        if st.button("Add Question"):
            options_dict = {chr(65+i): opt for i, opt in enumerate(options)}
            supabase.table("questions").insert({
                "exam_id": exam_id,
                "question_text": question_text,
                "options": options_dict,
                "correct_answer": correct_answer,
                "type": q_type,
                "created_by": st.session_state.user.id
            }).execute()
            st.success("Question added successfully!")

    # -----------------------
    # View Feedback Tab
    # -----------------------
    with tabs[2]:
        st.header("Student Feedback")
        try:
            feedback_data = supabase.table("feedback").select("*").order("submitted_at", desc=True).execute()
            if feedback_data.data:
                for fb in feedback_data.data:
                    st.markdown(f"**Student ID:** {fb['student_id']}")
                    st.markdown(f"**Exam ID:** {fb['exam_id']}")
                    st.markdown(f"**Feedback:** {fb['feedback_text'] if 'feedback_text' in fb else fb.get('message', '')}")
                    st.markdown(f"**Submitted At:** {fb['submitted_at']}")
                    st.markdown("---")
            else:
                st.info("No feedback submitted yet.")
        except Exception as e:
            st.error(f"❌ Error fetching feedback: {e}")


# ✅ Dashboards
import streamlit as st
from datetime import datetime
import uuid

# ✅ Student Dashboard
import streamlit as st
from datetime import datetime
import uuid

# ✅ Helper: Check if exam already taken
def has_taken_exam(student_id, exam_id):
    result = supabase.table("results").select("*").eq("student_id", student_id).eq("exam_id", exam_id).execute()
    return len(result.data) > 0

# ✅ Student Dashboard
def student_dashboard():
    if "user_id" not in st.session_state:
        st.warning("⚠️ You must be logged in.")
        return

    st.title("🎓 Student Dashboard")

    student_id = st.session_state.user_id

    # Fetch available exams
    exams_res = supabase.table("exams").select("*").execute()
    exams = exams_res.data if exams_res.data else []

    # Fetch past results
    results_res = supabase.table("results").select("*").eq("student_id", student_id).execute()
    past_results = {r["exam_id"]: r for r in results_res.data} if results_res.data else {}

    # If user clicked Start Exam previously
    if "selected_exam_id" in st.session_state:
        take_exam(st.session_state.selected_exam_id)
        return

    if not exams:
        st.info("📭 No exams available at the moment.")
        return

    for exam in exams:
        exam_id = exam["id"]
        st.subheader(exam["title"])
        st.write(exam["description"])
        st.write(f"⏳ Duration: {exam['duration_minutes']} minutes")

        if exam_id in past_results:
            result = past_results[exam_id]
            st.success(f"✅ You already completed this exam. Score: {result['total_score']}")
            if "feedback" in result and result["feedback"]:
                st.write(f"💬 Your feedback: {result['feedback']}")
        else:
            if st.button(f"Start Exam: {exam['title']}", key=f"start_{exam_id}"):
                st.session_state.selected_exam_id = exam_id
                st.rerun()


def take_exam(exam_id):
    st.subheader("📄 Exam in Progress")

    # ✅ Ensure user is logged in
    if "user_id" not in st.session_state:
        st.error("❌ You must be logged in to take the exam.")
        return

    # Fetch questions for the exam
    questions_res = supabase.table("questions").select("*").eq("exam_id", exam_id).execute()
    questions = questions_res.data

    if not questions:
        st.warning("⚠ No questions available for this exam.")
        return

    # Store answers in session state
    if "answers" not in st.session_state:
        st.session_state.answers = {}

    # Display each question with friendly numbering
    for idx, q in enumerate(questions, start=1):
        st.write(f"**Question {idx}:** {q['question_text']}")

        options = q["options"] if isinstance(q["options"], list) else json.loads(q["options"])

        selected_answer = st.radio(
            f"Select your answer for Question {idx}:",
            options,
            key=f"q_{q['id']}"
        )

        # Store the answer internally mapped to the real UUID
        st.session_state.answers[q['id']] = selected_answer

    # Submit button
    if st.button("✅ Submit Exam"):
        total_score = 0
        for q in questions:
            correct_answer_letter = q["correct_answer"]  # Stored as A, B, C...
            options = q["options"] if isinstance(q["options"], list) else json.loads(q["options"])

            # Get the correct answer text from the letter
            correct_answer_text = options[ord(correct_answer_letter.upper()) - 65]

            student_answer = st.session_state.answers.get(q['id'])

            # Compare student answer to correct answer text
            if student_answer and student_answer.strip().lower() == correct_answer_text.strip().lower():
                total_score += 1

            # Save individual answer
            supabase.table("answers").insert({
                "student_id": st.session_state.user_id,
                "exam_id": exam_id,
                "question_id": q['id'],
                "answer_text": student_answer,
                "submitted_at": datetime.utcnow().isoformat()
            }).execute()

        # Save result
        supabase.table("results").insert({
            "student_id": st.session_state.user_id,
            "exam_id": exam_id,
            "total_score": total_score,
            "evaluation_status": "completed",
            "evaluated_at": datetime.utcnow().isoformat()
        }).execute()

        st.success(f"🎉 Exam submitted! Your score: {total_score} / {len(questions)}")

        # Clear stored answers
        st.session_state.answers = {}

        # Prevent retake by storing a flag
        st.session_state.exam_taken = True

        # Feedback section
        feedback = st.text_area("💬 Provide your feedback about this exam:")
        if st.button("Submit Feedback"):
            supabase.table("feedback").insert({
                "student_id": st.session_state.user_id,
                "exam_id": exam_id,
                "feedback_text": feedback,
                "submitted_at": datetime.utcnow().isoformat()
            }).execute()
            st.success("✅ Feedback submitted. Thank you!")

        st.rerun()


# ✅ Evaluation Logic
def evaluate_exam(exam_id, answers, questions):
    total_score = 0
    max_score = len(questions)
    review = []

    for q in questions:
        qid = q["id"]
        qtype = q["type"]
        options = q.get("options", [])
        correct = q["correct_answer"]
        selected = answers.get(qid)

        # Convert correct letter (like "A") to full text (like "António Guterres")
        correct_text = None
        if isinstance(correct, str) and correct in ["A", "B", "C", "D"]:
            index = ["A", "B", "C", "D"].index(correct)
            if index < len(options):
                correct_text = options[index]
            else:
                correct_text = correct  # fallback
        else:
            correct_text = correct

        # Match based on type
        if isinstance(selected, list):
            is_correct = set(selected) == set(correct_text if isinstance(correct_text, list) else [correct_text])
        else:
            is_correct = selected == correct_text

        review.append(
            f"- **Q: {q['question_text']}**\n  - Your Answer: {selected}\n  - Correct Answer: {correct_text} {'✅' if is_correct else '❌'}"
        )

        if is_correct:
            total_score += 1

        supabase.table("answers").insert({
            "id": str(uuid.uuid4()),
            "student_id": st.session_state.user.id,
            "exam_id": exam_id,
            "question_id": qid,
            "answer_text": selected,
            "submitted_at": datetime.utcnow().isoformat()
        }).execute()

    supabase.table("results").insert({
        "id": str(uuid.uuid4()),
        "student_id": st.session_state.user.id,
        "exam_id": exam_id,
        "total_score": total_score,
        "evaluation_status": "evaluated",
        "evaluated_at": datetime.utcnow().isoformat()
    }).execute()

    return total_score, max_score, review


def show_past_results(student_id):
    st.subheader("📊 Your Past Exam Results")

    # Fetch all exams and results
    exams_data = supabase.table("exams").select("id, title").execute().data
    results_data = supabase.table("results").select("*").eq("student_id", student_id).execute().data

    if not results_data:
        st.info("ℹ️ You haven't completed any exams yet.")
        return

    exam_title_map = {exam["id"]: exam["title"] for exam in exams_data}

    for result in results_data:
        exam_title = exam_title_map.get(result["exam_id"], "Unknown Exam")
        score = result["total_score"]
        st.success(f"✅ **{exam_title}** — Score: {score}")

def main():
    st.sidebar.title("🧠 Exam App")

    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        page = st.sidebar.radio("Go to", ["Login", "Signup"])
        if page == "Login":
            login()
        else:
            signup()
    else:
        page = st.sidebar.radio("Go to", ["Dashboard", "Logout"])

        if page == "Dashboard":
            if st.session_state.role == "admin":
                admin_dashboard()
            elif st.session_state.role == "student":
                student_dashboard()
            else:
                st.warning("⚠️ Unrecognized role.")
        elif page == "Logout":
            st.session_state.clear()
            st.warning("You have logged out. Please refresh the page.")  # No rerun, just ask user to refresh




main() 