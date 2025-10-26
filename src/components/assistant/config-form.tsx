import React, { useState, useEffect } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import { AssistantConfig } from "../../types";

interface ConfigFormProps {
  config: AssistantConfig;
  onSave: (config: AssistantConfig) => Promise<boolean>;
  onSaveAsTemplate: (name: string) => Promise<boolean>;
  onReset?: () => void;
  isLoading: boolean;
}

export const ConfigForm: React.FC<ConfigFormProps> = ({
  config,
  onSave,
  onSaveAsTemplate,
  onReset,
  isLoading,
}) => {
  const [formState, setFormState] = useState<AssistantConfig>(config);
  const [templateName, setTemplateName] = useState("");
  const [showSaveTemplate, setShowSaveTemplate] = useState(false);

  // Update form when config prop changes (when template is loaded)
  useEffect(() => {
    setFormState(config);
  }, [config]);

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;

    // Handle numeric values
    if (["temperature", "chunkSize", "chunkOverlap"].includes(name)) {
      setFormState({
        ...formState,
        [name]: Number(value),
      });
    } else {
      setFormState({
        ...formState,
        [name]: value,
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave(formState);
  };

  const handleSaveTemplate = async () => {
    if (templateName.trim()) {
      const success = await onSaveAsTemplate(templateName);
      if (success) {
        setTemplateName("");
        setShowSaveTemplate(false);
      }
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm"
    >
      <h2 className="text-lg font-semibold mb-4">Configuração do Assistente</h2>

      <div className="space-y-4">
        {/* Basic info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome do Assistente
            </label>
            <Input
              name="name"
              value={formState.name}
              onChange={handleChange}
              placeholder="Nome do assistente"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Modelo
            </label>
            <select
              name="model"
              value={formState.model}
              onChange={handleChange}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Descrição
          </label>
          <Input
            name="description"
            value={formState.description || ""}
            onChange={handleChange}
            placeholder="Descrição breve do assistente"
          />
        </div>

        {/* Advanced settings */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Temperatura
            </label>
            <Input
              type="number"
              name="temperature"
              value={formState.temperature}
              onChange={handleChange}
              step="0.01"
              min="0"
              max="1"
            />
            <p className="text-xs text-gray-500 mt-1">
              Valores mais baixos = respostas mais precisas
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tamanho do Chunk
            </label>
            <Input
              type="number"
              name="chunkSize"
              value={formState.chunkSize}
              onChange={handleChange}
              step="100"
              min="100"
            />
            <p className="text-xs text-gray-500 mt-1">
              Tamanho de cada fragmento de texto
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sobreposição
            </label>
            <Input
              type="number"
              name="chunkOverlap"
              value={formState.chunkOverlap}
              onChange={handleChange}
              step="10"
              min="0"
            />
            <p className="text-xs text-gray-500 mt-1">
              Sobreposição entre fragmentos
            </p>
          </div>
        </div>

        {/* Embedding model */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Modelo de Embedding (Fallback)
          </label>
          <select
            name="embeddingModel"
            value={formState.embeddingModel}
            onChange={handleChange}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <optgroup label="OpenAI - Usado apenas se NVIDIA falhar">
              <option value="text-embedding-3-large">
                text-embedding-3-large (melhor acurácia)
              </option>
              <option value="text-embedding-3-small">
                text-embedding-3-small (economia)
              </option>
            </optgroup>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Sistema usa NVIDIA nv-embedqa-e5-v5 por padrão. Este modelo é usado
            apenas como fallback.
          </p>
        </div>

        {/* Retrieval search type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tipo de Busca
          </label>
          <select
            name="retrievalSearchType"
            value={formState.retrievalSearchType || "mmr"}
            onChange={handleChange}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="mmr">
              MMR - Maximum Marginal Relevance (melhor diversidade)
            </option>
            <option value="similarity">Similarity - Máxima similaridade</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            MMR traz resultados mais diversos, Similarity traz os mais
            relevantes
          </p>
        </div>

        {/* Prompt template */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Template de Prompt
          </label>
          <Textarea
            name="prompt"
            value={formState.prompt}
            onChange={handleChange}
            rows={10}
            className="font-mono text-sm"
          />
          <p className="text-xs text-gray-500 mt-1">
            Use {"{context}"}, {"{chat_history}"} e {"{question}"} como
            variáveis no template
          </p>
        </div>

        {/* Save buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4">
          <Button type="submit" isLoading={isLoading} className="flex-1">
            Salvar Configurações
          </Button>

          {showSaveTemplate ? (
            <div className="flex gap-2 flex-1">
              <Input
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="Nome do template"
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                onClick={handleSaveTemplate}
                disabled={!templateName.trim() || isLoading}
              >
                Salvar
              </Button>
            </div>
          ) : (
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowSaveTemplate(true)}
              className="flex-1"
            >
              Salvar como Template
            </Button>
          )}
        </div>

        {/* Reset button - separate row */}
        {onReset && (
          <div className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onReset}
              disabled={isLoading}
              className="w-full"
            >
              Resetar para Padrão
            </Button>
          </div>
        )}
      </div>
    </form>
  );
};
