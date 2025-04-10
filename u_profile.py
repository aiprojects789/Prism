import json
import openai
import os
from openai import OpenAI
from firebase_admin import credentials, firestore
import firebase_admin
import streamlit as st


firebase_config = st.secrets["firebase"]


# Setting up Firebase setup
cred = credentials.Certificate(dict(firebase_config))
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()



# fetching api key 
openai_key = st.secrets["api"]["key"]

# Defining logic for generating profile
def generate_user_profile(interview_data):
    """
    Uses GPT-4 to create a natural user profile from interview data.
    Focuses on extracting key insights rather than rigid structure.
    """
    prompt = f"""
    Analyze this interview data and extract key information to create a comprehensive user profile.
    Structure the output in JSON format with these characteristics:
    
    1. Include only sections with available data
    2. Use natural groupings (e.g., life story, values, preferences)
    3. Prioritize concrete facts over assumptions
    4. Keep summaries concise but meaningful
    
    Interview Data:
    {json.dumps(interview_data)}
    
    Return ONLY valid JSON (no commentary):
    """

    
    # Setting up LLM
    client = OpenAI(api_key=openai_key)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You're a biographer extracting key user insights from interviews."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
    
# Defining function for cleaning the profile    
def clean_profile(profile_text):
    """Ensures the output is valid JSON"""
    try:
        return json.dumps(json.loads(profile_text), indent=2)
    except json.JSONDecodeError:
        # Fallback if GPT adds commentary
        start = profile_text.find('{')
        end = profile_text.rfind('}') + 1
        return json.dumps(json.loads(profile_text[start:end]), indent=2)

# Defining function for saving the profile
def save_profile(profile_json, collection="profiles", doc_id="current_user"):
    """Saves the user profile JSON to Firebase Firestore"""
    try:
        # Converting JSON string to Python dict
        profile_data = json.loads(profile_json)
        db.collection(collection).document(doc_id).set(profile_data)
        print(f"Profile saved to Firebase (collection: {collection}, doc: {doc_id})")
    except Exception as e:
        print(f"Failed to save profile: {e}")



if __name__ == "__main__":
    # Fetching the conversation from database
    doc_ref = db.collection("conversations").document("full_conversation")
    doc = doc_ref.get()

    if doc.exists:
        interview_data = doc.to_dict().get("conversation")
        print("Loaded conversation from Firebase")
    else:
        print("No conversation found in Firebase")
        interview_data = {}
    
    # 2. Generating profile
    print("Generating profile...")
    profile = generate_user_profile(interview_data)
    cleaned_profile = clean_profile(profile)
    
    # 3. Saving result
    save_profile(cleaned_profile)
    