/**
 * AudioUpload Component
 * Handles file selection and upload initiation
 */

import React, { useRef, useState } from 'react';
import { Upload, FileAudio, X } from 'lucide-react';
import { useApp } from '../context/AppContext';

export const AudioUpload: React.FC = () => {
  const { processFile, isProcessing, currentFile, reset } = useApp();
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFile(files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      handleFile(files[0]);
    }
  };

  const handleFile = (file: File) => {
    // Validate file type
    const validTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/x-wav', 'audio/wave'];
    if (!validTypes.includes(file.type) && !file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
      alert('Please upload a valid audio file (WAV or MP3)');
      return;
    }

    // Process the file
    processFile(file);
  };

  const handleClick = () => {
    inputRef.current?.click();
  };

  const handleRemove = () => {
    reset();
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  if (currentFile) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 border-2 border-primary-500">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FileAudio className="w-8 h-8 text-primary-600" />
            <div>
              <p className="font-medium text-gray-900">{currentFile.name}</p>
              <p className="text-sm text-gray-500">
                {(currentFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          {!isProcessing && (
            <button
              onClick={handleRemove}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              title="Remove file"
            >
              <X className="w-5 h-5 text-gray-600" />
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`
        relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
        transition-all duration-200
        ${dragActive
          ? 'border-primary-500 bg-primary-50'
          : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        }
        ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept="audio/wav,audio/mpeg,audio/mp3,.wav,.mp3"
        onChange={handleChange}
        disabled={isProcessing}
      />

      <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />

      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Upload Audio File
      </h3>

      <p className="text-gray-600 mb-4">
        Drag and drop your audio file here, or click to browse
      </p>

      <p className="text-sm text-gray-500">
        Supported formats: WAV, MP3
      </p>
    </div>
  );
};
