import Lottie from 'lottie-react';
import type { LottieRefCurrentProps } from 'lottie-react';
import { useEffect, useState, useImperativeHandle, forwardRef, useRef } from 'react';

interface LottieRobotProps {
  className?: string;
  style?: React.CSSProperties;
}

export interface LottieRobotHandle {
  dance: () => void;
  stop: () => void;
}

const LottieRobot = forwardRef<LottieRobotHandle, LottieRobotProps>(
  ({ className = '', style = {} }, ref) => {
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

    // Expose dance and stop methods to parent component
    useImperativeHandle(ref, () => ({
      dance: () => {
        console.log('Dance called!'); // Debug log
        if (danceAnimation) {
          setIsDancing(true);
          setCurrentAnimation(danceAnimation);
          setTimeout(() => {
            if (lottieRef.current) {
              lottieRef.current.setSpeed(0.1); // Slow down the dance animation
              lottieRef.current.play();
            }
          }, 100);
        }
      },
      stop: () => {
        console.log('Stop called!'); // Debug log
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
        className={`fixed pointer-events-none z-0 ${isDancing ? 'animate-energetic-dance' : 'animate-float-gentle'} ${className}`}
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
            opacity: 0.9 !important;
            filter: drop-shadow(0 0 30px rgba(168, 85, 247, 0.6));
          }

          .dancing {
            opacity: 0.9 !important;
            transform: scale(1.1);
            filter: drop-shadow(0 0 30px rgba(168, 85, 247, 0.6));
          }
        `}</style>
      </div>
    );
  }
);

LottieRobot.displayName = 'LottieRobot';

export default LottieRobot;