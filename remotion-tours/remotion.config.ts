import { Config } from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setStillImageFormat('png');
Config.setOverwriteOutput(true);
Config.setCodec('h264');

export const config = {
  compositions: [{
    id: 'RealEstateTour',
    component: './src/RealEstateTour',
    durationInFrames: 150,
    fps: 30,
    width: 1920,
    height: 1080,
    defaultProps: {
      images: [],
      propertyDetails: {},
      settings: {
        durationPerImage: 8, // seconds
        effectSpeed: 'medium' // slow, medium, fast
      }
    }
  }]
};