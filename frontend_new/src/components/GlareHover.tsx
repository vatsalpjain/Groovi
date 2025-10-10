import React from 'react';

interface GlareHoverProps {
  width?: string;
  height?: string;
  background?: string;
  borderRadius?: string;
  borderColor?: string;
  children?: React.ReactNode;
  glareColor?: string;
  glareOpacity?: number;
  glareAngle?: number;
  glareSize?: number;
  transitionDuration?: number;
  playOnce?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

const GlareHover: React.FC<GlareHoverProps> = ({
  width = 'auto',
  height = 'auto',
  background = 'transparent',
  borderRadius = '50px',
  borderColor = 'transparent',
  children,
  glareColor = '#ffffff',
  glareOpacity = 0.5,
  glareAngle = -45,
  glareSize = 250,
  transitionDuration = 650,
  playOnce = false,
  className = '',
  style = {}
}) => {
  const hex = glareColor.replace('#', '');
  let rgba = glareColor;
  if (/^[0-9A-Fa-f]{6}$/.test(hex)) {
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);
    rgba = `rgba(${r}, ${g}, ${b}, ${glareOpacity})`;
  } else if (/^[0-9A-Fa-f]{3}$/.test(hex)) {
    const r = parseInt(hex[0] + hex[0], 16);
    const g = parseInt(hex[1] + hex[1], 16);
    const b = parseInt(hex[2] + hex[2], 16);
    rgba = `rgba(${r}, ${g}, ${b}, ${glareOpacity})`;
  }

  const containerClassName = `w-[190px] h-auto bg-transparent rounded-[50px] border border-transparent overflow-hidden relative self-center inline-flex justify-center items-center cursor-pointer ${className}`;

  const containerStyle: React.CSSProperties = {
    width: width !== 'auto' ? width : undefined,
    height: height !== 'auto' ? height : undefined,
    background: background !== 'transparent' ? background : undefined,
    borderRadius: borderRadius !== '50px' ? borderRadius : undefined,
    borderColor: borderColor !== 'transparent' ? borderColor : undefined,
    ...style
  };

  const beforeStyle: React.CSSProperties = {
    background: `linear-gradient(
      ${glareAngle}deg,
      hsla(0, 0%, 0%, 0) 60%,
      ${rgba} 70%,
      hsla(0, 0%, 0%, 0),
      hsla(0, 0%, 0%, 0) 100%
    )`,
    transition: playOnce ? 'none' : `${transitionDuration}ms ease`,
    backgroundSize: `${glareSize}% ${glareSize}%, 100% 100%`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: '-100% -100%, 0 0',
    pointerEvents: 'none'
  };

  return (
    <div
      className={`group ${containerClassName}`}
      style={containerStyle}
      onMouseEnter={(e) => {
        const beforeEl = e.currentTarget.querySelector('.glare-before') as HTMLElement;
        if (beforeEl) {
          Object.assign(beforeEl.style, {
            backgroundPosition: '100% 100%, 0 0',
            transition: `${transitionDuration}ms ease`
          });
        }
      }}
      onMouseLeave={(e) => {
        const beforeEl = e.currentTarget.querySelector('.glare-before') as HTMLElement;
        if (beforeEl && !playOnce) {
          Object.assign(beforeEl.style, {
            backgroundPosition: '-100% -100%, 0 0'
          });
        }
      }}
    >
      <div
        className="glare-before absolute inset-0"
        style={beforeStyle}
      />
      {children}
    </div>
  );
};

export default GlareHover;
