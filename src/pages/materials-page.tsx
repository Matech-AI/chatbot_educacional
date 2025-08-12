import React, { useState, useEffect } from "react";
import { useMaterialsStore } from "../store/materials-store";
import { useAuthStore } from "../store/auth-store";
import { MaterialCard } from "../components/materials/material-card";
import { UploadForm } from "../components/materials/upload-form";
import { DriveSync } from "../components/materials/drive-sync";
import { RecursiveDriveSync } from "../components/materials/recursive-drive-sync";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { BackButton } from "../components/ui/back-button";
import {
  Search,
  Upload,
  X,
  Cloud,
  Zap,
  FolderTree,
  BarChart3,
  Settings,
  RefreshCw,
  HardDrive,
  Database,
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
  const [activeTab, setActiveTab] = useState<
    "materials" | "upload" | "sync" | "recursive" | "stats" | "edit" // Adicionar "edit"
  >("materials");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [folderStructure, setFolderStructure] = useState<any>(null);
  const [driveStats, setDriveStats] = useState<any>(null);
  const [editingMaterial, setEditingMaterial] = useState<Material | null>(null); // Adicionar esta linha

  // Can manage materials if admin or instructor
  const canManage = user?.role === "admin" || user?.role === "instructor";

  // Fetch materials and stats on mount
  useEffect(() => {
    fetchMaterials();
    if (canManage) {
      loadDriveStats();
    }
  }, [fetchMaterials, canManage]);

  const loadDriveStats = async () => {
    try {
      const base = import.meta.env.VITE_API_BASE_URL || "";
      const response = await fetch(`${base}/drive-stats-detailed`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      const contentType = response.headers.get("content-type") || "";
      const text = await response.text();
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${text}`);
      }
      const stats = contentType.includes("application/json")
        ? JSON.parse(text)
        : {};
      setDriveStats(stats);
      setFolderStructure(stats.folder_structure);
    } catch (error) {
      console.error("Error loading drive stats:", error);
    }
  };

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
      loadDriveStats(); // Refresh stats
    }
    return success;
  };

  const handleDelete = async (id: string) => {
    if (window.confirm("Tem certeza que deseja excluir este material?")) {
      await deleteMaterial(id);
      loadDriveStats(); // Refresh stats
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
      loadDriveStats(); // Refresh stats
    }
    return success;
  };

  const handleSync = () => {
    fetchMaterials();
    loadDriveStats();
    setActiveTab("materials");
  };

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    if (tab === "stats") {
      loadDriveStats();
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const renderFolderStructure = (structure: any) => {
    if (!structure || Object.keys(structure).length === 0) {
      return (
        <p className="text-gray-500 text-center py-4">
          Nenhuma estrutura de pastas encontrada
        </p>
      );
    }

    return (
      <div className="space-y-2">
        {Object.entries(structure).map(
          ([folderPath, folderData]: [string, any]) => (
            <div
              key={folderPath}
              className="border border-gray-200 rounded-lg p-3"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <FolderTree size={16} className="text-blue-600" />
                  <span className="font-medium text-sm">
                    {folderPath === "root"
                      ? "📁 Pasta Raiz"
                      : `📂 ${folderPath}`}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>{folderData.file_count} arquivos</span>
                  <span>{formatBytes(folderData.total_size)}</span>
                </div>
              </div>

              {folderData.files && folderData.files.length > 0 && (
                <div className="ml-6 space-y-1">
                  {folderData.files
                    .slice(0, 5)
                    .map((file: any, index: number) => (
                      <div
                        key={index}
                        className="flex items-center justify-between text-xs"
                      >
                        <span className="text-gray-600">📄 {file.name}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-gray-400">
                            {file.type.toUpperCase()}
                          </span>
                          <span className="text-gray-400">
                            {formatBytes(file.size)}
                          </span>
                        </div>
                      </div>
                    ))}
                  {folderData.files.length > 5 && (
                    <div className="text-xs text-gray-500 italic">
                      ... e mais {folderData.files.length - 5} arquivos
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        )}
      </div>
    );
  };

  const tabs = [
    { id: "materials" as const, label: "📚 Materiais", icon: Database },
    ...(canManage
      ? [
          { id: "upload" as const, label: "📤 Upload", icon: Upload },
          { id: "sync" as const, label: "☁️ Sync Simples", icon: Cloud },
          { id: "recursive" as const, label: "⚡ Sync Recursivo", icon: Zap },
          { id: "stats" as const, label: "📊 Estatísticas", icon: BarChart3 },
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
                onClick={() => handleTabChange("recursive")}
                variant={activeTab === "recursive" ? "default" : "outline"}
                className="flex items-center gap-2"
              >
                <Zap size={20} />
                <span>Sync Recursivo</span>
              </Button>

              <Button
                onClick={() => {
                  fetchMaterials();
                  loadDriveStats();
                }}
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
                onClick={() => handleTabChange(tab.id)}
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
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Button
                      onClick={() => handleTabChange("recursive")}
                      variant="outline"
                      className="flex items-center gap-2"
                    >
                      <Zap size={16} />
                      Sync Recursivo
                    </Button>
                    <Button
                      onClick={() => handleTabChange("stats")}
                      variant="outline"
                      className="flex items-center gap-2"
                    >
                      <BarChart3 size={16} />
                      Ver Estatísticas
                    </Button>
                    <Button
                      onClick={() => handleTabChange("upload")}
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
                          onClick={() => handleTabChange("recursive")}
                          variant="outline"
                          className="flex items-center gap-2"
                        >
                          <Zap size={16} />
                          Sincronizar Drive
                        </Button>
                        <Button
                          onClick={() => handleTabChange("upload")}
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

        {activeTab === "stats" && canManage && (
          <motion.div
            key="stats"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Statistics Cards */}
            {driveStats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        Total de Arquivos
                      </p>
                      <p className="text-2xl font-bold text-gray-900">
                        {driveStats.total_files}
                      </p>
                    </div>
                    <Database size={24} className="text-blue-600" />
                  </div>
                </div>

                <div className="bg-white rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        Tamanho Total
                      </p>
                      <p className="text-2xl font-bold text-gray-900">
                        {formatBytes(driveStats.total_size)}
                      </p>
                    </div>
                    <HardDrive size={24} className="text-green-600" />
                  </div>
                </div>

                <div className="bg-white rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        Tipos de Arquivo
                      </p>
                      <p className="text-2xl font-bold text-gray-900">
                        {Object.keys(driveStats.file_types || {}).length}
                      </p>
                    </div>
                    <Settings size={24} className="text-purple-600" />
                  </div>
                </div>

                <div className="bg-white rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        Status Drive
                      </p>
                      <p className="text-lg font-bold text-green-600">
                        {driveStats.drive_authenticated
                          ? "Conectado"
                          : "Desconectado"}
                      </p>
                    </div>
                    <Cloud
                      size={24}
                      className={
                        driveStats.drive_authenticated
                          ? "text-green-600"
                          : "text-red-600"
                      }
                    />
                  </div>
                </div>
              </div>
            )}

            {/* File Types Distribution */}
            {driveStats?.file_types && (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 size={20} />
                  Distribuição de Tipos de Arquivo
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(driveStats.file_types).map(
                    ([type, count]: [string, any]) => (
                      <div
                        key={type}
                        className="text-center p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="text-lg font-bold text-gray-900">
                          {count}
                        </div>
                        <div className="text-sm text-gray-600">
                          {type || "sem extensão"}
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}

            {/* Folder Structure */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <FolderTree size={20} />
                Estrutura de Pastas
              </h3>
              <div className="max-h-96 overflow-y-auto">
                {renderFolderStructure(folderStructure)}
              </div>
            </div>

            {/* Refresh Button */}
            <div className="flex justify-center">
              <Button
                onClick={loadDriveStats}
                variant="outline"
                className="flex items-center gap-2"
              >
                <RefreshCw size={16} />
                Atualizar Estatísticas
              </Button>
            </div>
          </motion.div>
        )}

        {/* Adicionar esta seção para a aba de edição */}
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

// Export default para funcionar com lazy loading
export default MaterialsPage;
