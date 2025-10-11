import { useEffect } from 'react';

interface ThemeColors {
  // CSS Variables
  accentPrimary: string;
  accentSecondary: string;
  glowColor: string;
  gradientStart: string;
  gradientEnd: string;
  
  // Additional theme properties
  backgroundColor: string;
  textColor: string;
  waveColor: string;
  cardBackground: string;
  borderColor: string;
  isDarkMode: boolean;
  backgroundImage?: string; // Optional background image URL
  backgroundOverlay?: string; // Overlay color for readability
}

const moodThemes: Record<string, ThemeColors> = {
  // Happy - LIGHT MODE (Fresh Green & Vibrant) 🌿
  'happy': {
    accentPrimary: '#10B981', // Emerald green
    accentSecondary: '#34D399', // Light green
    glowColor: 'rgba(52, 211, 153, 0.35)',
    gradientStart: '#10B981',
    gradientEnd: '#34D399',
    backgroundColor: '#ECFDF5', // Very light mint
    textColor: '#064E3B', // Dark green
    waveColor: 'rgba(52, 211, 153, 0.85)', // Bright green waves
    cardBackground: 'rgba(255, 255, 255, 0.75)',
    borderColor: 'rgba(16, 185, 129, 0.4)',
    isDarkMode: false,
    backgroundImage: 'linear-gradient(-45deg, #ECFDF5, #D1FAE5, #A7F3D0, #6EE7B7)', // Green gradient flow
    backgroundOverlay: 'rgba(236, 253, 245, 0.75)',
  },
  
  // Energetic - DARK MODE (Electric & Dynamic)
  'energetic': {
    accentPrimary: '#A855F7',
    accentSecondary: '#06B6D4',
    glowColor: 'rgba(6, 182, 212, 0.4)',
    gradientStart: '#A855F7',
    gradientEnd: '#06B6D4',
    backgroundColor: '#0a0a0a',
    textColor: '#ffffff',
    waveColor: 'rgba(6, 182, 212, 0.8)', // Increased opacity
    cardBackground: 'rgba(15, 15, 15, 0.5)',
    borderColor: 'rgba(6, 182, 212, 0.4)',
    isDarkMode: true,
    backgroundImage: 'linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #4facfe)',
    backgroundOverlay: 'rgba(10, 10, 10, 0.7)',
  },
  
  // Calm - LIGHT MODE (Peaceful Sky)
  'calm': {
    accentPrimary: '#3B82F6',
    accentSecondary: '#60A5FA',
    glowColor: 'rgba(59, 130, 246, 0.3)',
    gradientStart: '#3B82F6',
    gradientEnd: '#60A5FA',
    backgroundColor: '#DBEAFE',
    textColor: '#1E3A8A',
    waveColor: 'rgba(96, 165, 250, 0.85)', // Increased opacity
    cardBackground: 'rgba(255, 255, 255, 0.75)',
    borderColor: 'rgba(59, 130, 246, 0.4)',
    isDarkMode: false,
    backgroundImage: 'linear-gradient(-45deg, #DBEAFE, #BFDBFE, #93C5FD, #60A5FA)',
    backgroundOverlay: 'rgba(219, 234, 254, 0.75)',
  },
  
  // Sad - DARK MODE (Comforting Purple)
  'sad': {
    accentPrimary: '#A78BFA',
    accentSecondary: '#C4B5FD',
    glowColor: 'rgba(167, 139, 250, 0.3)',
    gradientStart: '#A78BFA',
    gradientEnd: '#C4B5FD',
    backgroundColor: '#1a1625',
    textColor: '#F3E8FF',
    waveColor: 'rgba(196, 181, 253, 0.7)', // Increased opacity
    cardBackground: 'rgba(88, 70, 130, 0.25)',
    borderColor: 'rgba(167, 139, 250, 0.3)',
    isDarkMode: true,
    backgroundImage: 'linear-gradient(-45deg, #4a5568, #6b46c1, #805ad5, #9f7aea)',
    backgroundOverlay: 'rgba(26, 22, 37, 0.8)',
  },
  
  // Angry - DARK MODE (Intense Fire)
  'angry': {
    accentPrimary: '#7C3AED',
    accentSecondary: '#DC2626',
    glowColor: 'rgba(220, 38, 38, 0.4)',
    gradientStart: '#7C3AED',
    gradientEnd: '#DC2626',
    backgroundColor: '#0a0a0a',
    textColor: '#ffffff',
    waveColor: 'rgba(220, 38, 38, 0.8)', // Increased opacity
    cardBackground: 'rgba(15, 15, 15, 0.5)',
    borderColor: 'rgba(220, 38, 38, 0.4)',
    isDarkMode: true,
    backgroundImage: 'linear-gradient(-45deg, #eb3349, #f45c43, #fc4a1a, #f7b733)',
    backgroundOverlay: 'rgba(10, 10, 10, 0.7)',
  },
  
  // Anxious - LIGHT MODE (Warm Amber Warning)
  'anxious': {
    accentPrimary: '#D97706',
    accentSecondary: '#F59E0B',
    glowColor: 'rgba(245, 158, 11, 0.3)',
    gradientStart: '#D97706',
    gradientEnd: '#F59E0B',
    backgroundColor: '#FEF3C7',
    textColor: '#78350F',
    waveColor: 'rgba(245, 158, 11, 0.85)', // Increased opacity
    cardBackground: 'rgba(255, 255, 255, 0.75)',
    borderColor: 'rgba(217, 119, 6, 0.4)',
    isDarkMode: false,
    backgroundImage: 'linear-gradient(-45deg, #FEF3C7, #FDE68A, #FCD34D, #FBBF24)',
    backgroundOverlay: 'rgba(254, 243, 199, 0.75)',
  },
  
  // Romantic - LIGHT MODE (Soft Pink)
  'romantic': {
    accentPrimary: '#EC4899',
    accentSecondary: '#F43F5E',
    glowColor: 'rgba(236, 72, 153, 0.3)',
    gradientStart: '#EC4899',
    gradientEnd: '#F43F5E',
    backgroundColor: '#FFF1F2',
    textColor: '#1F2937',
    waveColor: 'rgba(236, 72, 153, 0.85)', // Increased opacity
    cardBackground: 'rgba(255, 255, 255, 0.75)',
    borderColor: 'rgba(236, 72, 153, 0.4)',
    isDarkMode: false,
    backgroundImage: 'linear-gradient(-45deg, #ffecd2, #fcb69f, #ff9a9e, #fad0c4)',
    backgroundOverlay: 'rgba(255, 241, 242, 0.75)',
  },
  
  // Neutral - DARK MODE (Default Purple)
  'neutral': {
    accentPrimary: '#8B5CF6',
    accentSecondary: '#6366f1',
    glowColor: 'rgba(168, 85, 247, 0.3)',
    gradientStart: '#a855f7',
    gradientEnd: '#6366f1',
    backgroundColor: '#0a0a0a',
    textColor: '#ffffff',
    waveColor: 'rgba(168, 85, 247, 0.7)', // Increased opacity
    cardBackground: 'rgba(15, 15, 15, 0.5)',
    borderColor: 'rgba(168, 85, 247, 0.2)',
    isDarkMode: true,
    backgroundImage: 'linear-gradient(-45deg, #667eea, #764ba2, #6B8DD6, #8E37D7)',
    backgroundOverlay: 'rgba(10, 10, 10, 0.8)',
  },
};

