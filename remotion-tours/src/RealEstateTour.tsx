import React from 'react';
import { AbsoluteFill, Sequence, useVideoConfig, Audio, staticFile } from 'remotion';
import { KenBurnsImage, getEffectForIndex, Speed } from './KenBurnsImage';
import { PropertyDetails } from './PropertyDetails';
import { TransitionFade } from './TransitionFade';

interface RealEstateTourProps {
  images: string[];
  propertyDetails: {
    address: string;
    city: string;
    details: string;
    status: string;
    agentName: string;
    agentEmail: string;
    agentPhone: string;
    brandName: string;
  };
  settings: {
    durationPerImage: number; // seconds
    effectSpeed: Speed;
    transitionDuration: number; // seconds
  };
}

export const RealEstateTour: React.FC<RealEstateTourProps> = ({
  images,
  propertyDetails,
  settings,
}) => {
  const { fps } = useVideoConfig();
  
  // Calculate frame durations
  const imageFrames = settings.durationPerImage * fps;
  const transitionFrames = settings.transitionDuration * fps;
  
  // For demo purposes, use sample images if none provided
  const displayImages = images.length > 0 ? images : [
    'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1920&h=1080&fit=crop',
    'https://images.unsplash.com/photo-1484154218962-a197022b5858?w=1920&h=1080&fit=crop',
    'https://images.unsplash.com/photo-1502005229762-cf1b2da7c5d6?w=1920&h=1080&fit=crop',
    'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1920&h=1080&fit=crop',
  ];
  
  // Calculate total duration
  const totalDuration = displayImages.length * imageFrames;
  
  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {/* Background Images with Ken Burns Effects */}
      {displayImages.map((image, index) => {
        const startFrame = index * imageFrames;
        
        // Detect if image is exterior based on index or URL
        // Typically first and last images are exterior shots
        const isExterior = index === 0 || index === displayImages.length - 1 || 
                          image.toLowerCase().includes('exterior') || 
                          image.toLowerCase().includes('front') ||
                          image.toLowerCase().includes('outside');
        const isInterior = !isExterior;
        
        const effect = getEffectForIndex(index, isInterior);
        
        return (
          <Sequence
            key={`image-${index}`}
            from={startFrame}
            durationInFrames={imageFrames + (index < displayImages.length - 1 ? transitionFrames : 0)}
          >
            <KenBurnsImage
              src={image}
              duration={settings.durationPerImage}
              effect={effect}
              speed={settings.effectSpeed}
              startFrame={0}
              isInterior={isInterior}
            />
            
            {/* Fade transition to next image */}
            {index < displayImages.length - 1 && (
              <Sequence from={imageFrames - transitionFrames}>
                <TransitionFade duration={settings.transitionDuration} />
              </Sequence>
            )}
          </Sequence>
        );
      })}
      
      {/* Property Details Overlay */}
      <Sequence from={30} durationInFrames={totalDuration - 60}>
        <PropertyDetails
          {...propertyDetails}
          position="bottom"
        />
      </Sequence>
      
      {/* Optional: Background music */}
      {/* <Audio src={staticFile('background-music.mp3')} volume={0.1} /> */}
    </AbsoluteFill>
  );
};