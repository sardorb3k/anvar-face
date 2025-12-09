import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Student {
  id: number;
  student_id: string;
  first_name: string;
  last_name: string;
  group_name?: string;
  created_at: string;
}

export interface StudentCreate {
  student_id: string;
  first_name: string;
  last_name: string;
  group_name?: string;
}

export interface AttendanceRecord {
  id: number;
  student_id: number;
  student_number: string;
  first_name: string;
  last_name: string;
  group_name?: string;
  attendance_date: string;
  check_in_time: string;
  confidence_score: number;
  snapshot_path?: string;
}

export interface AttendanceCheckInResponse {
  status: string;
  message: string;
  student?: {
    id: number;
    student_id: string;
    first_name: string;
    last_name: string;
    group_name?: string;
  };
  confidence?: number;
  check_in_time?: string;
  attendance_id?: number;
}

export interface Statistics {
  total_students: number;
  today_attendance: number;
  week_attendance: number;
  month_attendance: number;
  attendance_rate: number;
  date: string;
}

export interface RTSPStatus {
  connected: boolean;
  running: boolean;
  rtsp_url?: string;
  fps: number;
  frame_count: number;
}

export interface RTSPConnectRequest {
  rtsp_url: string;
  timeout?: number;
}

export interface RTSPConnectResponse {
  success: boolean;
  message: string;
  status?: RTSPStatus;
}

export interface RecognitionResult {
  type: string;
  status: string;
  student?: {
    id: number;
    student_id: string;
    first_name: string;
    last_name: string;
    group_name?: string;
  };
  confidence?: number;
  check_in_time?: string;
  attendance_id?: number;
  message?: string;
  timestamp: string;
}

