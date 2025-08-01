import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

interface TransitionFadeProps {
  duration: number; // in seconds
}

export const TransitionFade: React.FC<TransitionFadeProps> = ({ duration }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const durationInFrames = duration * fps;
  
  const opacity = interpolate(
    frame,
    [0, durationInFrames],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );
  
  return (
    <AbsoluteFill
      style={{
        backgroundColor: 'black',
        opacity,
      }}
    />
  );
};