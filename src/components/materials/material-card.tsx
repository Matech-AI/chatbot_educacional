import React from "react";
import { Material } from "../../types";
import { formatDate, formatFileSize } from "../../lib/utils";
import { Button } from "../ui/button";
import { motion } from "framer-motion";

interface MaterialCardProps {
  material: Material;
  onEdit: (material: Material) => void;
  onDelete: (id: string) => void;
  canManage?: boolean;
}

// ========================================
// ÍCONES SVG INLINE
// ========================================
const PDFIcon: React.FC<{ className?: string }> = ({
  className = "w-6 h-6",
}) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M8.267 14.68c-.184 0-.308.018-.372.036v1.178c.076.018.171.023.302.023.479 0 .774-.242.774-.651 0-.366-.254-.586-.704-.586zm3.487.012c-.2 0-.33.018-.407.036v2.61c.077.018.201.018.313.018.817.006 1.349-.444 1.349-1.396.006-.83-.479-1.268-1.255-1.268z" />
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
    <path d="M14 2v6h6" />
    <path d="M10.5 17h-1l-.5-2h-2l-.5 2h-1l2-6h1l2 6zm-2.5-3.5h1.5l-.75-2.25L8.5 13.5z" />
    <path d="M15.5 17h-1l-1.5-2.25L11.5 17h-1l2-3-2-3h1l1.5 2.25L14.5 11h1l-2 3 2 3z" />
  </svg>
);

const DOCXIcon: React.FC<{ className?: string }> = ({
  className = "w-6 h-6",
}) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
    <path d="M14 2v6h6" />
    <path d="M10.5 17h-1l-.5-2h-2l-.5 2h-1l2-6h1l2 6zm-2.5-3.5h1.5l-.75-2.25L8.5 13.5z" />
    <path d="M15.5 17h-1l-1.5-2.25L11.5 17h-1l2-3-2-3h1l1.5 2.25L14.5 11h1l-2 3 2 3z" />
  </svg>
);

const TXTIcon: React.FC<{ className?: string }> = ({
  className = "w-6 h-6",
}) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
    <path d="M14 2v6h6" />
    <path d="M9 13h6" />
    <path d="M9 17h6" />
    <path d="M9 9h1" />
  </svg>
);

const VideoIcon: React.FC<{ className?: string }> = ({
  className = "w-6 h-6",
}) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
    <path d="M14 2v6h6" />
    <path d="m10 11 5 3-5 3v-6z" />
  </svg>
);

const FileIcon: React.FC<{ className?: string }> = ({
  className = "w-6 h-6",
}) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
    <path d="M14 2v6h6" />
  </svg>
);

const DownloadIcon: React.FC<{ className?: string }> = ({
  className = "w-4 h-4",
}) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7,10 12,15 17,10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

const EditIcon: React.FC<{ className?: string }> = ({
  className = "w-4 h-4",
}) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
  </svg>
);

const TrashIcon: React.FC<{ className?: string }> = ({
  className = "w-4 h-4",
}) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <polyline points="3,6 5,6 21,6" />
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    <line x1="10" y1="11" x2="10" y2="17" />
    <line x1="14" y1="11" x2="14" y2="17" />
  </svg>
);

const ExternalLinkIcon: React.FC<{ className?: string }> = ({
  className = "w-4 h-4",
}) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
  >
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    <polyline points="15,3 21,3 21,9" />
    <line x1="10" y1="14" x2="21" y2="3" />
  </svg>
);

