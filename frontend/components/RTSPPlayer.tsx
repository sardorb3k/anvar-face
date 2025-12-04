'use client';

import React, { useEffect, useRef, useState } from 'react';

interface RTSPPlayerProps {
  streamUrl: string;
  isConnected: boolean;
  onError?: (error: string) => void;
}

const RTSPPlayer: React.FC<RTSPPlayerProps> = ({
  streamUrl,
  isConnected,
  onError,
}) => {
  const imgRef = useRef<HTMLImageElement>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (!isConnected || !streamUrl) {
      return;
    }

    // MJPEG stream URL
    const mjpegUrl = streamUrl;
    
    if (imgRef.current) {
      imgRef.current.src = mjpegUrl;
      
      imgRef.current.onerror = () => {
        const errorMsg = 'Stream yuklanmadi';
        setError(errorMsg);
        if (onError) {
          onError(errorMsg);
        }
      };

      imgRef.current.onload = () => {
        setError('');
      };
    }

    return () => {
      if (imgRef.current) {
        imgRef.current.src = '';
      }
    };
  }, [streamUrl, isConnected, onError]);

  if (!isConnected) {
    return (
      <div className="bg-gray-900 rounded-lg flex items-center justify-center h-96">
        <div className="text-white text-center">
          <div className="text-2xl mb-2">📹</div>
          <p>RTSP stream ulanmagan</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-900 rounded-lg flex items-center justify-center h-96">
        <div className="text-red-400 text-center">
          <div className="text-2xl mb-2">⚠️</div>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative bg-gray-900 rounded-lg overflow-hidden">
      <img
        ref={imgRef}
        alt="RTSP Stream"
        className="w-full h-auto max-h-[600px] object-contain"
        style={{ display: 'block' }}
      />
      <div className="absolute top-4 right-4">
        <div className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium flex items-center">
          <div className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></div>
          Live
        </div>
      </div>
    </div>
  );
};

export default RTSPPlayer;

