import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, X, Plus, FileText, File, Edit } from 'lucide-react';
import { formatFileSize } from '../../lib/utils';
import { Material } from '../../types';

interface UploadFormProps {
  onUpload: (file: File, description: string, tags: string[]) => Promise<boolean>;
  onUpdate?: (materialId: string, description: string, tags: string[]) => Promise<boolean>;
  isLoading: boolean;
  material?: Material; // Material existente para edição
}

export const UploadForm: React.FC<UploadFormProps> = ({ 
  onUpload, 
  onUpdate, 
  isLoading, 
  material 
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Preencher o formulário com os dados do material existente quando estiver em modo de edição
  useEffect(() => {
    if (material) {
      setIsEditMode(true);
      setDescription(material.description || '');
      setTags(material.tags || []);
    } else {
      setIsEditMode(false);
      setFile(null);
      setDescription('');
      setTags([]);
    }
  }, [material]);
  
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
    
    if (isEditMode && material && onUpdate) {
      // Modo de edição - atualizar metadados
      const success = await onUpdate(material.id, description, tags);
      if (success) {
        // Reset form or close modal/panel
      }
    } else if (file && onUpload) {
      // Modo de upload - criar novo material
      const success = await onUpload(file, description, tags);
      if (success) {
        // Reset form
        setFile(null);
        setDescription('');
        setTags([]);
      }
    }
  };
  
  const removeFile = () => {
    setFile(null);
  };
  
  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
      <h2 className="text-lg font-semibold mb-4">
        {isEditMode ? 'Editar Material' : 'Upload de Material'}
      </h2>
      
      <div className="space-y-4">
        {/* File upload area - mostrar apenas no modo de upload */}
        {!isEditMode ? (
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
              accept=".pdf,.docx,.txt,.pptx"
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
        ) : (
          // Mostrar informações do arquivo no modo de edição
          <div className="border rounded-lg p-4 bg-gray-50">
            <div className="flex items-center">
              <div className="mr-3">
                <FileText size={24} className="text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">{material?.title}</p>
                <p className="text-sm text-gray-500">{formatFileSize(material?.size || 0)}</p>
              </div>
            </div>
          </div>
        )}
        
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
            disabled={(isEditMode ? false : !file) || isLoading}
            isLoading={isLoading}
            className="w-full"
          >
            {isEditMode ? 'Salvar Alterações' : 'Fazer upload'}
          </Button>
        </div>
      </div>
    </form>
  );
};