"""Mood analysis using Groq AI with VADER fallback"""

import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from groq import Groq
from config.settings import settings

class MoodAnalyzer:
    """Analyzes text sentiment and returns mood with AI summary"""
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        
        # Initialize Groq if API key exists
        self.groq = None
        if settings.GROQ_API_KEY:
            try:
                self.groq = Groq(api_key=settings.GROQ_API_KEY)
                print("✅ Groq AI initialized")
            except Exception as e:
                print(f"❌ Groq init failed: {e}")
    
    def analyze_with_groq(self, text: str) -> dict:
        """
        Analyze mood using Groq AI (PRIMARY METHOD)
        Returns: mood analysis + song recommendations
        """
        if not self.groq:
            return None
        
        try:
            prompt = f"""Analyze this text for mood and recommend 5 songs.
            Text: "{text}"

            Return JSON:
            {{
                "mood_analysis": {{
                    "score": 0.5,
                    "magnitude": 0.7,
                    "mood_category": "Positive",
                    "mood_description": "You're in a good mood!",
                    "intensity": "moderate",
                    "summary": "80-120 word engaging summary celebrating mood and connecting to music..."
                }},
                "song_recommendations": [
                    {{"name": "Song", "artist": "Artist", "search_terms": ["term1", "term2"]}}
                ]
            }}

            Guidelines:
            - score: -1.0 to 1.0
            - mood_category: "Very Negative", "Negative", "Neutral", "Positive", "Very Positive"
            - Also try to uplift the mood if very negative
            - If mood is negative, suggest soothing songs
            - summary: Positive, fun 80-120 words connecting mood to music
            - Also Don't repeat the songs again and again
            - 5 popular songs matching mood
            - also the 5 songs should have some correlation to each other"""

            response = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="groq/compound",
                max_tokens=1024,
                temperature=0.5
            )

            response_text = response.choices[0].message.content.strip()
            
            # Clean markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].strip()
            
            result = json.loads(response_text)
            
            if "mood_analysis" in result and "song_recommendations" in result:
                print(f"✅ Groq: {result['mood_analysis']['summary'][:50]}...")
                return result
            
            print("❌ Groq response invalid format")
            return None
            
        except Exception as e:
            print(f"❌ Groq error: {e}")
            return None
    
    def analyze_with_vader(self, text: str) -> dict:
        """
        Analyze mood using VADER (FALLBACK METHOD)
        Returns: mood analysis only (no songs)
        """
        sentiment = self.vader.polarity_scores(text)
        score = sentiment['compound']
        
        # Map score to mood
        if score >= 0.5:
            category = "Very Positive"
            description = "You're feeling fantastic and energetic!"
            summary = "What an incredible energy you're radiating! Your positivity is infectious and it's the perfect time to celebrate with music that matches your soaring spirits. Whether you're dancing or conquering the world, these songs will amplify your amazing mood and keep those good vibes flowing!"
        elif score >= 0.1:
            category = "Positive"
            description = "You're in a good, upbeat mood!"
            summary = "You're glowing with positive energy! This upbeat mood calls for music that celebrates life's wonderful moments. These songs will be your perfect companions as you ride this wave of happiness. Let the melodies lift you even higher!"
        elif score >= -0.1:
            category = "Neutral"
            description = "You're feeling calm and balanced."
            summary = "There's something beautiful about finding balance in life. This peaceful state is perfect for discovering music that speaks to your soul. These songs will complement your tranquil mood and add a gentle spark to your day."
        elif score >= -0.5:
            category = "Negative"
            description = "You're feeling a bit down or melancholic."
            summary = "Life has its challenging moments, and music has this incredible power to be your companion through them. These songs offer comfort, hope, and a reminder that you're not alone. Music can be the bridge that carries us back to brighter days."
        else:
            category = "Very Negative"
            description = "You're going through a tough time."
            summary = "In your darkest moments, music becomes a lifeline. These songs are chosen with care to honor your feelings while gently offering hope and healing. You're stronger than you know, and sometimes recovery begins with the right song."
        
        return {
            "score": score,
            "magnitude": abs(score),
            "mood_category": category,
            "mood_description": description,
            "intensity": "moderate",
            "summary": summary
        }
    
    def analyze(self, text: str) -> tuple:
        """
        MAIN FUNCTION - Try Groq first, fallback to VADER
        Returns: (mood_analysis_dict, groq_song_recommendations_list)
        """
        # Try Groq AI
        groq_result = self.analyze_with_groq(text)
        if groq_result:
            return groq_result["mood_analysis"], groq_result.get("song_recommendations", [])
        
        # Fallback to VADER
        print("⚠️ Falling back to VADER")
        return self.analyze_with_vader(text), []

mood_analyzer = MoodAnalyzer()