'use client';

import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';

interface WebcamCaptureProps {
  onCapture: (imageSrc: string) => void;
  maxCaptures?: number;
  currentCaptures?: number;
}

const WebcamCapture: React.FC<WebcamCaptureProps> = ({
  onCapture,
  maxCaptures = 10,
  currentCaptures = 0,
}) => {
  const webcamRef = useRef<Webcam>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);

  const capture = useCallback(() => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        onCapture(imageSrc);
      }
    }
  }, [onCapture]);

  const videoConstraints = {
    width: 640,
    height: 480,
    facingMode: 'user',
  };

  const handleUserMedia = () => {
    setHasPermission(true);
  };

  const handleUserMediaError = () => {
    setHasPermission(false);
  };

  return (
    <div className="relative">
      {hasPermission === false && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          Kamera ruxsati berilmadi. Iltimos, brauzer sozlamalarida kameraga ruxsat bering.
        </div>
      )}
      
      <div className="relative bg-gray-900 rounded-lg overflow-hidden">
        <Webcam
          audio={false}
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          videoConstraints={videoConstraints}
          onUserMedia={handleUserMedia}
          onUserMediaError={handleUserMediaError}
          className="w-full"
        />
        
        {/* Overlay with face guide */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="border-4 border-blue-500 rounded-full w-64 h-64 opacity-50"></div>
        </div>
      </div>

      <div className="mt-4 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          Rasmlar: {currentCaptures} / {maxCaptures}
        </div>
        <button
          onClick={capture}
          disabled={currentCaptures >= maxCaptures}
          className={`px-6 py-2 rounded-lg font-medium ${
            currentCaptures >= maxCaptures
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          📸 Rasm Olish
        </button>
      </div>

      <div className="mt-2 text-sm text-gray-500">
        💡 Maslahat: Turli burchaklardan va yoritilishda rasmlar oling
      </div>
    </div>
  );
};

export default WebcamCapture;

