import json
import openai
import os
from openai import OpenAI
from firebase_admin import credentials, firestore
import firebase_admin
import streamlit as st
from collections import defaultdict

# Load Firebase credentials from Streamlit secrets
firebase_config = st.secrets["firebase"]

# Initialize Firebase
cred = credentials.Certificate(dict(firebase_config))
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Load OpenAI API key
openai_key = st.secrets["api"]["key"]


# Function to summarize a specific phase
def generate_phase_summary(phase, data):
    """
    Generates a summary/profile from a specific phase of interview data using GPT-4.
    """
    prompt = f"""
    Create a structured JSON summary for the following interview phase: "{phase}".
    Summarize the key ideas, values, stories, and personal characteristics discussed.
    Use clear groupings like background, personality traits, preferences, life lessons, etc.
    Return only valid JSON without any extra commentary.

    Interview Data:
    {json.dumps(data, indent=2)}
    """

    client = OpenAI(api_key=openai_key)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": "You are a professional profile summarizer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


# Function to break data by phase and summarize each
# def generate_full_profile_by_phase(interview_data):
#     """
#     Splits the full interview data by phase and summarizes each separately.
#     Then combines all phase summaries into one full profile.
#     """
#     phase_data = defaultdict(list)

#     # Step 1: Group entries by phase
#     for item in interview_data:
#         phase = item.get("phase", "Miscellaneous")
#         phase_data[phase].append(item)

#     # Step 2: Summarize each phase
#     full_profile = {}
#     for phase, entries in phase_data.items():
#         print(f"Summarizing phase: {phase}")
#         phase_summary_text = generate_phase_summary(phase, entries)

#         try:
#             phase_summary_json = json.loads(phase_summary_text)
#         except json.JSONDecodeError:
#             # Try to extract just the JSON part
#             start = phase_summary_text.find('{')
#             end = phase_summary_text.rfind('}') + 1
#             phase_summary_json = json.loads(phase_summary_text[start:end])

#         full_profile[phase] = phase_summary_json

#     return json.dumps(full_profile, indent=2)




def generate_full_profile_by_phase(interview_data, chunk_size=4):
    """
    Splits interview data by phase, chunks large phases, summarizes each chunk,
    and combines summaries into a full profile.
    """
    phase_data = defaultdict(list)
    for item in interview_data:
        phase = item.get("phase", "Miscellaneous")
        phase_data[phase].append(item)

    full_profile = {}

    for phase, entries in phase_data.items():
        print(f"Summarizing phase: {phase}")

        # Chunk long phases
        chunked_summaries = []
        for i in range(0, len(entries), chunk_size):
            chunk = entries[i:i + chunk_size]
            print(f"  Summarizing chunk {i//chunk_size + 1} of {phase}...")
            try:
                summary_text = generate_phase_summary(phase, chunk)
                summary_json = json.loads(summary_text)
            except json.JSONDecodeError:
                start = summary_text.find('{')
                end = summary_text.rfind('}') + 1
                summary_json = json.loads(summary_text[start:end])
            chunked_summaries.append(summary_json)

        # Combine chunk summaries into a single summary for the phase
        full_profile[phase] = {
            f"part_{idx+1}": chunk for idx, chunk in enumerate(chunked_summaries)
        }

    return json.dumps(full_profile, indent=2)




# Save final profile to Firestore
def save_profile(profile_json, collection="profiles", doc_id="current_user"):
    """Saves the user profile JSON to Firebase Firestore"""
    try:
        profile_data = json.loads(profile_json)
        db.collection(collection).document(doc_id).set(profile_data)
        print(f"Profile saved to Firebase (collection: {collection}, doc: {doc_id})")
    except Exception as e:
        print(f"Failed to save profile: {e}")


# Main logic
if __name__ == "__main__":
    # Fetch conversation data from Firestore
    doc_ref = db.collection("conversations").document("full_conversation")
    doc = doc_ref.get()

    if doc.exists:
        interview_data = doc.to_dict().get("conversation")
        print("Loaded conversation from Firebase")
    else:
        print("No conversation found in Firebase")
        interview_data = []

    # Generate full profile from phase-wise summaries
    print("Generating profile...")
    cleaned_profile = generate_full_profile_by_phase(interview_data)

    # Save the profile
    save_profile(cleaned_profile)
