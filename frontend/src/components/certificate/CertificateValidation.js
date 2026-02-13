import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import StatusBadge from './StatusBadge';
import { 
  Download, 
  Copy, 
  Share2, 
  ExternalLink, 
  Calendar,
  User,
  Package,
  Hash,
  MapPin,
  Shield,
  CheckCircle,
  Clock,
  QrCode
} from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { toast } from 'sonner';

/**
 * CertificateValidation - Página pública de validação de certificado
 * Acessada via QR Code ou link direto
 */
const CertificateValidation = () => {
  const { code } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [certificate, setCertificate] = useState(null);
  const [validation, setValidation] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking');

  useEffect(() => {
    fetchCertificate();
  }, [code]);

  const fetchCertificate = async () => {
    try {
      setLoading(true);
      setServerStatus('checking');
      
      // Criar instância axios sem interceptors para chamada pública
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/certificates/${code}`
      );
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Certificado não encontrado');
        }
        throw new Error('Erro ao validar certificado');
      }
      
      const data = await response.json();
      
      setCertificate(data.certificate);
      setValidation(data.validation);
      setServerStatus('online');
      setError(null);
      
    } catch (err) {
      console.error('Erro ao buscar certificado:', err);
      setError(err.message);
      setServerStatus('offline');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/certificates/${code}/pdf`
      );
      
      if (!response.ok) throw new Error('Erro ao baixar PDF');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `certificado_${certificate?.certificate_number || code}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('PDF baixado com sucesso!');
    } catch (err) {
      toast.error('Erro ao baixar PDF');
    }
  };

  const handleCopyLink = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url);
    toast.success('Link copiado!');
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Certificado ${certificate?.certificate_number}`,
          text: 'Validação de certificado digital',
          url: window.location.href,
        });
      } catch (err) {
        // User cancelled
      }
    } else {
      handleCopyLink();
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      return new Date(dateString).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  // Determinar status do certificado para o badge
  const getCertificateStatus = () => {
    if (!validation) return 'checking';
    if (validation.status === 'revoked') return 'revoked';
    if (validation.status === 'expired') return 'expired';
    if (validation.days_remaining !== null && validation.days_remaining <= 30) return 'expiring';
    return 'valid';
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-950 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-gray-700 border-t-green-500 rounded-full animate-spin mx-auto" />
          </div>
          <p className="mt-4 text-gray-400">Verificando certificado...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-950 flex items-center justify-center p-4">
        <Card className="max-w-md w-full bg-gray-800 border-red-500/50">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Shield className="w-8 h-8 text-red-500" />
            </div>
            <h1 className="text-xl font-bold text-white mb-2">Certificado Inválido</h1>
            <p className="text-gray-400 mb-6">{error}</p>
            <Button 
              variant="outline" 
              onClick={() => window.location.reload()}
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              Tentar novamente
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-green-500" />
            <span className="font-bold text-white">CERTIFICADO DIGITAL</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <QrCode className="w-4 h-4" />
            <span className="hidden sm:inline">Validação Online</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Status Badge Principal */}
        <div className="flex justify-center mb-8">
          <StatusBadge 
            certificateStatus={getCertificateStatus()}
            serverStatus={serverStatus}
            daysRemaining={validation?.days_remaining}
          />
        </div>

        {/* Timestamp de verificação */}
        <div className="text-center mb-8">
          <p className="text-sm text-gray-500">
            Verificado em {new Date().toLocaleString('pt-BR')}
          </p>
        </div>

        {/* Dados do Certificado */}
        <Card className="bg-gray-800/50 border-gray-700 mb-6">
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
              <Hash className="w-5 h-5 text-green-500" />
              Dados do Certificado
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Número do Certificado */}
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center flex-shrink-0">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Número do Certificado</p>
                  <p className="text-white font-mono font-bold">{certificate?.certificate_number}</p>
                </div>
              </div>

              {/* Cliente */}
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Cliente</p>
                  <p className="text-white font-semibold">{certificate?.client_name}</p>
                </div>
              </div>

              {/* Produto */}
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center flex-shrink-0">
                  <Package className="w-5 h-5 text-purple-500" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Produto</p>
                  <p className="text-white font-semibold">{certificate?.product_name}</p>
                </div>
              </div>

              {/* Serial */}
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                  <Hash className="w-5 h-5 text-amber-500" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Serial Number</p>
                  <p className="text-white font-mono">{certificate?.serial_number}</p>
                </div>
              </div>

              {/* Região */}
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center flex-shrink-0">
                  <MapPin className="w-5 h-5 text-cyan-500" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Região</p>
                  <p className="text-white">{certificate?.region}</p>
                </div>
              </div>

              {/* Validade */}
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center flex-shrink-0">
                  <Calendar className="w-5 h-5 text-red-500" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Válido até</p>
                  <p className="text-white font-semibold">{formatDate(certificate?.expiration_date)}</p>
                </div>
              </div>
            </div>

            {/* Credenciais (parcialmente ocultas) */}
            {certificate?.credentials && (
              <div className="mt-6 p-4 bg-gray-900/50 rounded-lg border border-gray-700">
                <p className="text-sm text-gray-400 mb-3 flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Credenciais de Acesso
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-500">Login</p>
                    <p className="text-white font-mono">{certificate.credentials.login}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Senha</p>
                    <p className="text-white font-mono">{certificate.credentials.password}</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Ações */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button 
            onClick={handleDownloadPDF}
            className="bg-green-600 hover:bg-green-700 text-white"
            data-testid="download-pdf-btn"
          >
            <Download className="w-4 h-4 mr-2" />
            Baixar PDF
          </Button>
          
          <Button 
            variant="outline"
            onClick={handleCopyLink}
            className="border-gray-600 text-gray-300 hover:bg-gray-800"
            data-testid="copy-link-btn"
          >
            <Copy className="w-4 h-4 mr-2" />
            Copiar Link
          </Button>
          
          <Button 
            variant="outline"
            onClick={handleShare}
            className="border-gray-600 text-gray-300 hover:bg-gray-800"
            data-testid="share-btn"
          >
            <Share2 className="w-4 h-4 mr-2" />
            Compartilhar
          </Button>
        </div>

        {/* Hash de validação */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-500 mb-1">Hash de validação</p>
          <p className="text-xs font-mono text-gray-600 break-all px-4">
            sha256:{certificate?.hash}
          </p>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-sm text-gray-500">
          <p>Emitido por {certificate?.issued_by_name}</p>
          <p>em {formatDate(certificate?.issued_at)}</p>
        </footer>
      </main>
    </div>
  );
};

export default CertificateValidation;