export const MaterialCard: React.FC<MaterialCardProps> = ({
  material,
  onEdit,
  onDelete,
  canManage = false,
}) => {
  // ========================================
  // SELETOR DE ÍCONE E COR
  // ========================================
  const getIconAndColor = () => {
    const type = material.type.toLowerCase();

    switch (type) {
      case "pdf":
        return {
          icon: <PDFIcon className="w-6 h-6 text-red-600" />,
          bgColor: "bg-red-50",
          textColor: "text-red-600",
        };
      case "docx":
      case "doc":
        return {
          icon: <DOCXIcon className="w-6 h-6 text-blue-600" />,
          bgColor: "bg-blue-50",
          textColor: "text-blue-600",
        };
      case "txt":
        return {
          icon: <TXTIcon className="w-6 h-6 text-gray-600" />,
          bgColor: "bg-gray-50",
          textColor: "text-gray-600",
        };
      case "video":
      case "mp4":
      case "avi":
      case "mov":
      case "webm":
        return {
          icon: <VideoIcon className="w-6 h-6 text-purple-600" />,
          bgColor: "bg-purple-50",
          textColor: "text-purple-600",
        };
      default:
        return {
          icon: <FileIcon className="w-6 h-6 text-gray-500" />,
          bgColor: "bg-gray-50",
          textColor: "text-gray-500",
        };
    }
  };

  const { icon, bgColor, textColor } = getIconAndColor();

  // ========================================
  // HANDLERS
  // ========================================
  // Removido o handleView que não é mais necessário

  const handleDownload = () => {
    // Para download, adicionamos o parâmetro download=true
    let url;
    if (material.path) {
      // Se já tiver um caminho completo, adicionar o parâmetro download
      url = `${material.path}?download=true`;
    } else {
      // Caso contrário, construir a URL com o ID e o parâmetro download
      url = `/api/materials/${material.id}?download=true`;
    }

    window.open(url, "_blank");
  };

  const handleEdit = () => {
    onEdit(material);
  };

  const handleDelete = () => {
    if (window.confirm(`Tem certeza que deseja excluir "${material.title}"?`)) {
      onDelete(material.id);
    }
  };

  // ========================================
  // RENDER
  // ========================================
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden group"
    >
      {/* Header */}
      <div className="flex items-start p-4">
        {/* Ícone */}
        <div
          className={`w-12 h-12 ${bgColor} rounded-lg flex items-center justify-center mr-4 flex-shrink-0 group-hover:scale-105 transition-transform duration-200`}
        >
          {icon}
        </div>

        {/* Conteúdo */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors duration-200">
            {material.title}
          </h3>

          {material.description && (
            <p className="text-xs text-gray-500 mb-2 line-clamp-2 leading-relaxed">
              {material.description}
            </p>
          )}

          {/* Metadados */}
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span
              className={`px-2 py-1 rounded-full ${bgColor} ${textColor} font-medium`}
            >
              {material.type.toUpperCase()}
            </span>
            <span>•</span>
            <span>{formatFileSize(material.size)}</span>
            <span>•</span>
            <span>{formatDate(material.uploadedAt)}</span>
          </div>
        </div>
      </div>

      {/* Tags */}
      {material.tags && material.tags.length > 0 && (
        <div className="px-4 pb-3">
          <div className="flex flex-wrap gap-1">
            {material.tags.slice(0, 3).map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                {tag}
              </span>
            ))}
            {material.tags.length > 3 && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                +{material.tags.length - 3}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="border-t border-gray-200 px-4 py-3 bg-gray-50 group-hover:bg-gray-100 transition-colors duration-200">
        <div className="flex items-center justify-between">
          {/* Ações */}
          <div className="flex items-center gap-1 ml-auto">
            <button
              onClick={handleDownload}
              className="p-2 rounded-md hover:bg-white hover:shadow-sm transition-all duration-200 text-gray-600 hover:text-blue-600"
              title="Download"
            >
              <DownloadIcon />
            </button>

            {canManage && (
              <>
                <button
                  onClick={handleEdit}
                  className="p-2 rounded-md hover:bg-white hover:shadow-sm transition-all duration-200 text-gray-600 hover:text-green-600"
                  title="Editar"
                >
                  <EditIcon />
                </button>

                <button
                  onClick={handleDelete}
                  className="p-2 rounded-md hover:bg-white hover:shadow-sm transition-all duration-200 text-gray-600 hover:text-red-600"
                  title="Excluir"
                >
                  <TrashIcon />
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};