// Student API
export const studentAPI = {
  register: async (data: StudentCreate): Promise<Student> => {
    const response = await api.post('/api/students/register', data);
    return response.data;
  },

  uploadImages: async (studentId: string, files: File[]): Promise<any> => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await api.post(
      `/api/students/${studentId}/upload-images`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  getStudent: async (studentId: string): Promise<Student> => {
    const response = await api.get(`/api/students/${studentId}`);
    return response.data;
  },

  listStudents: async (skip = 0, limit = 100): Promise<Student[]> => {
    const response = await api.get('/api/students/', {
      params: { skip, limit },
    });
    return response.data;
  },

  deleteStudent: async (studentId: string): Promise<any> => {
    const response = await api.delete(`/api/students/${studentId}`);
    return response.data;
  },
};

// Attendance API
export const attendanceAPI = {
  checkIn: async (imageBase64: string): Promise<AttendanceCheckInResponse> => {
    const response = await api.post('/api/attendance/check-in', {
      image: imageBase64,
    });
    return response.data;
  },

  getToday: async (): Promise<{ date: string; total_attendance: number; records: AttendanceRecord[] }> => {
    const response = await api.get('/api/attendance/today');
    return response.data;
  },

  getStudentHistory: async (
    studentId: string,
    dateFrom?: string,
    dateTo?: string
  ): Promise<any> => {
    const response = await api.get(`/api/attendance/student/${studentId}`, {
      params: { date_from: dateFrom, date_to: dateTo },
    });
    return response.data;
  },

  getStatistics: async (): Promise<Statistics> => {
    const response = await api.get('/api/attendance/statistics');
    return response.data;
  },
};

// RTSP API
export const rtspAPI = {
  connect: async (request: RTSPConnectRequest): Promise<RTSPConnectResponse> => {
    const response = await api.post('/api/rtsp/connect', request);
    return response.data;
  },

  disconnect: async (): Promise<RTSPConnectResponse> => {
    const response = await api.post('/api/rtsp/disconnect');
    return response.data;
  },

  getStatus: async (): Promise<RTSPStatus> => {
    const response = await api.get('/api/rtsp/status');
    return response.data;
  },

  getStreamUrl: (): string => {
    const baseUrl = API_URL.replace('http://', '').replace('https://', '');
    return `${API_URL}/api/rtsp/stream`;
  },
};

// ==================== Room Types ====================

export interface Room {
  id: number;
  name: string;
  is_active: boolean;
  created_at: string;
  camera_count: number;
}

export interface RoomDetail extends Room {
  cameras: Camera[];
}

export interface RoomCreate {
  name: string;
}

export interface RoomUpdate {
  name?: string;
  is_active?: boolean;
}

export interface Camera {
  id: number;
  room_id: number;
  name: string;
  rtsp_url: string;
  is_active: boolean;
  created_at: string;
  status: 'connected' | 'streaming' | 'disconnected';
}

export interface CameraCreate {
  name: string;
  rtsp_url: string;
}

export interface CameraUpdate {
  name?: string;
  rtsp_url?: string;
  is_active?: boolean;
}

export interface CameraStatus {
  camera_id: number;
  room_id: number;
  connected: boolean;
  running: boolean;
  rtsp_url: string;
  fps: number;
}

export interface OccupantInfo {
  student_id: number;
  student_number: string;
  first_name: string;
  last_name: string;
  group_name?: string;
  last_seen_at: string;
  confidence: number;
  camera_id?: number;
}

export interface RoomPresence {
  room_id: number;
  room_name: string;
  occupants: OccupantInfo[];
  total_count: number;
}

export interface AllRoomsPresence {
  rooms: RoomPresence[];
  total_people: number;
}

export interface StudentLocation {
  found: boolean;
  room_id?: number;
  room_name?: string;
  last_seen_at?: string;
  confidence?: number;
  camera_id?: number;
}

export interface PresenceStats {
  total_people_tracked: number;
  total_rooms: number;
  occupied_rooms: number;
  presence_timeout_seconds: number;
}

export interface CameraControlResponse {
  success: boolean;
  message: string;
  camera_id: number;
  status?: CameraStatus;
}

// ==================== Room API ====================

export const roomAPI = {
  // Room CRUD
  create: async (data: RoomCreate): Promise<Room> => {
    const response = await api.post('/api/rooms/', data);
    return response.data;
  },

  list: async (includeInactive = false): Promise<Room[]> => {
    const response = await api.get('/api/rooms/', {
      params: { include_inactive: includeInactive },
    });
    return response.data;
  },

  get: async (roomId: number): Promise<RoomDetail> => {
    const response = await api.get(`/api/rooms/${roomId}`);
    return response.data;
  },

  update: async (roomId: number, data: RoomUpdate): Promise<Room> => {
    const response = await api.put(`/api/rooms/${roomId}`, data);
    return response.data;
  },

  delete: async (roomId: number): Promise<void> => {
    await api.delete(`/api/rooms/${roomId}`);
  },

  // Camera CRUD
  addCamera: async (roomId: number, data: CameraCreate): Promise<Camera> => {
    const response = await api.post(`/api/rooms/${roomId}/cameras`, data);
    return response.data;
  },

  listCameras: async (roomId: number, includeInactive = false): Promise<Camera[]> => {
    const response = await api.get(`/api/rooms/${roomId}/cameras`, {
      params: { include_inactive: includeInactive },
    });
    return response.data;
  },

  updateCamera: async (roomId: number, cameraId: number, data: CameraUpdate): Promise<Camera> => {
    const response = await api.put(`/api/rooms/${roomId}/cameras/${cameraId}`, data);
    return response.data;
  },

  deleteCamera: async (roomId: number, cameraId: number): Promise<void> => {
    await api.delete(`/api/rooms/${roomId}/cameras/${cameraId}`);
  },

  // Camera Control
  startCamera: async (roomId: number, cameraId: number, timeout = 30): Promise<CameraControlResponse> => {
    const response = await api.post(`/api/rooms/${roomId}/cameras/${cameraId}/start`, { timeout });
    return response.data;
  },

  stopCamera: async (roomId: number, cameraId: number): Promise<CameraControlResponse> => {
    const response = await api.post(`/api/rooms/${roomId}/cameras/${cameraId}/stop`);
    return response.data;
  },

  startAllCameras: async (roomId: number, timeout = 30): Promise<{ started: number; failed: number }> => {
    const response = await api.post(`/api/rooms/${roomId}/start-all`, { timeout });
    return response.data;
  },

  stopAllCameras: async (roomId: number): Promise<{ stopped: number }> => {
    const response = await api.post(`/api/rooms/${roomId}/stop-all`);
    return response.data;
  },

  // Presence
  getRoomPresence: async (roomId: number): Promise<RoomPresence> => {
    const response = await api.get(`/api/rooms/${roomId}/presence`);
    return response.data;
  },

  getAllPresence: async (): Promise<AllRoomsPresence> => {
    const response = await api.get('/api/rooms/presence/all');
    return response.data;
  },

  getStudentLocation: async (studentId: string): Promise<StudentLocation> => {
    const response = await api.get(`/api/rooms/presence/student/${studentId}`);
    return response.data;
  },

  getPresenceStats: async (): Promise<PresenceStats> => {
    const response = await api.get('/api/rooms/presence/stats');
    return response.data;
  },
};

// WebSocket URL helper
export const getWsUrl = (): string => {
  return API_URL.replace('http://', 'ws://').replace('https://', 'wss://');
};

export default api;

