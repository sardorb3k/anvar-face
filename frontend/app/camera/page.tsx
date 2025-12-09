'use client';

import React, { useState, useEffect, useRef } from 'react';
import { rtspAPI, RecognitionResult, RTSPStatus } from '@/lib/api';
import StudentCard from '@/components/StudentCard';
import { attendanceAPI, AttendanceRecord } from '@/lib/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = API_URL.replace('http://', 'ws://').replace('https://', 'wss://');

// Overlay ko'rinish vaqti (soniyalarda)
const OVERLAY_DISPLAY_TIME = 5000; // 5 soniya

export default function CameraPage() {
  const [rtspUrl, setRtspUrl] = useState<string>('');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [status, setStatus] = useState<RTSPStatus | null>(null);
  const [error, setError] = useState<string>('');
  const [lastRecognition, setLastRecognition] = useState<RecognitionResult | null>(null);
  const [recognitionHistory, setRecognitionHistory] = useState<RecognitionResult[]>([]);
  const [todayAttendance, setTodayAttendance] = useState<AttendanceRecord[]>([]);
  const [showOverlay, setShowOverlay] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const streamImgRef = useRef<HTMLImageElement>(null);
  const overlayTimeoutRef = useRef<NodeJS.Timeout | null>(null);

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
    checkStatus();

    // Check status periodically
    const interval = setInterval(checkStatus, 5000);
    return () => {
      clearInterval(interval);
      // Cleanup overlay timeout
      if (overlayTimeoutRef.current) {
        clearTimeout(overlayTimeoutRef.current);
      }
    };
  }, []);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (isConnected) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [isConnected]);

  const checkStatus = async () => {
    try {
      const currentStatus = await rtspAPI.getStatus();
      setStatus(currentStatus);
      setIsConnected(currentStatus.connected);
    } catch (error) {
      console.error('Failed to check status:', error);
    }
  };

  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const ws = new WebSocket(`${WS_URL}/ws/rtsp/stream`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      // Check if it's binary (frame) or text (JSON message)
      if (event.data instanceof Blob) {
        // Binary data - MJPEG frame
        const reader = new FileReader();
        reader.onload = () => {
          if (streamImgRef.current) {
            streamImgRef.current.src = reader.result as string;
          }
        };
        reader.readAsDataURL(event.data);
      } else {
        // JSON message - recognition result or status
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'recognition') {
            // Backend sends 'recognized' array with multiple students
            if (message.recognized && message.recognized.length > 0) {
              // Get the first recognized student for overlay display
              const firstStudent = message.recognized[0];

              // Transform to expected format for overlay
              const recognitionData: RecognitionResult = {
                type: 'recognition',
                status: firstStudent.status || 'success',
                student: {
                  id: firstStudent.id,
                  student_id: firstStudent.student_id,
                  first_name: firstStudent.first_name,
                  last_name: firstStudent.last_name,
                  group_name: firstStudent.group_name,
                },
                confidence: firstStudent.confidence,
                check_in_time: firstStudent.check_in_time,
                attendance_id: firstStudent.attendance_id,
                timestamp: message.timestamp,
              };

              setLastRecognition(recognitionData);

              // Add all recognized students to history
              message.recognized.forEach((student: any) => {
                const studentRecognition: RecognitionResult = {
                  type: 'recognition',
                  status: student.status || 'success',
                  student: {
                    id: student.id,
                    student_id: student.student_id,
                    first_name: student.first_name,
                    last_name: student.last_name,
                    group_name: student.group_name,
                  },
                  confidence: student.confidence,
                  check_in_time: student.check_in_time,
                  timestamp: message.timestamp,
                };
                setRecognitionHistory(prev => [studentRecognition, ...prev.slice(0, 9)]);
              });

              // Show overlay
              setShowOverlay(true);
              if (overlayTimeoutRef.current) {
                clearTimeout(overlayTimeoutRef.current);
              }
              overlayTimeoutRef.current = setTimeout(() => {
                setShowOverlay(false);
              }, OVERLAY_DISPLAY_TIME);

              // Refresh attendance if any student has success status
              const hasNewAttendance = message.recognized.some(
                (s: any) => s.status === 'success'
              );
              if (hasNewAttendance) {
                fetchTodayAttendance();
              }
            }
          } else if (message.type === 'status') {
            setStatus(message);
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Try to reconnect if still connected
      if (isConnected) {
        setTimeout(connectWebSocket, 2000);
      }
    };

    wsRef.current = ws;
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const handleConnect = async () => {
    if (!rtspUrl.trim()) {
      setError('Iltimos, RTSP link kiriting');
      return;
    }

    if (!rtspUrl.startsWith('rtsp://') && !rtspUrl.startsWith('rtsps://')) {
      setError('Noto\'g\'ri RTSP link formati. rtsp:// yoki rtsps:// bilan boshlanishi kerak');
      return;
    }

    setIsConnecting(true);
    setError('');

    try {
      const response = await rtspAPI.connect({
        rtsp_url: rtspUrl,
        timeout: 30,
      });

      if (response.success) {
        setIsConnected(true);
        setStatus(response.status || null);
        setError('');
      } else {
        setError(response.message || 'RTSP ga ulanib bo\'lmadi');
        setIsConnected(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Xatolik yuz berdi');
      setIsConnected(false);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    setIsConnecting(true);
    try {
      await rtspAPI.disconnect();
      setIsConnected(false);
      setStatus(null);
      setLastRecognition(null);
      setRecognitionHistory([]);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Uzilishda xatolik');
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        RTSP Kamera - Real-time Davomat
      </h1>

      {/* RTSP Connection Form */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-xl font-semibold mb-4">RTSP Kamera Ulanishi</h2>
        
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="flex gap-4">
          <div className="flex-1">
            <input
              type="text"
              value={rtspUrl}
              onChange={(e) => setRtspUrl(e.target.value)}
              placeholder="rtsp://user:password@ip:port/stream"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isConnecting || isConnected}
            />
            <p className="text-sm text-gray-500 mt-2">
              Misol: rtsp://admin:password@192.168.1.100:554/stream1
            </p>
          </div>
          
          {!isConnected ? (
            <button
              onClick={handleConnect}
              disabled={isConnecting}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium"
            >
              {isConnecting ? 'Ulanmoqda...' : 'Ulanish'}
            </button>
          ) : (
            <button
              onClick={handleDisconnect}
              disabled={isConnecting}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 font-medium"
            >
              {isConnecting ? 'Uzilmoqda...' : 'Uzish'}
            </button>
          )}
        </div>

        {/* Status */}
        {status && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Holat:</span>
                <span className={`ml-2 font-medium ${status.connected ? 'text-green-600' : 'text-red-600'}`}>
                  {status.connected ? '✅ Ulangan' : '❌ Uzilgan'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">FPS:</span>
                <span className="ml-2 font-medium">{status.fps.toFixed(1)}</span>
              </div>
              <div>
                <span className="text-gray-600">Frame:</span>
                <span className="ml-2 font-medium">{status.frame_count}</span>
              </div>
              <div>
                <span className="text-gray-600">Stream:</span>
                <span className={`ml-2 font-medium ${status.running ? 'text-green-600' : 'text-gray-600'}`}>
                  {status.running ? 'Ishlamoqda' : 'To\'xtatilgan'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Video Stream */}
        <div className="lg:col-span-2 space-y-6">
          {/* RTSP Stream */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Kamera Oqimi</h2>
            
            {/* WebSocket Stream Image */}
            {isConnected && (
              <div className="relative bg-gray-900 rounded-lg overflow-hidden">
                <img
                  ref={streamImgRef}
                  alt="RTSP Stream"
                  className="w-full h-auto max-h-[600px] object-contain"
                  style={{ display: 'block' }}
                />
                {/* Live indicator */}
                <div className="absolute top-4 right-4">
                  <div className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium flex items-center">
                    <div className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></div>
                    Live
                  </div>
                </div>

                {/* So'nggi tanilgan student - kamera ustida overlay */}
                {showOverlay && lastRecognition && lastRecognition.student && (
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 animate-fade-in-up">
                    <div className={`flex items-center justify-between ${
                      lastRecognition.status === 'success'
                        ? 'text-green-400'
                        : lastRecognition.status === 'already_attended'
                        ? 'text-yellow-400'
                        : 'text-white'
                    }`}>
                      <div className="flex items-center space-x-3">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold ${
                          lastRecognition.status === 'success'
                            ? 'bg-green-500 text-white'
                            : lastRecognition.status === 'already_attended'
                            ? 'bg-yellow-500 text-white'
                            : 'bg-gray-500 text-white'
                        }`}>
                          {lastRecognition.student.first_name.charAt(0)}
                        </div>
                        <div>
                          <div className="text-xl font-bold text-white">
                            {lastRecognition.student.first_name} {lastRecognition.student.last_name}
                          </div>
                          <div className="text-sm text-gray-300">
                            {lastRecognition.student.student_id}
                            {lastRecognition.student.group_name && ` • ${lastRecognition.student.group_name}`}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-2xl font-bold ${
                          (lastRecognition.confidence || 0) >= 0.7
                            ? 'text-green-400'
                            : (lastRecognition.confidence || 0) >= 0.5
                            ? 'text-yellow-400'
                            : 'text-red-400'
                        }`}>
                          {((lastRecognition.confidence || 0) * 100).toFixed(0)}%
                        </div>
                        <div className={`text-sm font-medium ${
                          lastRecognition.status === 'success'
                            ? 'text-green-400'
                            : lastRecognition.status === 'already_attended'
                            ? 'text-yellow-400'
                            : 'text-gray-400'
                        }`}>
                          {lastRecognition.status === 'success' && '✓ Davomat qabul qilindi'}
                          {lastRecognition.status === 'already_attended' && '⚠ Allaqachon qayd etilgan'}
                          {lastRecognition.status === 'no_match' && '✗ Tanilmadi'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {!isConnected && (
              <div className="bg-gray-900 rounded-lg flex items-center justify-center h-96">
                <div className="text-white text-center">
                  <div className="text-4xl mb-4">📹</div>
                  <p className="text-lg">RTSP kamera ulanmagan</p>
                  <p className="text-sm text-gray-400 mt-2">
                    Yuqoridagi formadan RTSP link kiriting va "Ulanish" tugmasini bosing
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Last Recognition Result */}
          {lastRecognition && lastRecognition.student && (
            <StudentCard
              student={lastRecognition.student}
              confidence={lastRecognition.confidence || 0}
              status={lastRecognition.status as any}
              message={
                lastRecognition.status === 'success'
                  ? 'Davomat muvaffaqiyatli qabul qilindi'
                  : lastRecognition.status === 'already_attended'
                  ? 'Siz allaqachon davomat qilgansiz'
                  : lastRecognition.message || ''
              }
              checkInTime={lastRecognition.check_in_time}
            />
          )}

          {/* Recognition History */}
          {recognitionHistory.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">So'nggi Tanishlar</h3>
              <div className="space-y-2">
                {recognitionHistory.map((result, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded border ${
                      result.status === 'success'
                        ? 'bg-green-50 border-green-200'
                        : result.status === 'already_attended'
                        ? 'bg-yellow-50 border-yellow-200'
                        : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        {result.student && (
                          <span className="font-medium">
                            {result.student.first_name} {result.student.last_name}
                          </span>
                        )}
                        <span className="text-sm text-gray-600 ml-2">
                          ({result.status})
                        </span>
                      </div>
                      {result.confidence && (
                        <span className="text-sm font-medium">
                          {(result.confidence * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
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
    </div>
  );
}

