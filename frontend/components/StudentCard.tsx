'use client';

import React from 'react';

interface StudentCardProps {
  student: {
    student_id: string;
    first_name: string;
    last_name: string;
    group_name?: string;
  };
  confidence: number;
  status: 'success' | 'already_attended' | 'error';
  message: string;
  checkInTime?: string;
}

const StudentCard: React.FC<StudentCardProps> = ({
  student,
  confidence,
  status,
  message,
  checkInTime,
}) => {
  const statusColors = {
    success: 'bg-green-50 border-green-200',
    already_attended: 'bg-yellow-50 border-yellow-200',
    error: 'bg-red-50 border-red-200',
  };

  const statusTextColors = {
    success: 'text-green-800',
    already_attended: 'text-yellow-800',
    error: 'text-red-800',
  };

  return (
    <div className={`p-6 rounded-lg border-2 ${statusColors[status]}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
            {student.first_name[0]}{student.last_name[0]}
          </div>
          <div className="ml-4">
            <h3 className="text-xl font-semibold text-gray-900">
              {student.first_name} {student.last_name}
            </h3>
            <p className="text-gray-600">ID: {student.student_id}</p>
            {student.group_name && (
              <p className="text-gray-600">Guruh: {student.group_name}</p>
            )}
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-blue-600">
            {(confidence * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500">Ishonch darajasi</div>
        </div>
      </div>

      <div className={`text-center py-2 rounded font-medium ${statusTextColors[status]}`}>
        {message}
      </div>

      {checkInTime && (
        <div className="mt-2 text-center text-gray-600">
          Vaqt: {checkInTime}
        </div>
      )}
    </div>
  );
};

export default StudentCard;