export const useTheme = (mood: string | null) => {
  useEffect(() => {
    console.log('🎨 Theme Hook - Received mood:', mood);
    
    if (!mood) {
      console.log('🎨 Theme Hook - Applying neutral theme');
      applyTheme(moodThemes.neutral);
      return;
    }

    // Normalize mood - remove punctuation, lowercase, trim
    const normalizedMood = mood
      .toLowerCase()
      .replace(/[^\w\s]/g, '') // Remove punctuation
      .trim();
    
    console.log('🎨 Theme Hook - Normalized mood:', normalizedMood);
    
    // ENHANCED: Try multiple matching strategies
    let theme = null;
    
    // Strategy 1: Exact match
    if (moodThemes[normalizedMood]) {
      theme = moodThemes[normalizedMood];
      console.log('🎨 Exact match found:', normalizedMood);
    }
    
    // Strategy 2: Check if mood contains any valid mood keyword
    if (!theme) {
      const validMoods = ['happy', 'energetic', 'calm', 'sad', 'angry', 'anxious', 'romantic', 'neutral'];
      
      for (const validMood of validMoods) {
        if (normalizedMood.includes(validMood) || validMood.includes(normalizedMood)) {
          theme = moodThemes[validMood];
          console.log('🎨 Keyword match found:', validMood);
          break;
        }
      }
    }
    
    // Strategy 3: Synonym mapping
    if (!theme) {
      const synonymMap: Record<string, string> = {
        // Happy synonyms
        'joyful': 'happy', 'cheerful': 'happy', 'delighted': 'happy', 
        'pleased': 'happy', 'content': 'happy', 'glad': 'happy',
        'ecstatic': 'happy', 'thrilled': 'happy', 'elated': 'happy',
        
        // Energetic synonyms
        'excited': 'energetic', 'hyper': 'energetic', 'pumped': 'energetic',
        'enthusiastic': 'energetic', 'lively': 'energetic', 'vibrant': 'energetic',
        'dynamic': 'energetic', 'active': 'energetic',
        
        // Calm synonyms
        'peaceful': 'calm', 'relaxed': 'calm', 'chill': 'calm',
        'tranquil': 'calm', 'serene': 'calm', 'mellow': 'calm',
        'zen': 'calm', 'composed': 'calm', 'soothed': 'calm',
        
        // Sad synonyms
        'melancholic': 'sad', 'depressed': 'sad', 'down': 'sad',
        'gloomy': 'sad', 'blue': 'sad', 'unhappy': 'sad',
        'sorrowful': 'sad', 'dejected': 'sad', 'heartbroken': 'sad',
        
        // Angry synonyms
        'frustrated': 'angry', 'mad': 'angry', 'furious': 'angry',
        'irritated': 'angry', 'annoyed': 'angry', 'enraged': 'angry',
        'upset': 'angry', 'outraged': 'angry',
        
        // Anxious synonyms
        'stressed': 'anxious', 'nervous': 'anxious', 'worried': 'anxious',
        'tense': 'anxious', 'uneasy': 'anxious', 'apprehensive': 'anxious',
        'overwhelmed': 'anxious', 'restless': 'anxious',
        
        // Romantic synonyms
        'loving': 'romantic', 'affectionate': 'romantic', 'passionate': 'romantic',
        'tender': 'romantic', 'devoted': 'romantic', 'infatuated': 'romantic',
        'smitten': 'romantic', 'amorous': 'romantic',
      };
      
      for (const [synonym, validMood] of Object.entries(synonymMap)) {
        if (normalizedMood.includes(synonym)) {
          theme = moodThemes[validMood];
          console.log('🎨 Synonym match found:', synonym, '→', validMood);
          break;
        }
      }
    }
    
    // Fallback to neutral
    if (!theme) {
      theme = moodThemes.neutral;
      console.log('🎨 No match found, using neutral theme');
    }
    
    console.log('🎨 Applying theme:', theme);
    applyTheme(theme);
  }, [mood]);
};

