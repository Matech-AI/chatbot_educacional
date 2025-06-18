import React, { useEffect } from 'react';
import { useDocumentStore, Document } from '../store/document-store';
import { Button } from '../components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Trash2 } from 'lucide-react';
import { format } from 'date-fns';

export const DocumentsPage: React.FC = () => {
  const { documents, isLoading, error, fetchDocuments, deleteDocument } = useDocumentStore();

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleDelete = async (filename: string, kbId: string) => {
    if (window.confirm(`Are you sure you want to delete ${filename}?`)) {
      await deleteDocument(filename, kbId);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Document Management</h1>
      <Card>
        <CardHeader>
          <CardTitle>Documents in Vector Store</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading && <p>Loading documents...</p>}
          {error && <p className="text-red-500">{error}</p>}
          {!isLoading && !error && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Filename</TableHead>
                  <TableHead>Knowledge Base</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((doc: Document) => (
                  <TableRow key={doc.filename}>
                    <TableCell>{doc.filename}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{doc.knowledge_base_id}</Badge>
                    </TableCell>
                    <TableCell>
                      {doc.last_updated ? format(new Date(doc.last_updated * 1000), 'PPpp') : 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDelete(doc.filename, doc.knowledge_base_id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};