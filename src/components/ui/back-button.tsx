import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import { Button } from './button';

export const BackButton: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Button
      variant="ghost"
      size="sm"
      className="flex items-center gap-1 text-gray-600 hover:text-gray-900"
      onClick={() => navigate('/')}
    >
      <ChevronLeft size={16} />
      <span>Voltar ao Dashboard</span>
    </Button>
  );
};