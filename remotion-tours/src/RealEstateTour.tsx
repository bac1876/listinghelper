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
  watermark?: {
    url: string;
    position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
    opacity?: number;
    scale?: number;
  };
}

export const RealEstateTour: React.FC<RealEstateTourProps> = ({
  images,
  propertyDetails,
  settings,
  watermark,
}) => {
  const { fps } = useVideoConfig();
  
  // Calculate frame durations
  const imageFrames = settings.durationPerImage * fps;
  const transitionFrames = settings.transitionDuration * fps;
  const finalSlideFrames = 5 * fps; // 5 seconds for final slide
  
  // For demo purposes, use sample images if none provided
  const displayImages = images.length > 0 ? images : [
    'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1920&h=1080&fit=crop',
    'https://images.unsplash.com/photo-1484154218962-a197022b5858?w=1920&h=1080&fit=crop',
    'https://images.unsplash.com/photo-1502005229762-cf1b2da7c5d6?w=1920&h=1080&fit=crop',
    'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1920&h=1080&fit=crop',
  ];
  
  // Calculate total duration including final slide
  const imagesTotalDuration = displayImages.length * imageFrames;
  const totalDuration = imagesTotalDuration + finalSlideFrames;
  
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
            {index < displayImages.length - 1 && transitionFrames > 0 && (
              <Sequence from={imageFrames - transitionFrames} durationInFrames={transitionFrames}>
                <TransitionFade duration={settings.transitionDuration} />
              </Sequence>
            )}
          </Sequence>
        );
      })}
      
      {/* Property Details Overlay - Show during images, not on final slide */}
      <Sequence from={30} durationInFrames={Math.max(1, imagesTotalDuration - 60)}>
        <PropertyDetails
          {...propertyDetails}
          position="bottom"
        />
      </Sequence>
      
      {/* Final Call-to-Action Slide */}
      <Sequence from={imagesTotalDuration} durationInFrames={finalSlideFrames}>
        <AbsoluteFill style={{ 
          backgroundColor: '#000',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '60px',
        }}>
          <div style={{
            textAlign: 'center',
            maxWidth: '800px',
          }}>
            <h1 style={{
              color: 'white',
              fontSize: '48px',
              fontWeight: 'bold',
              marginBottom: '40px',
              fontFamily: 'Arial, sans-serif',
              lineHeight: 1.2,
            }}>
              For Your Personal Showing
            </h1>
            <p style={{
              color: 'white',
              fontSize: '36px',
              marginBottom: '20px',
              fontFamily: 'Arial, sans-serif',
            }}>
              Call {propertyDetails.agentName}
            </p>
            <p style={{
              color: '#4CAF50',
              fontSize: '42px',
              fontWeight: 'bold',
              marginBottom: '30px',
              fontFamily: 'Arial, sans-serif',
            }}>
              {propertyDetails.agentPhone}
            </p>
            {propertyDetails.brandName && (
              <p style={{
                color: 'rgba(255, 255, 255, 0.8)',
                fontSize: '24px',
                fontFamily: 'Arial, sans-serif',
              }}>
                {propertyDetails.brandName}
              </p>
            )}
          </div>
        </AbsoluteFill>
      </Sequence>
      
      {/* Watermark Overlay - Show throughout entire video */}
      {watermark && watermark.url && (
        <AbsoluteFill style={{ pointerEvents: 'none' }}>
          <img
            src={watermark.url}
            style={{
              position: 'absolute',
              opacity: watermark.opacity || 0.7,
              width: `${(watermark.scale || 0.15) * 100}%`,
              height: 'auto',
              ...(watermark.position === 'top-left' && { top: 20, left: 20 }),
              ...(watermark.position === 'top-right' && { top: 20, right: 20 }),
              ...(watermark.position === 'bottom-left' && { bottom: 20, left: 20 }),
              ...((watermark.position === 'bottom-right' || !watermark.position) && { bottom: 20, right: 20 }),
            }}
          />
        </AbsoluteFill>
      )}
      
      {/* Optional: Background music */}
      {/* <Audio src={staticFile('background-music.mp3')} volume={0.1} /> */}
    </AbsoluteFill>
  );
};