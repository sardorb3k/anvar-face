'use client';

import React, { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import Webcam from 'react-webcam';
import { attendanceAPI, AttendanceRecord } from '@/lib/api';
import StudentCard from '@/components/StudentCard';
import AttendanceTable from '@/components/AttendanceTable';

export default function AttendancePage() {
  const webcamRef = useRef<Webcam>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [autoCapture, setAutoCapture] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);
  const [todayAttendance, setTodayAttendance] = useState<AttendanceRecord[]>([]);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);

  // Fetch today's attendance
  const fetchTodayAttendance = async () => {
    try {
      const data = await attendanceAPI.getToday();
      setTodayAttendance(data.records);
    } catch (error) {
      console.error('Failed to fetch attendance:', error);
    }
  };

  useEffect(() => {
    fetchTodayAttendance();
  }, []);

  // Auto-capture every 2 seconds
  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (autoCapture && !isProcessing) {
      interval = setInterval(() => {
        handleCapture();
      }, 2000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoCapture, isProcessing]);

  const handleCapture = async () => {
    if (!webcamRef.current || isProcessing) return;

    const imageSrc = webcamRef.current.getScreenshot();
    if (!imageSrc) return;

    setIsProcessing(true);

    try {
      const result = await attendanceAPI.checkIn(imageSrc);
      setLastResult(result);
      
      // Refresh attendance list if successful
      if (result.status === 'success') {
        await fetchTodayAttendance();
      }
    } catch (error: any) {
      console.error('Check-in failed:', error);
      setLastResult({
        status: 'error',
        message: error.response?.data?.detail || 'Xatolik yuz berdi',
      });
    } finally {
      setIsProcessing(false);
    }
  };

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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Real-time Davomat Olish
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Camera */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Kamera</h2>

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

              {/* Processing overlay */}
              {isProcessing && (
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                  <div className="text-white text-xl font-semibold">
                    Tekshirilmoqda...
                  </div>
                </div>
              )}

              {/* Status indicator */}
              <div className="absolute top-4 right-4">
                <div
                  className={`w-4 h-4 rounded-full ${
                    autoCapture ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
                  }`}
                ></div>
              </div>
            </div>

            {/* Controls */}
            <div className="mt-4 flex space-x-4">
              <button
                onClick={handleCapture}
                disabled={isProcessing || autoCapture}
                className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium"
              >
                📸 Davomat Olish
              </button>
              <button
                onClick={() => setAutoCapture(!autoCapture)}
                className={`flex-1 py-3 rounded-lg font-medium ${
                  autoCapture
                    ? 'bg-red-600 text-white hover:bg-red-700'
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
              >
                {autoCapture ? '⏸ To\'xtatish' : '▶ Avtomatik Rejim'}
              </button>
            </div>

            <div className="mt-2 text-sm text-gray-500 text-center">
              {autoCapture
                ? '⚡ Avtomatik rejim: Har 2 sekundda tekshiriladi'
                : '💡 Avtomatik rejimni yoqib, uzluksiz davomat oling'}
            </div>
          </div>

          {/* Recognition Result */}
          {lastResult && lastResult.student && (
            <StudentCard
              student={lastResult.student}
              confidence={lastResult.confidence || 0}
              status={lastResult.status}
              message={lastResult.message}
              checkInTime={lastResult.check_in_time}
            />
          )}

          {lastResult && !lastResult.student && (
            <div
              className={`p-6 rounded-lg border-2 ${
                lastResult.status === 'error'
                  ? 'bg-red-50 border-red-200'
                  : 'bg-yellow-50 border-yellow-200'
              }`}
            >
              <p
                className={`text-center font-medium ${
                  lastResult.status === 'error' ? 'text-red-800' : 'text-yellow-800'
                }`}
              >
                {lastResult.message}
              </p>
            </div>
          )}
        </div>

        {/* Right Column - Today's Attendance */}
        <div className="lg:col-span-1">
          <div className="bg-white p-6 rounded-lg shadow sticky top-4">
            <h2 className="text-xl font-semibold mb-4">Bugungi Davomat</h2>
            <div className="mb-4 p-4 bg-blue-50 rounded-lg">
              <div className="text-3xl font-bold text-blue-600">
                {todayAttendance.length}
              </div>
              <div className="text-sm text-gray-600">Jami talabalar</div>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {todayAttendance.slice(0, 10).map((record) => (
                <div
                  key={record.id}
                  className="p-3 bg-gray-50 rounded border border-gray-200"
                >
                  <div className="font-medium text-sm">
                    {record.first_name} {record.last_name}
                  </div>
                  <div className="text-xs text-gray-500">
                    {record.student_number} • {record.check_in_time}
                  </div>
                  <div className="text-xs text-green-600">
                    {(record.confidence_score * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>

            {todayAttendance.length > 10 && (
              <div className="mt-2 text-sm text-gray-500 text-center">
                +{todayAttendance.length - 10} boshqalar
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Full Attendance Table */}
      <div className="mt-8 bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">
          Barcha Davomat Ro'yxati
        </h2>
        <AttendanceTable records={todayAttendance} />
      </div>
    </div>
  );
}