// Update the applyTheme function to add/remove body class:
const applyTheme = (colors: ThemeColors) => {
  const root = document.documentElement;
  const body = document.body;
  
  console.log('🎨 Applying comprehensive theme:', colors);
  
  // Toggle light/dark mode class
  if (colors.isDarkMode) {
    body.classList.remove('light-mode');
    body.classList.add('dark-mode');
  } else {
    body.classList.remove('dark-mode');
    body.classList.add('light-mode');
  }
  
  // Set ALL CSS variables
  root.style.setProperty('--accent-primary', colors.accentPrimary);
  root.style.setProperty('--accent-secondary', colors.accentSecondary);
  root.style.setProperty('--glow-color', colors.glowColor);
  root.style.setProperty('--gradient-start', colors.gradientStart);
  root.style.setProperty('--gradient-end', colors.gradientEnd);
  root.style.setProperty('--wave-color', colors.waveColor);
  root.style.setProperty('--bg-color', colors.backgroundColor);
  root.style.setProperty('--text-color', colors.textColor);
  root.style.setProperty('--card-bg', colors.cardBackground);
  root.style.setProperty('--border-color', colors.borderColor);
  
  // Set background image and overlay
  if (colors.backgroundImage) {
    root.style.setProperty('--bg-image', colors.backgroundImage);
  } else {
    root.style.setProperty('--bg-image', 'none');
  }
  
  if (colors.backgroundOverlay) {
    root.style.setProperty('--bg-overlay', colors.backgroundOverlay);
  }
  
  // Apply to body
  body.style.backgroundColor = colors.backgroundColor;
  body.style.color = colors.textColor;
  
  // Update app background with transition
  const app = document.querySelector('.app') as HTMLElement;
  if (app) {
    app.style.transition = 'background 0.6s ease-in-out';
    if (colors.isDarkMode) {
      app.style.background = `linear-gradient(180deg, ${colors.backgroundColor} 0%, #000000 100%)`;
    } else {
      app.style.background = `linear-gradient(180deg, ${colors.backgroundColor} 0%, #ffffff 100%)`;
    }
  }
  
  // Force repaint for waves
  root.style.setProperty('--force-repaint', String(Date.now()));
  
  console.log('✅ Theme applied successfully! Wave color:', colors.waveColor);
};