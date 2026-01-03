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

            Return JSON with EXACT mood_category from this list:
            - "happy" (joyful, cheerful, delighted)
            - "energetic" (excited, hyper, pumped)
            - "calm" (peaceful, relaxed, chill)
            - "sad" (melancholic, depressed, down)
            - "angry" (frustrated, rage, mad)
            - "anxious" (stressed, nervous, worried)
            - "romantic" (loving, affectionate, passionate)
            - "neutral" (balanced, normal, okay)

            Return JSON:
            {{
                "mood_analysis": {{
                    "score": 0.5,
                    "magnitude": 0.7,
                    "mood_category": "happy",
                    "mood_description": "You're in a good mood!",
                    "intensity": "moderate",
                    "summary": "80-120 word engaging summary celebrating mood and connecting to music..."
                }},
                "song_recommendations": [
                    {{"name": "Song", "artist": "Artist", "search_terms": ["term1", "term2"]}}
                ]
            }}

            IMPORTANT: mood_category MUST be one of: happy, energetic, calm, sad, angry, anxious, romantic, neutral
            
            Guidelines:
            - score: -1.0 to 1.0
            - If mood is negative, suggest soothing songs to uplift
            - summary: Positive, fun 80-120 words connecting mood to music
            - 5 popular songs matching mood with variety"""

            response = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="groq/compound",
                max_tokens=1024,
                temperature=0.8
            )

            response_text = response.choices[0].message.content.strip()
            
            # Clean markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].strip()
            
            result = json.loads(response_text)
            
            if "mood_analysis" in result and "song_recommendations" in result:
                # Validate mood_category
                valid_moods = ["happy", "energetic", "calm", "sad", "angry", "anxious", "romantic", "neutral"]
                mood_cat = result['mood_analysis']['mood_category'].lower()
                
                if mood_cat not in valid_moods:
                    # Map to closest valid mood
                    mood_cat = self._map_to_valid_mood(mood_cat, result['mood_analysis']['score'])
                    result['mood_analysis']['mood_category'] = mood_cat
                
                print(f"✅ Groq: {result['mood_analysis']['mood_category']} - {result['mood_analysis']['summary'][:50]}...")
                return result
            
            print("❌ Groq response invalid format")
            return None
            
        except Exception as e:
            print(f"❌ Groq error: {e}")
            return None
    
    def _map_to_valid_mood(self, mood: str, score: float) -> str:
        """Map any mood to one of the 8 valid categories"""
        mood_lower = mood.lower()
        
        # Mapping dictionary
        mood_map = {
            'joyful': 'happy', 'cheerful': 'happy', 'delighted': 'happy', 'positive': 'happy',
            'excited': 'energetic', 'hyper': 'energetic', 'pumped': 'energetic',
            'peaceful': 'calm', 'relaxed': 'calm', 'chill': 'calm', 'tranquil': 'calm',
            'melancholic': 'sad', 'depressed': 'sad', 'down': 'sad', 'negative': 'sad',
            'frustrated': 'angry', 'rage': 'angry', 'mad': 'angry',
            'stressed': 'anxious', 'nervous': 'anxious', 'worried': 'anxious',
            'loving': 'romantic', 'affectionate': 'romantic', 'passionate': 'romantic',
        }
        
        # Try direct mapping
        for key, value in mood_map.items():
            if key in mood_lower or mood_lower in key:
                return value
        
        # Fallback based on score
        if score >= 0.5:
            return 'happy'
        elif score >= 0.1:
            return 'calm'
        elif score >= -0.1:
            return 'neutral'
        elif score >= -0.5:
            return 'sad'
        else:
            return 'anxious'
    
    def analyze_with_vader(self, text: str) -> dict:
        """
        Analyze mood using VADER (FALLBACK METHOD)
        Returns: mood analysis only (no songs)
        """
        sentiment = self.vader.polarity_scores(text)
        score = sentiment['compound']
        
        # Map score to our 8 categories
        if score >= 0.5:
            category = "happy"
            description = "You're feeling fantastic and energetic!"
            summary = "What an incredible energy you're radiating! Your positivity is infectious and it's the perfect time to celebrate with music that matches your soaring spirits. Whether you're dancing or conquering the world, these songs will amplify your amazing mood and keep those good vibes flowing!"
        elif score >= 0.3:
            category = "energetic"
            description = "You're feeling pumped and ready to go!"
            summary = "You're absolutely buzzing with energy! This electric mood calls for music that matches your vibrant spirit. These songs will keep you moving, grooving, and riding this incredible wave of excitement!"
        elif score >= 0.1:
            category = "calm"
            description = "You're feeling peaceful and balanced."
            summary = "There's something beautiful about finding balance in life. This peaceful state is perfect for discovering music that speaks to your soul. These songs will complement your tranquil mood and add a gentle spark to your day."
        elif score >= -0.1:
            category = "neutral"
            description = "You're in a balanced, neutral mood."
            summary = "You're in a perfectly balanced state, and that's wonderful! This is a great moment to explore diverse sounds and let music guide your emotions. These songs offer a beautiful journey through different vibes."
        elif score >= -0.3:
            category = "anxious"
            description = "You're feeling a bit stressed or worried."
            summary = "Life can be overwhelming sometimes, but music has this incredible power to soothe and center us. These carefully chosen songs will help ease your mind and bring a sense of calm to your day."
        elif score >= -0.5:
            category = "sad"
            description = "You're feeling down or melancholic."
            summary = "In moments of sadness, music becomes our companion. These songs honor your feelings while gently offering comfort and hope. Remember, it's okay to feel this way, and music can be the first step toward healing."
        else:
            category = "angry"
            description = "You're feeling frustrated or angry."
            summary = "Strong emotions need powerful music. These songs acknowledge your anger while channeling it into something transformative. Let the music help you process and release what you're feeling."
        
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