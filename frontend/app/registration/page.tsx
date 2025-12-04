'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { studentAPI } from '@/lib/api';

const WebcamCapture = dynamic(() => import('@/components/WebcamCapture'), {
  ssr: false,
});

interface FormData {
  student_id: string;
  first_name: string;
  last_name: string;
  group_name: string;
}

export default function RegistrationPage() {
  const [step, setStep] = useState<1 | 2>(1);
  const [formData, setFormData] = useState<FormData>({
    student_id: '',
    first_name: '',
    last_name: '',
    group_name: '',
  });
  const [capturedImages, setCapturedImages] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleNextStep = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.student_id || !formData.first_name || !formData.last_name) {
      setError('Iltimos, barcha majburiy maydonlarni to\'ldiring');
      return;
    }

    try {
      setIsSubmitting(true);
      await studentAPI.register(formData);
      setStep(2);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Xatolik yuz berdi');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCapture = (imageSrc: string) => {
    setCapturedImages([...capturedImages, imageSrc]);
  };

  const handleRemoveImage = (index: number) => {
    setCapturedImages(capturedImages.filter((_, i) => i !== index));
  };

  const handleSubmitImages = async () => {
    if (capturedImages.length < 5) {
      setError('Kamida 5 ta rasm kerak');
      return;
    }

    try {
      setIsSubmitting(true);
      setError('');

      // Convert base64 to files
      const files = await Promise.all(
        capturedImages.map(async (base64, index) => {
          const response = await fetch(base64);
          const blob = await response.blob();
          return new File([blob], `image_${index}.jpg`, { type: 'image/jpeg' });
        })
      );

      const result = await studentAPI.uploadImages(formData.student_id, files);
      setSuccess(`Muvaffaqiyatli! ${result.successful_uploads} ta rasm yuklandi.`);
      
      // Reset form after 2 seconds
      setTimeout(() => {
        setStep(1);
        setFormData({
          student_id: '',
          first_name: '',
          last_name: '',
          group_name: '',
        });
        setCapturedImages([]);
        setSuccess('');
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Rasmlarni yuklashda xatolik');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Talaba Ro'yxatdan O'tishi
      </h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}

      {/* Progress indicator */}
      <div className="mb-8">
        <div className="flex items-center">
          <div
            className={`flex items-center ${
              step >= 1 ? 'text-blue-600' : 'text-gray-400'
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'
              }`}
            >
              1
            </div>
            <span className="ml-2 font-medium">Ma'lumotlar</span>
          </div>
          <div className="flex-1 h-1 bg-gray-200 mx-4">
            <div
              className={`h-full ${
                step >= 2 ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            ></div>
          </div>
          <div
            className={`flex items-center ${
              step >= 2 ? 'text-blue-600' : 'text-gray-400'
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200'
              }`}
            >
              2
            </div>
            <span className="ml-2 font-medium">Rasmlar</span>
          </div>
        </div>
      </div>

      {/* Step 1: Student Information */}
      {step === 1 && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Talaba Ma'lumotlari</h2>
          <form onSubmit={handleNextStep} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Talaba ID *
              </label>
              <input
                type="text"
                name="student_id"
                value={formData.student_id}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Masalan: 2024001"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ism *
              </label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ism"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Familiya *
              </label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Familiya"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Guruh
              </label>
              <input
                type="text"
                name="group_name"
                value={formData.group_name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Masalan: IT-101"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {isSubmitting ? 'Yuklanmoqda...' : 'Keyingisi'}
            </button>
          </form>
        </div>
      )}

      {/* Step 2: Image Capture */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">
              Rasmlar Olish (5-10 ta)
            </h2>
            <p className="text-gray-600 mb-4">
              {formData.first_name} {formData.last_name} uchun rasmlar oling
            </p>
            <WebcamCapture
              onCapture={handleCapture}
              maxCaptures={10}
              currentCaptures={capturedImages.length}
            />
          </div>

          {/* Captured Images Preview */}
          {capturedImages.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">
                Olingan Rasmlar ({capturedImages.length})
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {capturedImages.map((img, index) => (
                  <div key={index} className="relative">
                    <img
                      src={img}
                      alt={`Capture ${index + 1}`}
                      className="w-full h-32 object-cover rounded border"
                    />
                    <button
                      onClick={() => handleRemoveImage(index)}
                      className="absolute top-1 right-1 bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-700"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex space-x-4">
            <button
              onClick={() => setStep(1)}
              className="flex-1 bg-gray-200 text-gray-700 py-2 rounded-md hover:bg-gray-300"
            >
              Orqaga
            </button>
            <button
              onClick={handleSubmitImages}
              disabled={capturedImages.length < 5 || isSubmitting}
              className="flex-1 bg-green-600 text-white py-2 rounded-md hover:bg-green-700 disabled:bg-gray-400"
            >
              {isSubmitting ? 'Yuklanmoqda...' : 'Yuborish'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

