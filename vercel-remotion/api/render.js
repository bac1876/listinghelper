import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';
import path from 'path';
import { uploadToCloudinary } from '../lib/cloudinary';

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { images, propertyDetails, settings } = req.body;

    // Validate input
    if (!images || !Array.isArray(images) || images.length === 0) {
      return res.status(400).json({ error: 'No images provided' });
    }

    // Default settings
    const videoSettings = {
      durationPerImage: 8,
      effectSpeed: 'medium',
      transitionDuration: 1.5,
      ...settings
    };

    // Bundle the Remotion project
    console.log('Bundling Remotion project...');
    const bundleLocation = await bundle({
      entryPoint: path.join(process.cwd(), 'remotion/src/index.tsx'),
      webpackOverride: (config) => config,
    });

    // Select the composition
    const composition = await selectComposition({
      serveUrl: bundleLocation,
      id: 'RealEstateTour',
      inputProps: {
        images,
        propertyDetails,
        settings: videoSettings
      },
    });

    // Calculate duration based on number of images
    const fps = 30;
    const totalDuration = images.length * videoSettings.durationPerImage * fps;

    // Render the video
    console.log('Rendering video...');
    const outputPath = path.join('/tmp', `tour-${Date.now()}.mp4`);
    
    await renderMedia({
      composition: {
        ...composition,
        durationInFrames: totalDuration,
      },
      serveUrl: bundleLocation,
      codec: 'h264',
      outputLocation: outputPath,
      inputProps: {
        images,
        propertyDetails,
        settings: videoSettings
      },
    });

    // Upload to cloud storage (you can use Vercel Blob or Cloudinary)
    console.log('Uploading video...');
    const videoUrl = await uploadToCloudinary(outputPath, `tour-${Date.now()}`);

    // Return the video URL
    return res.status(200).json({
      success: true,
      videoUrl,
      duration: videoSettings.durationPerImage * images.length,
      settings: videoSettings
    });

  } catch (error) {
    console.error('Error rendering video:', error);
    return res.status(500).json({
      error: 'Failed to render video',
      message: error.message
    });
  }
}