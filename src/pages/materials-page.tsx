import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useMaterialsStore } from "../store/materials-store";
import { useAuthStore } from "../store/auth-store";
import { MaterialCard } from "../components/materials/material-card";
import { UploadForm } from "../components/materials/upload-form";
import { DriveSync } from "../components/materials/drive-sync";
import { RecursiveDriveSync } from "../components/materials/recursive-drive-sync";
import { PrivateDriveSync } from "../components/materials/private-drive-sync";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { BackButton } from "../components/ui/back-button";
import {
  Search,
  Upload,
  X,
  Cloud,
  Zap,
  Settings,
  RefreshCw,
  Database,
  UserCircle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Material } from "../types";

interface MaterialsPageProps {}

const MaterialsPage: React.FC<MaterialsPageProps> = () => {
  const {
    materials,
    isLoading,
    isProcessing,
    fetchMaterials,
    uploadMaterial,
    deleteMaterial,
    updateMaterial,
  } = useMaterialsStore();
  const { user } = useAuthStore();

  const [searchTerm, setSearchTerm] = useState("");
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState<
    "materials" | "upload" | "sync" | "recursive" | "edit" | "private-drive"
  >(
    searchParams.get("tab") === "private-drive" ? "private-drive" : "materials"
  );
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState<Material | null>(null);

  // Can manage materials if admin or instructor
  const canManage = user?.role === "admin" || user?.role === "instructor";

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
      setActiveTab("materials");
    }
    return success;
  };

  const handleDelete = async (id: string) => {
    if (window.confirm("Tem certeza que deseja excluir este material?")) {
      await deleteMaterial(id);
    }
  };

  const handleEdit = (material: Material) => {
    setEditingMaterial(material);
    setActiveTab("edit");
  };

  const handleUpdate = async (
    id: string,
    description: string,
    tags: string[]
  ) => {
    const success = await updateMaterial(id, description, tags);
    if (success) {
      setActiveTab("materials");
      setEditingMaterial(null);
    }
    return success;
  };

  const handleSync = () => {
    fetchMaterials();
    setActiveTab("materials");
  };

  const tabs = [
    { id: "materials" as const, label: "📚 Materiais", icon: Database },
    ...(canManage
      ? [
          { id: "upload" as const, label: "📤 Upload", icon: Upload },
          { id: "sync" as const, label: "☁️ Sync Simples", icon: Cloud },
          { id: "recursive" as const, label: "⚡ Sync Recursivo", icon: Zap },
          { id: "private-drive" as const, label: "🔐 Drive Privado", icon: UserCircle },
        ]
      : []),
  ];

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
              {canManage
                ? "Gerencie os materiais com download recursivo automático"
                : "Acesse os materiais de treino disponíveis"}
            </p>
          </div>

          {canManage && (
            <div className="flex gap-2">
              <Button
                onClick={() => setActiveTab("recursive")}
                variant={activeTab === "recursive" ? "default" : "outline"}
                className="flex items-center gap-2"
              >
                <Zap size={20} />
                <span>Sync Recursivo</span>
              </Button>

              <Button
                onClick={() => fetchMaterials()}
                variant="outline"
                className="flex items-center gap-2"
              >
                <RefreshCw size={20} />
                <span>Atualizar</span>
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? "border-red-500 text-red-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <div className="flex items-center gap-2">
                  <tab.icon size={16} />
                  {tab.label}
                </div>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === "materials" && (
          <motion.div
            key="materials"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Search */}
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <Input
                  icon={<Search size={18} />}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Buscar por título, descrição ou tags..."
                />
              </div>

              {canManage && (
                <Button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Settings size={18} />
                  <span>Avançado</span>
                </Button>
              )}
            </div>

            {/* Advanced Options */}
            <AnimatePresence>
              {showAdvanced && canManage && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="bg-gray-50 rounded-lg p-4"
                >
                  <h3 className="font-medium text-gray-900 mb-3">
                    Opções Avançadas
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Button
                      onClick={() => setActiveTab("recursive")}
                      variant="outline"
                      className="flex items-center gap-2"
                    >
                      <Zap size={16} />
                      Sync Recursivo
                    </Button>
                    <Button
                      onClick={() => setActiveTab("upload")}
                      variant="outline"
                      className="flex items-center gap-2"
                    >
                      <Upload size={16} />
                      Upload Manual
                    </Button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Materials Grid */}
            <div className="grid gap-4">
              <AnimatePresence>
                {isLoading ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex justify-center py-12"
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                      <span>Carregando materiais...</span>
                    </div>
                  </motion.div>
                ) : filteredMaterials.length > 0 ? (
                  filteredMaterials.map((material) => (
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
                    className="bg-white rounded-lg border border-gray-200 p-8 text-center"
                  >
                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Search size={24} className="text-gray-400" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">
                      Nenhum material encontrado
                    </h3>
                    <p className="text-gray-600 mb-4">
                      {searchTerm
                        ? `Não foi possível encontrar materiais correspondentes a "${searchTerm}".`
                        : "Nenhum material disponível."}
                    </p>
                    {canManage && !searchTerm && (
                      <div className="flex justify-center gap-2">
                        <Button
                          onClick={() => setActiveTab("recursive")}
                          variant="outline"
                          className="flex items-center gap-2"
                        >
                          <Zap size={16} />
                          Sincronizar Drive
                        </Button>
                        <Button
                          onClick={() => setActiveTab("upload")}
                          variant="outline"
                          className="flex items-center gap-2"
                        >
                          <Upload size={16} />
                          Upload Manual
                        </Button>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}

        {activeTab === "upload" && canManage && (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <UploadForm onUpload={handleUpload} isLoading={isProcessing} />
          </motion.div>
        )}

        {activeTab === "sync" && canManage && (
          <motion.div
            key="sync"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <DriveSync onSync={handleSync} isLoading={isProcessing} />
          </motion.div>
        )}

        {activeTab === "recursive" && canManage && (
          <motion.div
            key="recursive"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <RecursiveDriveSync onSync={handleSync} isLoading={isProcessing} />
          </motion.div>
        )}

        {activeTab === "private-drive" && canManage && (
          <motion.div
            key="private-drive"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <div className="mb-5">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <UserCircle size={20} className="text-red-600" />
                Sincronizar Drive Pessoal
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Baixe arquivos do seu Google Drive pessoal autorizando acesso com sua conta Google.
              </p>
            </div>
            <PrivateDriveSync onSync={handleSync} />
          </motion.div>
        )}

        {activeTab === "edit" && editingMaterial && (
          <motion.div
            key="edit"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <UploadForm
              onUpload={handleUpload}
              onUpdate={(id, description, tags) =>
                handleUpdate(id, description, tags)
              }
              isLoading={isProcessing}
              material={editingMaterial}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MaterialsPage;
