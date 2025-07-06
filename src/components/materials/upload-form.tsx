import React, { useState, useRef } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, X, Plus, FileText, File } from 'lucide-react';
import { formatFileSize } from '../../lib/utils';

interface UploadFormProps {
  onUpload: (file: File, description: string, tags: string[]) => Promise<boolean>;
  isLoading: boolean;
  onEmbed: () => Promise<void>;
  isEmbedding: boolean;
}

export const UploadForm: React.FC<UploadFormProps> = ({ onUpload, isLoading, onEmbed, isEmbedding }) => {
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleFilesChange = (files: FileList | null) => {
    if (files && files.length > 0) {
      setFile(files[0]);
    }
  };
  
  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };
  
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
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesChange(e.dataTransfer.files);
    }
  };
  
  const addTag = () => {
    const trimmedTag = tagInput.trim();
    if (trimmedTag && !tags.includes(trimmedTag)) {
      setTags([...tags, trimmedTag]);
    }
    setTagInput('');
  };
  
  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag();
    }
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (file) {
      const success = await onUpload(file, description, tags);
      if (success) {
        // Reset form
        setFile(null);
        setDescription('');
        setTags([]);
        setUploadSuccess(true); // Set success state
      }
    }
  };
  
  const removeFile = () => {
    setFile(null);
    setUploadSuccess(false); // Reset success state
  };
  
  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Upload de Material</h2>
      
      <div className="space-y-4">
        {/* File upload area */}
        <div 
          className={`border-2 border-dashed rounded-lg p-6 text-center ${
            dragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300'
          } transition-colors duration-200`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
        >
          <input 
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFilesChange(e.target.files)}
            className="hidden"
            accept=".pdf,.docx,.txt,.mp4,.webm,.mov"
          />
          
          <AnimatePresence mode="wait">
            {file ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="flex flex-col items-center"
              >
                <div className="mb-3 w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <FileText size={24} className="text-blue-600" />
                </div>
                
                <div className="mb-2">
                  <p className="font-medium text-gray-900">{file.name}</p>
                  <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
                </div>
                
                <Button 
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={removeFile}
                  className="flex items-center gap-1 mt-2"
                >
                  <X size={14} />
                  <span>Remover</span>
                </Button>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="flex flex-col items-center"
              >
                <div className="mb-3 w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
                  <Upload size={24} className="text-gray-600" />
                </div>
                
                <p className="mb-1 text-sm text-gray-900">
                  Arraste e solte arquivos aqui ou
                </p>
                
                <Button 
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleBrowseClick}
                  className="mt-2"
                >
                  Procurar arquivos
                </Button>
                
                <p className="mt-2 text-xs text-gray-500">
                  Formatos suportados: PDF, DOCX, TXT, MP4, WEBM, MOV
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        
        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Descrição
          </label>
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Adicione uma descrição para o material..."
            className="w-full"
          />
        </div>
        
        {/* Tags */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tags
          </label>
          
          <div className="flex">
            <Input 
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Adicionar tag"
              className="flex-1"
            />
            
            <Button 
              type="button"
              variant="outline"
              className="ml-2"
              onClick={addTag}
              disabled={!tagInput.trim()}
            >
              <Plus size={16} />
            </Button>
          </div>
          
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {tags.map((tag, index) => (
                <div 
                  key={index}
                  className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-1 rounded-full flex items-center"
                >
                  {tag}
                  <button 
                    type="button"
                    className="ml-1.5 text-blue-700 hover:text-blue-900"
                    onClick={() => removeTag(tag)}
                  >
                    <X size={12} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Submit button */}
        <div className="mt-6">
          <Button 
            type="submit"
            disabled={!file || isLoading}
            isLoading={isLoading}
            className="w-full"
          >
            Fazer upload
          </Button>
        </div>

        {uploadSuccess && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg text-center">
            <p className="text-green-800 font-medium mb-2">
              Upload bem-sucedido!
            </p>
            <p className="text-sm text-gray-600 mb-3">
              Agora você pode adicionar o conhecimento do material à base de dados.
            </p>
            <Button
              type="button"
              onClick={onEmbed}
              disabled={isEmbedding}
              isLoading={isEmbedding}
              variant="success"
              className="w-full"
            >
              {isEmbedding ? "Adicionando..." : "Adicionar Conhecimento"}
            </Button>
          </div>
        )}
      </div>
    </form>
  );
};