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
        padding: '40px',
      }}
    >
      <div
        style={{
          transform: `translateY(${(1 - slideIn) * (position === 'top' ? -100 : 100)}px)`,
          opacity,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: '25px',
          borderRadius: '10px',
          maxWidth: '450px',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
        }}
      >
        {/* Property Info */}
        <div style={{ marginBottom: '20px' }}>
          <h1
            style={{
              color: 'white',
              fontSize: '32px',
              fontWeight: 'bold',
              margin: 0,
              marginBottom: '8px',
              fontFamily: 'Arial, sans-serif',
            }}
          >
            {address}
          </h1>
          <p
            style={{
              color: 'white',
              fontSize: '22px',
              margin: 0,
              marginBottom: '15px',
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
                padding: '6px 16px',
                borderRadius: '20px',
                fontSize: '16px',
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
              fontSize: '18px',
              margin: 0,
              marginBottom: '20px',
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
            paddingTop: '15px',
          }}
        >
          <p
            style={{
              color: 'white',
              fontSize: '20px',
              margin: 0,
              marginBottom: '4px',
              fontWeight: 'bold',
              fontFamily: 'Arial, sans-serif',
            }}
          >
            {agentName}
          </p>
          <p
            style={{
              color: 'rgba(255, 255, 255, 0.8)',
              fontSize: '16px',
              margin: 0,
              marginBottom: '3px',
              fontFamily: 'Arial, sans-serif',
            }}
          >
            {agentPhone} • {agentEmail}
          </p>
          <p
            style={{
              color: 'rgba(255, 255, 255, 0.8)',
              fontSize: '14px',
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