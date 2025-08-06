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
  | 'zoomOutPanDown'
  | 'zoomInRotate'
  | 'panRotate'
  | 'zoomOutRotate';

export type Speed = 'slow' | 'medium' | 'fast';

interface KenBurnsImageProps {
  src: string;
  duration: number; // in seconds
  effect: KenBurnsEffect;
  speed: Speed;
  startFrame: number;
  isInterior?: boolean; // Flag to indicate if this is an interior shot
}

export const KenBurnsImage: React.FC<KenBurnsImageProps> = ({
  src,
  duration,
  effect,
  speed,
  startFrame,
  isInterior = true, // Default to interior for more movement
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Adjust frame relative to when this image starts
  const relativeFrame = frame - startFrame;
  const durationInFrames = duration * fps;
  
  // Speed multipliers - controls how much movement happens
  // Increase movement for interior shots
  const baseMultiplier = {
    slow: 0.15,    // Very subtle movement
    medium: 0.3,   // Moderate movement
    fast: 0.5      // More dramatic movement
  }[speed];
  
  // Boost movement for interior shots to show more of the room
  const speedMultiplier = isInterior ? baseMultiplier * 1.8 : baseMultiplier;
  
  // Calculate progress (0 to 1)
  const progress = interpolate(
    relativeFrame,
    [0, durationInFrames],
    [0, 1],
    { extrapolateRight: 'clamp', extrapolateLeft: 'clamp' }
  );
  
  // Base zoom levels - more zoom for interiors to explore the space
  const zoomStart = 1;
  const zoomEnd = 1 + (0.4 * speedMultiplier); // Max zoom depends on speed
  
  // Calculate zoom based on effect
  let zoom = 1;
  if (effect.includes('zoomIn')) {
    zoom = interpolate(progress, [0, 1], [zoomStart, zoomEnd]);
  } else if (effect.includes('zoomOut')) {
    zoom = interpolate(progress, [0, 1], [zoomEnd, zoomStart]);
  }
  
  // Pan distances (as percentage of image size) - increased for better room exploration
  const panDistance = isInterior ? 25 * speedMultiplier : 15 * speedMultiplier;
  
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
  
  // Add rotation for more dynamic movement (especially for interiors)
  let rotation = 0;
  if (effect.includes('Rotate')) {
    // More rotation for interiors to show room perspective
    const maxRotation = isInterior ? 3 : 1.5; // degrees
    rotation = interpolate(progress, [0, 0.5, 1], [0, maxRotation, 0]);
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
          transform: `scale(${zoom}) translate(${translateX}%, ${translateY}%) rotate(${rotation}deg)`,
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
export function getEffectForIndex(index: number, isInterior: boolean = true): KenBurnsEffect {
  // More dynamic effects for interiors, simpler for exteriors
  const interiorEffects: KenBurnsEffect[] = [
    'zoomIn',
    'zoomInRotate',
    'panLeft',
    'panRight',
    'zoomInPanLeft',
    'zoomInPanRight',
    'panRotate',
    'zoomOutPanUp',
    'zoomOutPanDown',
    'zoomOutRotate',
  ];
  
  const exteriorEffects: KenBurnsEffect[] = [
    'zoomIn',
    'zoomOut',
    'panLeft',
    'panRight',
    'zoomInPanLeft',
    'zoomInPanRight',
  ];
  
  const effects = isInterior ? interiorEffects : exteriorEffects;
  return effects[index % effects.length];
}