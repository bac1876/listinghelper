import React from 'react';
import { Composition } from 'remotion';
import { RealEstateTour } from './RealEstateTour';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="RealEstateTour"
        component={RealEstateTour}
        durationInFrames={300} // Will be calculated based on images
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          images: [],
          propertyDetails: {
            address: 'Beautiful Property',
            city: 'Los Angeles, CA',
            details: 'Call for viewing',
            status: 'Just Listed',
            agentName: 'Your Agent',
            agentEmail: 'agent@realestate.com',
            agentPhone: '(555) 123-4567',
            brandName: 'Premium Real Estate'
          },
          settings: {
            durationPerImage: 8, // seconds
            effectSpeed: 'medium', // slow, medium, fast
            transitionDuration: 1 // seconds
          }
        }}
      />
    </>
  );
};