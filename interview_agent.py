import json
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
import streamlit as st

# Fetching api key
api_key = st.secrets["api"]["key"]

# Defining llm
def llm_bot(api_key):
    llm = ChatOpenAI(
            openai_api_key=api_key,
            model="gpt-4",
            temperature=0.3,
            max_tokens=200)
    return llm


# Defining main interview agent logic
class InterviewAgent:
    def __init__(self, api_key):
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            model="gpt-4",
            temperature=0.3,
            max_tokens=200
        )
        self.phases = self._load_question_structure()
        self.conversation = []
        self.current_phase = 0
        self.current_question = 0
        self.follow_up_depth = 0

    def _load_question_structure(self):
        """Load the complete interview structure"""

        return [
            {
                "name": "Foundational Understanding",
                "instructions": ("Please answer the following questions as openly and descriptively as possible. "
                                 "Think about specific examples, feelings, and the 'why' behind your answers. "
                                 "The AI will use this information to build a comprehensive understanding of you to generate personalized recommendations. "
                                 "There are no right or wrong answers."),
                "questions": [
                    "Life Narrative: Tell me the story of your life, starting from where you feel is important. Touch upon key phases like your childhood, education, significant relationships (family, friends, partners), major life events, and career path. What moments stand out as particularly formative or defining?",
                    # "Core Values: What principles or values are most important to you in life (e.g., honesty, creativity, security, adventure, connection, independence, learning, community)? How do these values typically guide your decisions or how you spend your time?",
                    # "Personality & Self-Perception: How would you describe your personality to someone who doesn't know you? What do others typically say about you? What aspects of your personality are you most proud of, and are there any you find challenging?",
                    # "Significant Experiences: Describe a few experiences (positive or negative) that have significantly shaped who you are today or how you view the world. What did you learn from them?",
                    # "Sources of Joy & Fulfillment: What activities, interactions, or states of being genuinely bring you joy, satisfaction, or a sense of purpose?",
                    # "Dealing with Challenges: Think about a time you faced a significant challenge or stress. How did you cope? What are your typical strategies for dealing with stress or adversity?",
                    # "Social Connections: Describe the important relationships in your life currently. How do you typically spend time with these people? How do their perspectives or preferences influence you, if at all?"
                ]
            },
            {
                "name": "Daily Life, Habits & Preferences",
                "instructions": "Now, please describe your daily life, routines, habits, and preferences.",
                "questions": [
                    "Typical Routines: Describe a typical weekday and a typical weekend for you. What are the anchors of your routine? Where is there flexibility? How do you balance responsibilities and leisure?",
                    # "Learning & Curiosity: Are you typically curious about learning new things or trying new experiences? What topics or skills have recently captured your interest? How do you usually go about learning or exploring them?",
                    # "Risk & Comfort Zone: How do you generally feel about taking risks or stepping outside your comfort zone, whether it's trying a new food, traveling somewhere unfamiliar, or starting a new hobby? Please provide an example.",
                    # "Decision-Making Style: When faced with choices (like where to eat, what movie to watch, where to travel), how do you typically decide? Are you more analytical, impulsive, influenced by others, reliant on reviews, etc.?",
                    # "Atmosphere & Environment: Think about the physical environments where you feel most comfortable, energized, or relaxed (e.g., bustling cityscapes, quiet nature, cozy indoors, minimalist spaces, vibrant cafes). What elements contribute to that feeling?"
                ]
            },
            {
                "name": "Domain-Specific Exploration",
                "instructions": "Please answer the following questions by linking your answers to your values, experiences, and personality where possible.",
                "questions": [
                    # Movies & TV Section
                    "Movies & TV: Describe a movie or TV show that deeply resonated with you. What was it about the story, characters, themes, or style that connected with you?",
                    # "Movies & TV: What kind of mood are you usually in when you decide to watch something? Are you looking for escape, intellectual stimulation, emotional connection, or background noise?",
                    # "Movies & TV: Are there particular actors, directors, genres, or themes you consistently find yourself drawn to or actively avoiding? Why?",
                    # "Movies & TV: How do you typically discover new movies or shows to watch?",
                    # Music Section
                    # "Music: Describe the role music plays in your life. When and where do you usually listen?",
                    # "Music: Tell me about a song, artist, or concert experience that was particularly memorable or meaningful. What feelings did it evoke?",
                    # "Music: How does music affect your mood or energy levels? Do you seek out different types of music for different situations (e.g., working, relaxing, exercising)?",
                    # "Music: How do you discover new music?",
                    # Books & Reading Section
                    # "Books & Reading: What role does reading play in your life? What kind of books do you typically gravitate towards?",
                    # "Books & Reading: Describe a book that changed your perspective or stayed with you long after you finished it. What made it impactful?",
                    # "Books & Reading: When and where do you typically read? What kind of reading experience do you prefer (e.g., immersive, quick reads, challenging material)?",
                    # "Books & Reading: How do you find new books to read?",
                    # Food & Dining Section
                    # "Food & Dining: Describe your general philosophy or approach to food. Is it primarily fuel, pleasure, social connection, or creative expression?",
                    # "Food & Dining: Tell me about a truly memorable dining experience (at home or out). What made it special – the food, the company, the setting, the occasion?",
                    # "Food & Dining: When you choose a restaurant, what factors are most important (e.g., cuisine type, price, atmosphere, reviews, convenience, novelty)?",
                    # "Food & Dining: Are there cuisines, ingredients, or types of food you particularly love, dislike, or are curious to try? Any dietary preferences or restrictions?",
                    # Travel Section
                    # "Travel: What does travel mean to you? What motivates you to travel (or perhaps keeps you from traveling)?",
                    # "Travel: Describe a trip or travel experience that was particularly fulfilling or eye-opening. What aspects did you enjoy most (e.g., relaxation, adventure, cultural immersion, learning, food, nature)?",
                    # "Travel: What kind of pace and style do you prefer when traveling (e.g., planned itinerary vs. spontaneous, luxury vs. budget, fast-paced vs. slow)?",
                    # "Travel: Where do you dream of traveling and why?",
                    # Fitness & Wellness Section
                    # "Fitness & Wellness: How do you think about physical activity, fitness, or overall wellness in your life? Is it a priority, a chore, or something else?",
                    # "Fitness & Wellness: Describe any experiences with sports, exercise, or wellness activities that you've found particularly enjoyable, rewarding, or challenging. What did you like or dislike about them?",
                    # "Fitness & Wellness: What motivates you to be active (e.g., health benefits, stress relief, social aspect, competition, enjoyment of the activity itself)? What are the biggest barriers?",
                    # "Fitness & Wellness: What does 'feeling healthy' or 'fit' mean to you personally?"
                ]
            },
            {
                "name": "Synthesis & Future",
                "instructions": "Finally, please reflect on all areas you've discussed.",
                "questions": [
                    # "Discovery Process: Across all these areas (movies, food, travel, etc.), how do you generally discover new things you might like? Are you more likely to rely on algorithms, expert reviews, social recommendations, or random exploration?",
                    # "Aspirations: Looking ahead, are there new types of experiences, hobbies, or areas of interest you hope to explore more in the coming years?",
                    # "Anything Else: Is there anything else about your tastes, preferences, habits, or life experiences that you feel is important for your digital twin to understand?"
                ]
            }
        ]
     # Defining logic for followup questions
    def _needs_elaboration(self, response):
        """Check if response needs follow-up using multiple criteria"""
        if len(response.split()) < 30:
            return True
        return self._llm_assessment(response)

    # Assessing response quality
    def _llm_assessment(self, response):
        """Use LLM to assess response quality"""
        prompt = f"""Assess if this response needs follow-up (Answer only YES/NO):
        Response: {response[:500]}  # Truncate to save tokens
        Consider: Specific examples? Emotional depth? Concrete details?"""
        return self.llm([HumanMessage(content=prompt)]).content == "YES"

    # Generating followup question
    def _generate_follow_up(self, question, response):
        """Generate context-aware follow-up question"""
        prompt = f"""Generate ONE follow-up question based on:
        Original Q: {question}
        Response: {response[:300]}
        Keep it relevant and probing. Format: 'Follow-up: ...'"""
        result = self.llm([HumanMessage(content=prompt)]).content
        return result.replace("Follow-up: ", "").strip()

    # Saving progress
    def _save_progress(self):
        """Save conversation with token awareness"""
        truncated_convo = [{
            "q": msg["question"][:150],
            "a": msg["answer"][:500]
        } for msg in self.conversation]
        
        with open("interview_progress.json", "w") as f:
            json.dump(truncated_convo, f)

    # Defining logic for conducting interview
    def conduct_interview(self):
        try:
            while self.current_phase < len(self.phases):
                phase = self.phases[self.current_phase]
                print(f"\n=== {phase['name']} ===\n")

                while self.current_question < len(phase['questions']):
                    question = phase['questions'][self.current_question]
                    print(f"[Question {self.current_question+1}] {question}")
                    
                    # Getting initial response
                    response = input("\nYour answer: ").strip()
                    self.conversation.append({
                        "question": question,
                        "answer": response,
                        "phase": phase['name']
                    })

                    # Follow-up logic
                    self.follow_up_depth = 0
                    while self._needs_elaboration(response) and self.follow_up_depth < 2:
                        follow_up = self._generate_follow_up(question, response)
                        print(f"\n[Follow-up] {follow_up}")
                        follow_resp = input("Your answer: ").strip()
                        
                        self.conversation.append({
                            "question": follow_up,
                            "answer": follow_resp,
                            "phase": phase['name']
                        })
                        response += " " + follow_resp
                        self.follow_up_depth += 1

                    self.current_question += 1
                    self._save_progress()

                self.current_phase += 1
                self.current_question = 0

            print("\nInterview complete! Final report saved.")

        except KeyboardInterrupt:
            self._save_progress()
            print("\nProgress saved. You can resume later.")

if __name__ == "__main__":
    agent = InterviewAgent(api_key=api_key)
    agent.conduct_interview()