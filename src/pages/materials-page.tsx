import React, { useState } from 'react';
import { useMaterialsStore } from '../store/materials-store';
import { useAuthStore } from '../store/auth-store';
import { MaterialCard } from '../components/materials/material-card';
import { UploadForm } from '../components/materials/upload-form';
import { Input } from '../components/ui/input';
import { Search, Upload, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Material } from '../types';

export const MaterialsPage: React.FC = () => {
  const { materials, isProcessing, uploadMaterial, deleteMaterial } = useMaterialsStore();
  const { user } = useAuthStore();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [showUpload, setShowUpload] = useState(false);
  const [materialToEdit, setMaterialToEdit] = useState<Material | null>(null);
  
  // Can manage materials if admin or instructor
  const canManage = user?.role === 'admin' || user?.role === 'instructor';
  
  // Filter materials based on search term
  const filteredMaterials = materials.filter(material =>
    material.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (material.description && material.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (material.tags && material.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase())))
  );
  
  const handleUpload = async (file: File, description: string, tags: string[]) => {
    const success = await uploadMaterial(file, description, tags);
    if (success) {
      setShowUpload(false);
    }
    return success;
  };
  
  const handleDelete = async (id: string) => {
    // Show confirmation dialog
    if (window.confirm('Tem certeza que deseja excluir este material?')) {
      await deleteMaterial(id);
    }
  };
  
  const handleEdit = (material: Material) => {
    setMaterialToEdit(material);
    setShowUpload(true);
  };
  
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <header className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Gerenciamento de Materiais
          </h1>
          <p className="text-gray-600 mt-1">
            Gerencie os materiais do curso para o assistente educacional
          </p>
        </div>
        
        {canManage && (
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            {showUpload ? (
              <>
                <X size={20} />
                <span>Cancelar</span>
              </>
            ) : (
              <>
                <Upload size={20} />
                <span>Upload de Material</span>
              </>
            )}
          </button>
        )}
      </header>
      
      {/* Search and filter */}
      <div className="mb-6">
        <Input
          icon={<Search size={18} />}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Buscar por título, descrição ou tags..."
          className="max-w-xl"
        />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload form */}
        <AnimatePresence>
          {showUpload && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="lg:col-span-1 overflow-hidden"
            >
              <UploadForm 
                onUpload={handleUpload} 
                isLoading={isProcessing} 
              />
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Materials grid */}
        <div className={`grid gap-4 ${showUpload ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
          <AnimatePresence>
            {filteredMaterials.length > 0 ? (
              filteredMaterials.map(material => (
                <MaterialCard
                  key={material.id}
                  material={material}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  canManage={canManage}
                />
              ))
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="col-span-full bg-white rounded-lg border border-gray-200 p-8 text-center"
              >
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search size={24} className="text-gray-400" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Nenhum material encontrado</h3>
                <p className="text-gray-600">
                  {searchTerm 
                    ? `Não foi possível encontrar materiais correspondentes a "${searchTerm}".` 
                    : 'Nenhum material disponível. Faça upload de novos materiais.'}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};