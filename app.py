import streamlit as st
from interview_agent import InterviewAgent
# import json
from openai import OpenAI
from u_profile import generate_user_profile, clean_profile, save_profile
import firebase_admin
from firebase_admin import credentials, firestore
from twin import generate_recommendations, load_user_profile

# fetching openai key 
openai_key = st.secrets["api"]["key"]

# Convert Streamlit secrets into dict
firebase_config = st.secrets["firebase"]
# setting up firebase
cred = credentials.Certificate(dict(firebase_config))
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()







# Initializing session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "interview_agent" not in st.session_state:
    st.session_state.interview_agent = InterviewAgent(openai_key)
    st.session_state.follow_up_count = 0
    st.session_state.conversation_saved = False  

# Custom CSS
st.markdown("""<style>
    .stChatInput textarea { min-height: 150px; }
    .stMarkdown { padding: 1rem; border-radius: 0.5rem; }
    .assistant-message { background-color: #f0f2f6; }
</style>""", unsafe_allow_html=True)

# Displaying title
st.markdown('<h1 class="title" style="text-align: center; font-size: 80px; color: #E041B1;">Prism</h1>', unsafe_allow_html=True)

# Loading user profile if avaialble
profile = load_user_profile()

# Defining Sidebar
with st.sidebar:
    st.image("logo trans.png", width=200) # for displaying logo
    # Custom CSS to style the button
    st.markdown("""
    <style>
        .stButton button {
            background-color: #2c2c2e;  /* Lighter grey-blue shade */
            color: white;
            font-size: 16px;
            padding: 8px 20px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .stButton button:hover {
            background-color: #95A5A6;  /* Even lighter grey-blue for hover */
            box-shadow: none;  /* Removed shadow for a more subtle hover effect */
        }

        .stButton button:active {
            background-color: #BDC3C7;  /* Lighter grey when active */
        }
    </style>
""", unsafe_allow_html=True)

    if st.button("Delete Profile"):
    # fetching user profile from database for deleting
        doc_ref = db.collection("profiles").document("current_user")

        # Deleting the document
        doc_ref.delete()
        st.rerun()




if profile:
    # Defining digital twin layout
    # st.markdown('<h1 class="title" style="text-align: center; font-size: 80px; color: #E041B1;">Prism</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 18px;">Lets Prism to get personalized recommendations</p>', unsafe_allow_html=True)



    query = st.text_input('Write Your Query....')
    if st.button('Lets Prism'):
        recs = generate_recommendations(profile, query)

        st.markdown(
        f"""
        <div style="background-color: #2e2e2e; padding: 1em; border-radius: 8px;">
            <div style="background-color: #f0f0f0; color: #000; padding: 1em; border-radius: 8px;">
                {recs}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    


# # Defining Sidebar
# with st.sidebar:
#     st.image("logo trans.png", width=200) # for displaying logo


# if profile == None:
else:
    # Defining main interview agent UI
    
    st.markdown('<p style="text-align: center; font-size: 18px;">Create your digital twin and get personalized recommendations</p>', unsafe_allow_html=True)

    # Displaying chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Defining main Interview Logic
    agent = st.session_state.interview_agent

    if agent.current_phase < len(agent.phases):
        current_phase = agent.phases[agent.current_phase]
        
        if agent.current_question < len(current_phase["questions"]):
            current_q = current_phase["questions"][agent.current_question]
            
            # Displaying current question if not already shown
            if not any(msg["content"] == current_q for msg in st.session_state.messages):
                st.session_state.messages.append({"role": "assistant", "content": current_q})
                st.rerun()

            # Getting user response
            user_input = st.chat_input("Type your answer here...")
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                # Storing response
                agent.conversation.append({
                    "question": current_q,
                    "answer": user_input,
                    "phase": current_phase["name"]
                })
                
                # Checking response quality
                if agent._needs_elaboration(user_input):
                    if st.session_state.follow_up_count < 2:
                        follow_up = agent._generate_follow_up(current_q, user_input)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": f"Follow-up: {follow_up}"
                        })
                        st.session_state.follow_up_count += 1
                    else:
                        agent.current_question += 1
                        st.session_state.follow_up_count = 0
                else:
                    agent.current_question += 1
                    st.session_state.follow_up_count = 0

                # Saving progress and rerun
                agent._save_progress()
                st.rerun()
        else:
            # Moving to next phase
            agent.current_phase += 1
            agent.current_question = 0
            st.rerun()
    else:
        if not st.session_state.get("conversation_saved", False):
        # Saving entire conversation to Firebase database
            conversation_data = agent.conversation 
            db.collection("conversations").document("full_conversation").set({"conversation": conversation_data})

            st.session_state.conversation_saved = True
            st.rerun()


        # Generating the profile
        if st.session_state.get("conversation_saved", False):
            with st.spinner('User profile is being created...'):
                # Fetching the conversation from Firebase
                doc_ref = db.collection("conversations").document("full_conversation")
                doc = doc_ref.get()

                if doc.exists:
                    interview_data = doc.to_dict().get("conversation")
                    print("Loaded conversation from Firebase")
                else:
                    print("No conversation found in Firebase")
                    interview_data = {}

                # Generating and cleaning the profile
                profile = generate_user_profile(interview_data)
                cleaned_profile = clean_profile(profile)

                # Saving the profile to Firebase
                save_profile(cleaned_profile)

                st.success("Interview complete! User Profile generated and saved!")
                st.rerun()


 