import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

export type KenBurnsEffect = 
  | 'zoomIn' 
  | 'zoomOut' 
  | 'panLeft' 
  | 'panRight' 
  | 'panUp' 
  | 'panDown'
  | 'zoomInPanLeft'
  | 'zoomInPanRight'
  | 'zoomOutPanUp'
  | 'zoomOutPanDown';

export type Speed = 'slow' | 'medium' | 'fast';

interface KenBurnsImageProps {
  src: string;
  duration: number; // in seconds
  effect: KenBurnsEffect;
  speed: Speed;
  startFrame: number;
}

export const KenBurnsImage: React.FC<KenBurnsImageProps> = ({
  src,
  duration,
  effect,
  speed,
  startFrame,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Adjust frame relative to when this image starts
  const relativeFrame = frame - startFrame;
  const durationInFrames = duration * fps;
  
  // Speed multipliers - controls how much movement happens
  const speedMultiplier = {
    slow: 0.15,    // Very subtle movement
    medium: 0.3,   // Moderate movement
    fast: 0.5      // More dramatic movement
  }[speed];
  
  // Calculate progress (0 to 1)
  const progress = interpolate(
    relativeFrame,
    [0, durationInFrames],
    [0, 1],
    { extrapolateRight: 'clamp', extrapolateLeft: 'clamp' }
  );
  
  // Base zoom levels
  const zoomStart = 1;
  const zoomEnd = 1 + (0.4 * speedMultiplier); // Max zoom depends on speed
  
  // Calculate zoom based on effect
  let zoom = 1;
  if (effect.includes('zoomIn')) {
    zoom = interpolate(progress, [0, 1], [zoomStart, zoomEnd]);
  } else if (effect.includes('zoomOut')) {
    zoom = interpolate(progress, [0, 1], [zoomEnd, zoomStart]);
  }
  
  // Pan distances (as percentage of image size)
  const panDistance = 15 * speedMultiplier; // Adjust pan distance based on speed
  
  // Calculate pan positions
  let translateX = 0;
  let translateY = 0;
  
  if (effect.includes('panLeft')) {
    translateX = interpolate(progress, [0, 1], [panDistance, -panDistance]);
  } else if (effect.includes('panRight')) {
    translateX = interpolate(progress, [0, 1], [-panDistance, panDistance]);
  }
  
  if (effect.includes('panUp')) {
    translateY = interpolate(progress, [0, 1], [panDistance, -panDistance]);
  } else if (effect.includes('panDown')) {
    translateY = interpolate(progress, [0, 1], [-panDistance, panDistance]);
  }
  
  // Smooth easing for more natural movement
  const easedProgress = easeInOutCubic(progress);
  
  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#000',
      }}
    >
      <AbsoluteFill
        style={{
          transform: `scale(${zoom}) translate(${translateX}%, ${translateY}%)`,
          transformOrigin: 'center center',
        }}
      >
        <img
          src={src}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
          alt=""
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Easing function for smoother animation
function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

// Helper to get a diverse set of effects
export function getEffectForIndex(index: number): KenBurnsEffect {
  const effects: KenBurnsEffect[] = [
    'zoomIn',
    'zoomOut',
    'panLeft',
    'panRight',
    'zoomInPanLeft',
    'zoomInPanRight',
    'zoomOutPanUp',
    'zoomOutPanDown',
  ];
  
  return effects[index % effects.length];
}