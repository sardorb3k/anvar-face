'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import {
  roomAPI,
  Room,
  RoomDetail,
  Camera,
  CameraCreate,
  RoomCreate,
  getWsUrl,
} from '@/lib/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function RoomsPage() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<RoomDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showAddRoom, setShowAddRoom] = useState(false);
  const [showAddCamera, setShowAddCamera] = useState(false);
  const [newRoomName, setNewRoomName] = useState('');
  const [newCamera, setNewCamera] = useState<CameraCreate>({ name: '', rtsp_url: '' });

  // Camera control states
  const [startingCamera, setStartingCamera] = useState<number | null>(null);
  const [stoppingCamera, setStoppingCamera] = useState<number | null>(null);

  // Camera view states
  const [viewingCamera, setViewingCamera] = useState<Camera | null>(null);
  const [cameraFrames, setCameraFrames] = useState<{ [key: number]: string }>({});
  const wsRefs = useRef<{ [key: number]: WebSocket }>({});
  const streamImgRefs = useRef<{ [key: number]: HTMLImageElement | null }>({});

  // Load rooms
  const loadRooms = async () => {
    try {
      setLoading(true);
      const data = await roomAPI.list();
      setRooms(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Xonalarni yuklashda xatolik');
    } finally {
      setLoading(false);
    }
  };

  // Load room detail
  const loadRoomDetail = async (roomId: number) => {
    try {
      const data = await roomAPI.get(roomId);
      setSelectedRoom(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Xona ma\'lumotlarini yuklashda xatolik');
    }
  };

  useEffect(() => {
    loadRooms();
  }, []);

  // Connect to camera WebSocket for live stream
  const connectCameraWs = useCallback((cameraId: number) => {
    if (wsRefs.current[cameraId]?.readyState === WebSocket.OPEN) return;

    const wsUrl = `${getWsUrl()}/ws/cameras/${cameraId}/stream`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log(`Camera ${cameraId} WebSocket connected`);
    };

    ws.onmessage = (event) => {
      if (event.data instanceof Blob) {
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result as string;
          setCameraFrames(prev => ({ ...prev, [cameraId]: base64 }));
        };
        reader.readAsDataURL(event.data);
      }
    };

    ws.onclose = () => {
      console.log(`Camera ${cameraId} WebSocket disconnected`);
      delete wsRefs.current[cameraId];
    };

    ws.onerror = (error) => {
      console.error(`Camera ${cameraId} WebSocket error:`, error);
    };

    wsRefs.current[cameraId] = ws;
  }, []);

  // Disconnect camera WebSocket
  const disconnectCameraWs = useCallback((cameraId: number) => {
    if (wsRefs.current[cameraId]) {
      wsRefs.current[cameraId].close();
      delete wsRefs.current[cameraId];
    }
    setCameraFrames(prev => {
      const newFrames = { ...prev };
      delete newFrames[cameraId];
      return newFrames;
    });
  }, []);

  // Auto-connect to streaming cameras
  useEffect(() => {
    if (selectedRoom) {
      selectedRoom.cameras.forEach(camera => {
        if (camera.status === 'streaming') {
          connectCameraWs(camera.id);
        } else {
          disconnectCameraWs(camera.id);
        }
      });
    }

    // Cleanup on unmount
    return () => {
      Object.keys(wsRefs.current).forEach(id => {
        wsRefs.current[parseInt(id)]?.close();
      });
    };
  }, [selectedRoom, connectCameraWs, disconnectCameraWs]);

  // Open camera fullscreen view
  const openCameraView = (camera: Camera) => {
    setViewingCamera(camera);
  };

  // Close camera view
  const closeCameraView = () => {
    setViewingCamera(null);
  };

  // Create room
  const handleCreateRoom = async () => {
    if (!newRoomName.trim()) return;

    try {
      await roomAPI.create({ name: newRoomName });
      setNewRoomName('');
      setShowAddRoom(false);
      loadRooms();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Xona yaratishda xatolik');
    }
  };

  // Delete room
  const handleDeleteRoom = async (roomId: number) => {
    if (!confirm('Xonani o\'chirishni tasdiqlaysizmi?')) return;

    try {
      await roomAPI.delete(roomId);
      if (selectedRoom?.id === roomId) {
        setSelectedRoom(null);
      }
      loadRooms();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Xonani o\'chirishda xatolik');
    }
  };

  // Add camera
  const handleAddCamera = async () => {
    if (!selectedRoom || !newCamera.name.trim() || !newCamera.rtsp_url.trim()) return;

    try {
      await roomAPI.addCamera(selectedRoom.id, newCamera);
      setNewCamera({ name: '', rtsp_url: '' });
      setShowAddCamera(false);
      loadRoomDetail(selectedRoom.id);
      loadRooms();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Kamera qo\'shishda xatolik');
    }
  };

  // Delete camera
  const handleDeleteCamera = async (cameraId: number) => {
    if (!selectedRoom || !confirm('Kamerani o\'chirishni tasdiqlaysizmi?')) return;

    try {
      await roomAPI.deleteCamera(selectedRoom.id, cameraId);
      loadRoomDetail(selectedRoom.id);
      loadRooms();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Kamerani o\'chirishda xatolik');
    }
  };

  // Start camera
  const handleStartCamera = async (camera: Camera) => {
    if (!selectedRoom) return;

    try {
      setStartingCamera(camera.id);
      const result = await roomAPI.startCamera(selectedRoom.id, camera.id);
      if (result.success) {
        // Darhol WebSocket'ga ulanish - stream boshlanishini kutmasdan
        connectCameraWs(camera.id);
        // Room detail'ni yangilash
        loadRoomDetail(selectedRoom.id);
      } else {
        setError(result.message);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Kamerani ishga tushirishda xatolik');
    } finally {
      setStartingCamera(null);
    }
  };

  // Stop camera
  const handleStopCamera = async (camera: Camera) => {
    if (!selectedRoom) return;

    try {
      setStoppingCamera(camera.id);
      // WebSocket'ni darhol uzish
      disconnectCameraWs(camera.id);
      await roomAPI.stopCamera(selectedRoom.id, camera.id);
      loadRoomDetail(selectedRoom.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Kamerani to\'xtatishda xatolik');
    } finally {
      setStoppingCamera(null);
    }
  };

  // Start all cameras
  const handleStartAllCameras = async () => {
    if (!selectedRoom) return;

    try {
      const result = await roomAPI.startAllCameras(selectedRoom.id);
      alert(`${result.started} kamera ishga tushdi, ${result.failed} xatolik`);
      loadRoomDetail(selectedRoom.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Kameralarni ishga tushirishda xatolik');
    }
  };

  // Stop all cameras
  const handleStopAllCameras = async () => {
    if (!selectedRoom) return;

    try {
      const result = await roomAPI.stopAllCameras(selectedRoom.id);
      alert(`${result.stopped} kamera to'xtatildi`);
      loadRoomDetail(selectedRoom.id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Kameralarni to\'xtatishda xatolik');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'streaming':
        return 'bg-green-500';
      case 'connected':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'streaming':
        return 'Streaming';
      case 'connected':
        return 'Ulangan';
      default:
        return 'O\'chiq';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Xonalar Boshqaruvi</h1>
            <p className="text-gray-600 mt-1">Xonalar va kameralarni boshqaring</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/monitoring"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Monitoring
            </Link>
            <button
              onClick={() => setShowAddRoom(true)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition"
            >
              + Yangi Xona
            </button>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
            <button onClick={() => setError(null)} className="float-right font-bold">×</button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Rooms List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-md p-4">
              <h2 className="text-xl font-semibold mb-4">Xonalar ({rooms.length})</h2>

              {loading ? (
                <div className="text-center py-8 text-gray-500">Yuklanmoqda...</div>
              ) : rooms.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  Hali xona yo'q. Yangi xona qo'shing.
                </div>
              ) : (
                <div className="space-y-2">
                  {rooms.map((room) => (
                    <div
                      key={room.id}
                      onClick={() => loadRoomDetail(room.id)}
                      className={`p-4 rounded-lg cursor-pointer transition ${
                        selectedRoom?.id === room.id
                          ? 'bg-blue-100 border-2 border-blue-500'
                          : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="font-semibold text-gray-800">{room.name}</h3>
                          <p className="text-sm text-gray-500">
                            {room.camera_count} ta kamera
                          </p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteRoom(room.id);
                          }}
                          className="text-red-500 hover:text-red-700 p-1"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Room Detail */}
          <div className="lg:col-span-2">
            {selectedRoom ? (
              <div className="bg-white rounded-xl shadow-md p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-semibold">{selectedRoom.name}</h2>
                  <div className="flex gap-2">
                    <button
                      onClick={handleStartAllCameras}
                      className="bg-green-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-green-700"
                    >
                      Barchasini Ishga Tushirish
                    </button>
                    <button
                      onClick={handleStopAllCameras}
                      className="bg-red-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-red-700"
                    >
                      Barchasini To'xtatish
                    </button>
                    <button
                      onClick={() => setShowAddCamera(true)}
                      className="bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-blue-700"
                    >
                      + Kamera
                    </button>
                  </div>
                </div>

                {/* Cameras Grid */}
                {selectedRoom.cameras.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <p>Bu xonada hali kamera yo'q</p>
                    <button
                      onClick={() => setShowAddCamera(true)}
                      className="mt-4 text-blue-600 hover:underline"
                    >
                      Kamera qo'shish
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selectedRoom.cameras.map((camera) => (
                      <div key={camera.id} className="border rounded-lg overflow-hidden">
                        {/* Camera Preview */}
                        <div
                          className="relative bg-gray-900 aspect-video cursor-pointer group"
                          onClick={() => camera.status === 'streaming' && openCameraView(camera)}
                        >
                          {camera.status === 'streaming' && cameraFrames[camera.id] ? (
                            <>
                              <img
                                ref={el => { streamImgRefs.current[camera.id] = el; }}
                                src={cameraFrames[camera.id]}
                                alt={camera.name}
                                className="w-full h-full object-contain"
                              />
                              {/* Live badge */}
                              <div className="absolute top-2 right-2 bg-green-500 text-white px-2 py-0.5 rounded-full text-xs font-medium flex items-center">
                                <span className="w-1.5 h-1.5 bg-white rounded-full mr-1 animate-pulse"></span>
                                Live
                              </div>
                              {/* Hover overlay */}
                              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                <div className="bg-white/90 text-gray-800 px-4 py-2 rounded-lg font-medium">
                                  Katta ko'rinish
                                </div>
                              </div>
                            </>
                          ) : (
                            <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                              <div className="text-center">
                                <svg className="w-12 h-12 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                                <p className="text-sm">Stream yo'q</p>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Camera Info */}
                        <div className="p-3">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <h3 className="font-semibold text-gray-800">{camera.name}</h3>
                              <p className="text-xs text-gray-500 truncate max-w-[180px]" title={camera.rtsp_url}>
                                {camera.rtsp_url}
                              </p>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className={`w-2.5 h-2.5 rounded-full ${getStatusColor(camera.status)}`}></span>
                              <span className="text-xs text-gray-600">{getStatusText(camera.status)}</span>
                            </div>
                          </div>

                          <div className="flex gap-2">
                            {camera.status === 'streaming' ? (
                              <>
                                <button
                                  onClick={() => openCameraView(camera)}
                                  className="flex-1 bg-blue-100 text-blue-700 px-2 py-1.5 rounded text-sm hover:bg-blue-200"
                                >
                                  Ko'rish
                                </button>
                                <button
                                  onClick={() => handleStopCamera(camera)}
                                  disabled={stoppingCamera === camera.id}
                                  className="flex-1 bg-red-100 text-red-700 px-2 py-1.5 rounded text-sm hover:bg-red-200 disabled:opacity-50"
                                >
                                  {stoppingCamera === camera.id ? 'To\'xtatilmoqda...' : 'To\'xtatish'}
                                </button>
                              </>
                            ) : (
                              <button
                                onClick={() => handleStartCamera(camera)}
                                disabled={startingCamera === camera.id}
                                className="flex-1 bg-green-100 text-green-700 px-2 py-1.5 rounded text-sm hover:bg-green-200 disabled:opacity-50"
                              >
                                {startingCamera === camera.id ? 'Ulanmoqda...' : 'Ishga Tushirish'}
                              </button>
                            )}
                            <button
                              onClick={() => handleDeleteCamera(camera.id)}
                              className="bg-gray-100 text-gray-700 px-2 py-1.5 rounded text-sm hover:bg-gray-200"
                              title="O'chirish"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-md p-12 text-center text-gray-500">
                <svg className="w-20 h-20 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <p>Xona tanlang yoki yangi xona yarating</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Room Modal */}
      {showAddRoom && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-semibold mb-4">Yangi Xona Qo'shish</h3>
            <input
              type="text"
              placeholder="Xona nomi (masalan: 101-xona)"
              value={newRoomName}
              onChange={(e) => setNewRoomName(e.target.value)}
              className="w-full border rounded-lg px-4 py-2 mb-4"
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowAddRoom(false);
                  setNewRoomName('');
                }}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                Bekor qilish
              </button>
              <button
                onClick={handleCreateRoom}
                disabled={!newRoomName.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Qo'shish
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Camera Modal */}
      {showAddCamera && selectedRoom && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-semibold mb-4">
              {selectedRoom.name} - Kamera Qo'shish
            </h3>
            <input
              type="text"
              placeholder="Kamera nomi (masalan: Asosiy kamera)"
              value={newCamera.name}
              onChange={(e) => setNewCamera({ ...newCamera, name: e.target.value })}
              className="w-full border rounded-lg px-4 py-2 mb-3"
              autoFocus
            />
            <input
              type="text"
              placeholder="RTSP URL (rtsp://user:pass@ip:port/stream)"
              value={newCamera.rtsp_url}
              onChange={(e) => setNewCamera({ ...newCamera, rtsp_url: e.target.value })}
              className="w-full border rounded-lg px-4 py-2 mb-4 font-mono text-sm"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowAddCamera(false);
                  setNewCamera({ name: '', rtsp_url: '' });
                }}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                Bekor qilish
              </button>
              <button
                onClick={handleAddCamera}
                disabled={!newCamera.name.trim() || !newCamera.rtsp_url.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Qo'shish
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Camera Fullscreen View Modal */}
      {viewingCamera && (
        <div
          className="fixed inset-0 bg-black/90 flex items-center justify-center z-50"
          onClick={closeCameraView}
        >
          <div
            className="relative w-full max-w-5xl mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={closeCameraView}
              className="absolute -top-12 right-0 text-white hover:text-gray-300 transition"
            >
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* Camera info header */}
            <div className="bg-gray-900 px-4 py-3 rounded-t-lg flex justify-between items-center">
              <div className="flex items-center gap-3">
                <div className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium flex items-center">
                  <span className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></span>
                  Live
                </div>
                <h3 className="text-white font-semibold text-lg">{viewingCamera.name}</h3>
                {selectedRoom && (
                  <span className="text-gray-400">- {selectedRoom.name}</span>
                )}
              </div>
              <div className="text-gray-400 text-sm">
                {viewingCamera.rtsp_url}
              </div>
            </div>

            {/* Video stream */}
            <div className="bg-black rounded-b-lg overflow-hidden">
              {cameraFrames[viewingCamera.id] ? (
                <img
                  src={cameraFrames[viewingCamera.id]}
                  alt={viewingCamera.name}
                  className="w-full h-auto max-h-[70vh] object-contain"
                />
              ) : (
                <div className="aspect-video flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <p className="text-lg">Stream yuklanmoqda...</p>
                  </div>
                </div>
              )}
            </div>

            {/* Controls */}
            <div className="flex justify-center gap-4 mt-4">
              <button
                onClick={() => {
                  handleStopCamera(viewingCamera);
                  closeCameraView();
                }}
                className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                </svg>
                To'xtatish
              </button>
              <button
                onClick={closeCameraView}
                className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition"
              >
                Yopish
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
