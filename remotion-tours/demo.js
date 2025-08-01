// Demo script to show how to generate videos with different settings

const settings = {
  slow: {
    durationPerImage: 12, // 12 seconds per image
    effectSpeed: 'slow',
    transitionDuration: 2
  },
  medium: {
    durationPerImage: 8, // 8 seconds per image
    effectSpeed: 'medium',
    transitionDuration: 1.5
  },
  fast: {
    durationPerImage: 4, // 4 seconds per image
    effectSpeed: 'fast',
    transitionDuration: 1
  }
};

console.log('Remotion Real Estate Tour Generator');
console.log('===================================');
console.log('\nTo start the Remotion studio (visual editor):');
console.log('  npm start');
console.log('\nTo render a video with slow Ken Burns:');
console.log(`  npx remotion render RealEstateTour out/slow-tour.mp4 --props='${JSON.stringify({
  settings: settings.slow,
  propertyDetails: {
    address: '123 Beautiful Home',
    city: 'Los Angeles, CA 90210',
    details: 'Call (555) 123-4567 for a viewing',
    status: 'Just Listed',
    agentName: 'Jane Smith',
    agentEmail: 'jane@realestate.com',
    agentPhone: '(555) 123-4567',
    brandName: 'Premium Real Estate'
  }
})}'`);

console.log('\nTo render with medium speed:');
console.log(`  npx remotion render RealEstateTour out/medium-tour.mp4 --props='${JSON.stringify({
  settings: settings.medium
})}'`);

console.log('\nTo render with fast movement:');
console.log(`  npx remotion render RealEstateTour out/fast-tour.mp4 --props='${JSON.stringify({
  settings: settings.fast
})}'`);

console.log('\nKey Features:');
console.log('- Adjustable image duration (4-20 seconds)');
console.log('- Three speed settings for Ken Burns effects');
console.log('- Multiple movement patterns (zoom, pan, combinations)');
console.log('- Smooth transitions between images');
console.log('- Professional property details overlay');