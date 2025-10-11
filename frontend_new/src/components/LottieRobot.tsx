import Lottie from 'lottie-react';
import type { LottieRefCurrentProps } from 'lottie-react';
import { useEffect, useState, useImperativeHandle, forwardRef, useRef } from 'react';

// Update the interface to accept mood:
interface LottieRobotProps {
  className?: string;
  style?: React.CSSProperties;
  mood?: string; // Add this
}

export interface LottieRobotHandle {
  dance: () => void;
  stop: () => void;
}

const LottieRobot = forwardRef<LottieRobotHandle, LottieRobotProps>(
  ({ className = '', style = {}, mood = 'neutral' }, ref) => {
    const [idleAnimation, setIdleAnimation] = useState(null);
    const [danceAnimation, setDanceAnimation] = useState(null);
    const [currentAnimation, setCurrentAnimation] = useState(null);
    const [isDancing, setIsDancing] = useState(false);
    const lottieRef = useRef<LottieRefCurrentProps>(null);

    useEffect(() => {
      // Fetch the idle animation (Robot-Bot 3D)
      fetch('/Robot-Bot 3D.json')
        .then(response => response.json())
        .then(data => {
          setIdleAnimation(data);
          setCurrentAnimation(data);
        })
        .catch(error => console.error('Error loading idle animation:', error));

      // Fetch the dancing animation (Dancing-Bot)
      fetch('/Dancing-Bot.json')
        .then(response => response.json())
        .then(data => setDanceAnimation(data))
        .catch(error => console.error('Error loading dance animation:', error));
    }, []);

    // Add function to get animation speed based on mood:
    const getAnimationSpeed = (moodCategory: string): number => {
      const speedMap: Record<string, number> = {
        'happy': 1.5,        // Fast dancing
        'energetic': 1.8,    // Fastest dancing
        'calm': 0.6,         // Slow, gentle
        'romantic': 0.8,     // Smooth and slow
        'neutral': 1.0,      // Normal speed
        'anxious': 1.3,      // Quick, jittery
        'sad': 0.5,          // Very slow, comforting
        'angry': 1.4,        // Fast, intense
      };
      return speedMap[moodCategory.toLowerCase()] || 1.0;
    };

    // Expose dance and stop methods to parent component
    useImperativeHandle(ref, () => ({
      dance: () => {
        console.log('Dance called with mood:', mood);
        if (danceAnimation) {
          setIsDancing(true);
          setCurrentAnimation(danceAnimation);
          setTimeout(() => {
            if (lottieRef.current) {
              const speed = getAnimationSpeed(mood);
              console.log('Setting dance speed:', speed);
              lottieRef.current.setSpeed(speed);
              lottieRef.current.play();
            }
          }, 100);
        }
      },
      stop: () => {
        console.log('Stop called!');
        setIsDancing(false);
        if (idleAnimation) {
          setCurrentAnimation(idleAnimation);
        }
        if (lottieRef.current) {
          lottieRef.current.stop();
        }
      }
    }));

    if (!currentAnimation) return null;

    const defaultStyle: React.CSSProperties = {
      width: '300px',
      height: '300px',
      opacity: 0.3,
      transition: 'all 0.3s ease',
      ...style
    };

    return (
      <div 
        className={`lottie-robot-wrapper ${isDancing ? 'animate-energetic-dance' : 'animate-float-gentle'} ${className}`}
        style={defaultStyle}
      >
        <Lottie 
          lottieRef={lottieRef}
          animationData={currentAnimation} 
          loop={true}
          autoplay={isDancing}
          className="w-full h-full"
        />
        <style>{`
          @keyframes float-gentle {
            0%, 100% { 
              transform: translateY(0px) rotate(0deg); 
            }
            50% { 
              transform: translateY(-20px) rotate(5deg); 
            }
          }
          
          .animate-float-gentle {
            animation: float-gentle 6s ease-in-out infinite;
          }

          @keyframes energetic-dance {
            0% { 
              transform: translateY(0px) rotate(0deg) scale(1); 
            }
            15% { 
              transform: translateY(-15px) rotate(-8deg) scale(1.08); 
            }
            30% { 
              transform: translateY(-5px) rotate(5deg) scale(1.05); 
            }
            45% { 
              transform: translateY(-20px) rotate(-5deg) scale(1.1); 
            }
            60% { 
              transform: translateY(-10px) rotate(8deg) scale(1.06); 
            }
            75% { 
              transform: translateY(-15px) rotate(-3deg) scale(1.08); 
            }
            90% { 
              transform: translateY(-8px) rotate(6deg) scale(1.04); 
            }
            100% { 
              transform: translateY(0px) rotate(0deg) scale(1); 
            }
          }

          .animate-energetic-dance {
            animation: energetic-dance 1.5s ease-in-out infinite;
            opacity: 1 !important;
          }
        `}</style>
      </div>
    );
  }
);

LottieRobot.displayName = 'LottieRobot';

export default LottieRobot;