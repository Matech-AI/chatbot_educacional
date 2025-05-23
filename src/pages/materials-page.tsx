import React, { useState, useEffect } from "react";
import { useMaterialsStore } from "../store/materials-store";
import { useAuthStore } from "../store/auth-store";
import { MaterialCard } from "../components/materials/material-card";
import { UploadForm } from "../components/materials/upload-form";
import { DriveSync } from "../components/materials/drive-sync";
import { Input } from "../components/ui/input";
import { BackButton } from "../components/ui/back-button";
import { Search, Upload, X, Cloud } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Material } from "../types";

export const MaterialsPage: React.FC = () => {
  const {
    materials,
    isLoading,
    isProcessing,
    fetchMaterials,
    uploadMaterial,
    deleteMaterial,
  } = useMaterialsStore();
  const { user } = useAuthStore();

  const [searchTerm, setSearchTerm] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [showDriveSync, setShowDriveSync] = useState(false);

  // Can manage materials if admin or instructor
  const canManage = user?.role === "admin" || user?.role === "instructor";

  // Fetch materials on mount
  useEffect(() => {
    fetchMaterials();
  }, [fetchMaterials]);

  // Filter materials based on search term
  const filteredMaterials = materials.filter(
    (material) =>
      material.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (material.description &&
        material.description
          .toLowerCase()
          .includes(searchTerm.toLowerCase())) ||
      (material.tags &&
        material.tags.some((tag) =>
          tag.toLowerCase().includes(searchTerm.toLowerCase())
        ))
  );

  const handleUpload = async (
    file: File,
    description: string,
    tags: string[]
  ) => {
    const success = await uploadMaterial(file, description, tags);
    if (success) {
      setShowUpload(false);
    }
    return success;
  };

  const handleDelete = async (id: string) => {
    if (window.confirm("Tem certeza que deseja excluir este material?")) {
      await deleteMaterial(id);
    }
  };

  const handleDriveSync = () => {
    fetchMaterials();
    setShowDriveSync(false);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <header className="mb-6">
        <BackButton />
        <div className="mt-2 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Materiais de Treino
            </h1>
            <p className="text-gray-600 mt-1">
              Gerencie os materiais do DNA da Força
            </p>
          </div>

          {canManage && (
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setShowUpload(!showUpload);
                  setShowDriveSync(false);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                {showUpload ? (
                  <>
                    <X size={20} />
                    <span>Cancelar</span>
                  </>
                ) : (
                  <>
                    <Upload size={20} />
                    <span>Upload Manual</span>
                  </>
                )}
              </button>

              <button
                onClick={() => {
                  setShowDriveSync(!showDriveSync);
                  setShowUpload(false);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                {showDriveSync ? (
                  <>
                    <X size={20} />
                    <span>Cancelar</span>
                  </>
                ) : (
                  <>
                    <Cloud size={20} />
                    <span>Sincronizar Drive</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
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
        {/* Upload/Sync forms */}
        <AnimatePresence>
          {(showUpload || showDriveSync) && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="lg:col-span-1 overflow-hidden"
            >
              {showUpload ? (
                <UploadForm onUpload={handleUpload} isLoading={isProcessing} />
              ) : (
                <DriveSync onSync={handleDriveSync} isLoading={isProcessing} />
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Materials grid */}
        <div
          className={`grid gap-4 ${
            showUpload || showDriveSync ? "lg:col-span-2" : "lg:col-span-3"
          }`}
        >
          <AnimatePresence>
            {isLoading ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="col-span-full flex justify-center py-12"
              >
                <div className="loading-spinner" />
              </motion.div>
            ) : filteredMaterials.length > 0 ? (
              filteredMaterials.map((material) => (
                <MaterialCard
                  key={material.id}
                  material={material}
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
                <h3 className="text-xl font-semibold mb-2">
                  Nenhum material encontrado
                </h3>
                <p className="text-gray-600">
                  {searchTerm
                    ? `Não foi possível encontrar materiais correspondentes a "${searchTerm}".`
                    : "Nenhum material disponível. Faça upload de novos materiais."}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export async function fetchMaterials() {
  const res = await fetch("/api/materials");
  return await res.json();
}

export async function uploadMaterial(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch("/api/materials/upload", {
    method: "POST",
    body: formData,
  });
  return await res.json();
}

export async function syncDriveMaterials(folderId: string) {
  const res = await fetch("/api/sync-drive", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder_id: folderId }),
  });
  return await res.json();
}
