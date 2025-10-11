import { useEffect, useState } from 'react';
import Waves from './Waves';

interface DynamicWavesProps {
  style?: React.CSSProperties;
}

const DynamicWaves: React.FC<DynamicWavesProps> = ({ style }) => {
  const [waveColor, setWaveColor] = useState('rgba(168, 85, 247, 0.75)');

  useEffect(() => {
    // Function to update wave color from CSS variable
    const updateWaveColor = () => {
      const color = getComputedStyle(document.documentElement)
        .getPropertyValue('--wave-color')
        .trim();
      
      if (color) {
        console.log('🌊 Wave color updated to:', color);
        setWaveColor(color);
      }
    };

    // Initial update
    updateWaveColor();

    // Watch for CSS variable changes
    const observer = new MutationObserver(updateWaveColor);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['style'],
    });

    return () => observer.disconnect();
  }, []);

  return (
    <Waves
      lineColor={waveColor}
      backgroundColor="transparent"
      waveSpeedX={0.02}
      waveSpeedY={0.01}
      waveAmpX={40}
      waveAmpY={20}
      friction={0.9}
      tension={0.01}
      maxCursorMove={120}
      xGap={12}
      yGap={36}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: 0,
        pointerEvents: "none",
        ...style,
      }}
    />
  );
};

export default DynamicWaves;