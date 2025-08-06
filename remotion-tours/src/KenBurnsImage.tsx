import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

export type KenBurnsEffect = 
  | 'zoomIn' 
  | 'zoomOut' 
  | 'panLeft' 
  | 'panRight';

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
  const speedMultiplier = {
    slow: 0.2,    // Subtle movement
    medium: 0.35,  // Moderate movement  
    fast: 0.5      // More movement
  }[speed];
  
  // Calculate progress (0 to 1)
  const progress = interpolate(
    relativeFrame,
    [0, durationInFrames],
    [0, 1],
    { extrapolateRight: 'clamp', extrapolateLeft: 'clamp' }
  );
  
  // Calculate zoom OR pan (never both)
  let zoom = 1;
  let translateX = 0;
  let translateY = 0;
  
  if (effect === 'zoomIn') {
    // Gentle zoom in to show details
    const zoomEnd = 1 + (0.3 * speedMultiplier);
    zoom = interpolate(progress, [0, 1], [1, zoomEnd]);
  } else if (effect === 'zoomOut') {
    // Start zoomed in and pull back to show full room
    const zoomStart = 1 + (0.3 * speedMultiplier);
    zoom = interpolate(progress, [0, 1], [zoomStart, 1]);
  } else if (effect === 'panLeft') {
    // Pan from right to left to scan across the room
    const panDistance = 20 * speedMultiplier; // Percentage of image width
    translateX = interpolate(progress, [0, 1], [panDistance, -panDistance]);
  } else if (effect === 'panRight') {
    // Pan from left to right to scan across the room
    const panDistance = 20 * speedMultiplier; // Percentage of image width
    translateX = interpolate(progress, [0, 1], [-panDistance, panDistance]);
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
export function getEffectForIndex(index: number, isInterior: boolean = true): KenBurnsEffect {
  // Simple effects - alternating between pan and zoom
  const effects: KenBurnsEffect[] = [
    'panRight',   // Pan to see the room
    'zoomIn',     // Zoom to show details
    'panLeft',    // Pan the other direction
    'zoomOut',    // Pull back to see full room
  ];
  
  // For exteriors, prefer zoom effects
  if (!isInterior && (index === 0 || index % 4 < 2)) {
    return index % 2 === 0 ? 'zoomIn' : 'zoomOut';
  }
  
  return effects[index % effects.length];
}