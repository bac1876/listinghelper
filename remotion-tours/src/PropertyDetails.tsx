import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';

interface PropertyDetailsProps {
  address: string;
  city: string;
  details: string;
  status: string;
  agentName: string;
  agentEmail: string;
  agentPhone: string;
  brandName: string;
  position?: 'top' | 'bottom';
}

export const PropertyDetails: React.FC<PropertyDetailsProps> = ({
  address,
  city,
  details,
  status,
  agentName,
  agentEmail,
  agentPhone,
  brandName,
  position = 'bottom'
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Smooth entrance animation
  const slideIn = spring({
    frame,
    fps,
    config: {
      damping: 100,
      mass: 0.5,
    },
  });
  
  // Fade in animation
  const opacity = interpolate(
    frame,
    [0, 30],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );
  
  return (
    <AbsoluteFill
      style={{
        justifyContent: position === 'top' ? 'flex-start' : 'flex-end',
        alignItems: 'flex-start',
        padding: '60px',
      }}
    >
      <div
        style={{
          transform: `translateY(${(1 - slideIn) * (position === 'top' ? -100 : 100)}px)`,
          opacity,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: '40px',
          borderRadius: '10px',
          maxWidth: '600px',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
        }}
      >
        {/* Property Info */}
        <div style={{ marginBottom: '30px' }}>
          <h1
            style={{
              color: 'white',
              fontSize: '42px',
              fontWeight: 'bold',
              margin: 0,
              marginBottom: '10px',
              fontFamily: 'Arial, sans-serif',
            }}
          >
            {address}
          </h1>
          <p
            style={{
              color: 'white',
              fontSize: '28px',
              margin: 0,
              marginBottom: '20px',
              fontFamily: 'Arial, sans-serif',
            }}
          >
            {city}
          </p>
          {status && (
            <div
              style={{
                display: 'inline-block',
                backgroundColor: '#4CAF50',
                color: 'white',
                padding: '8px 20px',
                borderRadius: '25px',
                fontSize: '20px',
                fontWeight: 'bold',
                fontFamily: 'Arial, sans-serif',
              }}
            >
              {status}
            </div>
          )}
        </div>
        
        {/* Call to Action */}
        {details && (
          <p
            style={{
              color: 'white',
              fontSize: '24px',
              margin: 0,
              marginBottom: '30px',
              fontFamily: 'Arial, sans-serif',
              lineHeight: 1.4,
            }}
          >
            {details}
          </p>
        )}
        
        {/* Agent Info */}
        <div
          style={{
            borderTop: '1px solid rgba(255, 255, 255, 0.3)',
            paddingTop: '20px',
          }}
        >
          <p
            style={{
              color: 'white',
              fontSize: '24px',
              margin: 0,
              marginBottom: '5px',
              fontWeight: 'bold',
              fontFamily: 'Arial, sans-serif',
            }}
          >
            {agentName}
          </p>
          <p
            style={{
              color: 'rgba(255, 255, 255, 0.8)',
              fontSize: '20px',
              margin: 0,
              marginBottom: '5px',
              fontFamily: 'Arial, sans-serif',
            }}
          >
            {agentPhone} • {agentEmail}
          </p>
          <p
            style={{
              color: 'rgba(255, 255, 255, 0.8)',
              fontSize: '18px',
              margin: 0,
              fontFamily: 'Arial, sans-serif',
            }}
          >
            {brandName}
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
};