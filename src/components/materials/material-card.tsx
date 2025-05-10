import React from 'react';
import { Material } from '../../types';
import { formatDate, formatFileSize } from '../../lib/utils';
import { Button } from '../ui/button';
import { BookOpen, Download, Trash2, Edit } from 'lucide-react';
import { motion } from 'framer-motion';

interface MaterialCardProps {
  material: Material;
  onEdit: (material: Material) => void;
  onDelete: (id: string) => void;
  canManage?: boolean;
}

export const MaterialCard: React.FC<MaterialCardProps> = ({
  material,
  onEdit,
  onDelete,
  canManage = false
}) => {
  // Get icon based on material type
  const getIcon = () => {
    switch (material.type) {
      case 'pdf':
        return 'pdf.svg';
      case 'docx':
        return 'docx.svg';
      case 'txt':
        return 'txt.svg';
      case 'video':
        return 'video.svg';
      default:
        return 'file.svg';
    }
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden"
    >
      <div className="flex items-center p-4">
        <div className="w-12 h-12 bg-blue-100 rounded-md flex items-center justify-center mr-4">
          <img src={`/icons/${getIcon()}`} alt={material.type} className="w-6 h-6" />
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-gray-900 truncate">{material.title}</h3>
          
          {material.description && (
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{material.description}</p>
          )}
          
          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
            <span>{formatFileSize(material.size)}</span>
            <span>•</span>
            <span>{formatDate(material.uploadedAt)}</span>
          </div>
        </div>
      </div>
      
      {material.tags && material.tags.length > 0 && (
        <div className="px-4 pb-3 -mt-1 flex flex-wrap gap-1">
          {material.tags.map((tag, index) => (
            <span 
              key={index}
              className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
      
      <div className="border-t border-gray-200 px-4 py-3 bg-gray-50 flex items-center justify-between">
        <Button 
          size="sm"
          variant="outline"
          className="flex items-center gap-1"
          onClick={() => window.open(material.path, '_blank')}
        >
          <BookOpen size={14} />
          <span>Visualizar</span>
        </Button>
        
        <div className="flex items-center gap-2">
          <Button size="icon" variant="ghost" className="h-8 w-8">
            <Download size={16} />
          </Button>
          
          {canManage && (
            <>
              <Button 
                size="icon" 
                variant="ghost" 
                className="h-8 w-8"
                onClick={() => onEdit(material)}
              >
                <Edit size={16} />
              </Button>
              
              <Button 
                size="icon" 
                variant="ghost" 
                className="h-8 w-8 text-red-500 hover:text-red-700"
                onClick={() => onDelete(material.id)}
              >
                <Trash2 size={16} />
              </Button>
            </>
          )}
        </div>
      </div>
    </motion.div>
  );
};