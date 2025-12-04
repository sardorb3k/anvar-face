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

export default api;

