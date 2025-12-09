'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import {
  roomAPI,
  RoomPresence,
  OccupantInfo,
  PresenceStats,
  getWsUrl,
} from '@/lib/api';

export default function MonitoringPage() {
  const [rooms, setRooms] = useState<RoomPresence[]>([]);
  const [totalPeople, setTotalPeople] = useState(0);
  const [stats, setStats] = useState<PresenceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [wsConnected, setWsConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Load initial data
  const loadData = async () => {
    try {
      setLoading(true);
      const [presenceData, statsData] = await Promise.all([
        roomAPI.getAllPresence(),
        roomAPI.getPresenceStats(),
      ]);

      setRooms(presenceData.rooms);
      setTotalPeople(presenceData.total_people);
      setStats(statsData);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ma\'lumotlarni yuklashda xatolik');
    } finally {
      setLoading(false);
    }
  };

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = `${getWsUrl()}/ws/rooms/all/presence`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setWsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'initial_all_presence' || data.type === 'all_presence_refresh') {
          setRooms(data.rooms);
          setTotalPeople(data.total_people);
        } else if (data.type === 'presence_update') {
          // Update specific room
          setRooms((prevRooms) => {
            const updated = [...prevRooms];
            const index = updated.findIndex((r) => r.room_id === data.room_id);

            if (index >= 0) {
              updated[index] = {
                room_id: data.room_id,
                room_name: data.room_name,
                occupants: data.occupants,
                total_count: data.total_count,
              };
            }

            // Recalculate total
            const newTotal = updated.reduce((sum, r) => sum + r.total_count, 0);
            setTotalPeople(newTotal);

            return updated;
          });
        }
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnected(false);

      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket ulanishda xatolik');
    };

    wsRef.current = ws;
  }, []);

  // Cleanup
  useEffect(() => {
    loadData();
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connectWebSocket]);

  // Filter occupants by search query
  const getFilteredOccupants = (occupants: OccupantInfo[]) => {
    if (!searchQuery.trim()) return occupants;

    const query = searchQuery.toLowerCase();
    return occupants.filter(
      (o) =>
        o.first_name.toLowerCase().includes(query) ||
        o.last_name.toLowerCase().includes(query) ||
        o.student_number.toLowerCase().includes(query) ||
        (o.group_name && o.group_name.toLowerCase().includes(query))
    );
  };

  // Find student location
  const findStudent = () => {
    if (!searchQuery.trim()) return null;

    const query = searchQuery.toLowerCase();
    for (const room of rooms) {
      const found = room.occupants.find(
        (o) =>
          o.first_name.toLowerCase().includes(query) ||
          o.last_name.toLowerCase().includes(query) ||
          o.student_number.toLowerCase().includes(query)
      );
      if (found) {
        return { room, student: found };
      }
    }
    return null;
  };

  const foundResult = searchQuery.trim() ? findStudent() : null;

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800">Real-time Monitoring</h1>
            <p className="text-gray-600">Xonalardagi kishilarni real vaqtda kuzating</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* WebSocket Status */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
              wsConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
              {wsConnected ? 'Live' : 'Offline'}
            </div>

            <Link
              href="/rooms"
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition text-sm"
            >
              Xonalar Boshqaruvi
            </Link>

            <button
              onClick={loadData}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm"
            >
              Yangilash
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-md p-4">
            <div className="text-3xl font-bold text-blue-600">{totalPeople}</div>
            <div className="text-gray-600 text-sm">Jami Odamlar</div>
          </div>
          <div className="bg-white rounded-xl shadow-md p-4">
            <div className="text-3xl font-bold text-green-600">{stats?.occupied_rooms || 0}</div>
            <div className="text-gray-600 text-sm">Band Xonalar</div>
          </div>
          <div className="bg-white rounded-xl shadow-md p-4">
            <div className="text-3xl font-bold text-purple-600">{stats?.total_rooms || 0}</div>
            <div className="text-gray-600 text-sm">Jami Xonalar</div>
          </div>
          <div className="bg-white rounded-xl shadow-md p-4">
            <div className="text-3xl font-bold text-orange-600">{stats?.presence_timeout_seconds || 30}s</div>
            <div className="text-gray-600 text-sm">Timeout</div>
          </div>
        </div>

        {/* Search */}
        <div className="bg-white rounded-xl shadow-md p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            <div className="relative flex-1 w-full">
              <input
                type="text"
                placeholder="Talabani qidirish (ism, familiya, ID)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full border rounded-lg px-4 py-2 pl-10"
              />
              <svg
                className="absolute left-3 top-2.5 w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>

            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="text-gray-500 hover:text-gray-700"
              >
                Tozalash
              </button>
            )}
          </div>

          {/* Search Result */}
          {foundResult && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-green-600 text-white rounded-full flex items-center justify-center text-xl font-bold">
                  {foundResult.student.first_name[0]}
                </div>
                <div>
                  <div className="font-semibold">
                    {foundResult.student.first_name} {foundResult.student.last_name}
                  </div>
                  <div className="text-sm text-gray-600">
                    ID: {foundResult.student.student_number}
                    {foundResult.student.group_name && ` • ${foundResult.student.group_name}`}
                  </div>
                </div>
                <div className="ml-auto text-right">
                  <div className="text-lg font-semibold text-green-700">
                    {foundResult.room.room_name}
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatTime(foundResult.student.last_seen_at)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {searchQuery && !foundResult && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700">
              "{searchQuery}" bo'yicha hech kim topilmadi
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
            <button onClick={() => setError(null)} className="float-right font-bold">×</button>
          </div>
        )}

        {/* Rooms Grid */}
        {loading ? (
          <div className="text-center py-12 text-gray-500">Yuklanmoqda...</div>
        ) : rooms.length === 0 ? (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <svg className="w-20 h-20 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <p className="text-gray-500 mb-4">Hali xona qo'shilmagan</p>
            <Link href="/rooms" className="text-blue-600 hover:underline">
              Xona qo'shish
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {rooms.map((room) => {
              const filteredOccupants = getFilteredOccupants(room.occupants);
              const isHighlighted = searchQuery && filteredOccupants.length > 0;

              return (
                <div
                  key={room.room_id}
                  className={`bg-white rounded-xl shadow-md overflow-hidden transition ${
                    isHighlighted ? 'ring-2 ring-green-500' : ''
                  }`}
                >
                  {/* Room Header */}
                  <div className={`px-4 py-3 ${
                    room.total_count > 0 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
                  }`}>
                    <div className="flex justify-between items-center">
                      <h3 className="font-semibold text-lg">{room.room_name}</h3>
                      <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                        room.total_count > 0 ? 'bg-white text-blue-600' : 'bg-gray-300 text-gray-600'
                      }`}>
                        {room.total_count} kishi
                      </span>
                    </div>
                  </div>

                  {/* Occupants List */}
                  <div className="p-4 max-h-64 overflow-y-auto">
                    {filteredOccupants.length === 0 ? (
                      <div className="text-center py-6 text-gray-400">
                        {room.total_count === 0 ? (
                          <p>Xonada hech kim yo'q</p>
                        ) : (
                          <p>Qidiruv bo'yicha topilmadi</p>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {filteredOccupants.map((occupant) => (
                          <div
                            key={occupant.student_id}
                            className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50"
                          >
                            <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-semibold">
                              {occupant.first_name[0]}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-gray-800 truncate">
                                {occupant.first_name} {occupant.last_name}
                              </div>
                              <div className="text-xs text-gray-500">
                                {occupant.student_number}
                                {occupant.group_name && ` • ${occupant.group_name}`}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className={`text-sm font-medium ${getConfidenceColor(occupant.confidence)}`}>
                                {(occupant.confidence * 100).toFixed(0)}%
                              </div>
                              <div className="text-xs text-gray-400">
                                {formatTime(occupant.last_seen_at)}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
