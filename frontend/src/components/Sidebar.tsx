import React, { useState } from 'react';
import axios from 'axios';
import { UploadCloud, CheckCircle, FileText, Info } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setSuccess(false);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setSuccess(false);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post('http://localhost:8000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setSuccess(true);
      setFile(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="w-80 bg-white border-r border-slate-200 flex flex-col h-screen">
      <div className="p-6 border-b border-slate-100 flex items-center gap-3">
        <div className="bg-indigo-600 p-2 rounded-lg text-white">
          <FileText size={24} />
        </div>
        <h1 className="text-xl font-bold text-slate-800 tracking-tight">EduCompanion</h1>
      </div>
      
      <div className="p-6 flex-1 flex flex-col gap-6">
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 text-sm text-slate-600 shadow-sm">
          <h2 className="font-semibold text-slate-800 mb-2 flex items-center gap-2">
            <Info size={16} className="text-indigo-500" />
            How it works
          </h2>
          <p className="mb-2">1. Upload your course materials (PDF).</p>
          <p className="mb-2">2. Chat to ask questions or review concepts.</p>
          <p>3. Ask for a quiz to test your knowledge. You'll get rewards for correct answers and step-by-step help if you miss!</p>
        </div>

        <div className="flex flex-col gap-3 mt-4">
          <h3 className="font-semibold text-slate-700">Upload Study Material</h3>
          
          <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-300 border-dashed rounded-xl cursor-pointer bg-slate-50 hover:bg-slate-100 transition-colors">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <UploadCloud className="w-8 h-8 mb-3 text-slate-400" />
              <p className="mb-2 text-sm text-slate-500">
                <span className="font-semibold">Click to upload</span> or drag and drop
              </p>
              <p className="text-xs text-slate-400">PDF only (MAX. 10MB)</p>
            </div>
            <input type="file" className="hidden" accept=".pdf" onChange={handleFileChange} />
          </label>

          {file && (
            <div className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg border border-indigo-100">
              <span className="text-sm text-indigo-700 truncate w-48">{file.name}</span>
              <button 
                onClick={handleUpload}
                disabled={uploading}
                className="px-3 py-1 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {uploading ? '...' : 'Embed'}
              </button>
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 text-sm text-edu-green bg-emerald-50 p-3 rounded-lg border border-emerald-100 mt-2">
              <CheckCircle size={16} />
              <span>Document embedded successfully!</span>
            </div>
          )}
          
          {error && (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-100 mt-2">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
