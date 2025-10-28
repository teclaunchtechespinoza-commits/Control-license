import React, { useState, useEffect } from "react";
import { inviteHelpers } from "../api";

export default function AdminInvitePage() {
  const [email, setEmail] = useState("");
  const [invites, setInvites] = useState([]);
  const [inviteLink, setInviteLink] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [revoking, setRevoking] = useState(false);
  const [loadingList, setLoadingList] = useState(true);

  // Carregar lista de convites ao montar o componente
  useEffect(() => {
    loadInvites();
  }, []);

  const loadInvites = async () => {
    setLoadingList(true);
    try {
      const data = await inviteHelpers.listInvitations();
      setInvites(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load invites:", err);
      setError("Erro ao carregar convites existentes");
    } finally {
      setLoadingList(false);
    }
  };

  const onCreate = async (e) => {
    e.preventDefault();
    setError("");
    setInviteLink("");
    setLoading(true);
    try {
      const resp = await inviteHelpers.createInvitation(email.trim());
      setInviteLink(resp?.invite_link || "");
      setEmail(""); // Limpar campo após sucesso
      // Recarregar lista
      await loadInvites();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || "Falha ao criar convite";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const onRevoke = async (token) => {
    setRevoking(true);
    setError("");
    try {
      await inviteHelpers.revokeInvitation(token);
      setInviteLink(""); // Limpar link se foi o que acabou de criar
      // Recarregar lista
      await loadInvites();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || "Falha ao revogar convite";
      setError(errorMessage);
    } finally {
      setRevoking(false);
    }
  };

  const onDelete = async (token) => {
    if (!window.confirm("Tem certeza que deseja excluir este convite?")) {
      return;
    }
    
    setError("");
    try {
      await inviteHelpers.deleteInvitation(token);
      await loadInvites();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || "Falha ao excluir convite";
      setError(errorMessage);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert("Link copiado para a área de transferência!");
    }).catch(() => {
      alert("Erro ao copiar link");
    });
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return "N/A";
    return new Date(timestamp * 1000).toLocaleString('pt-BR');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Gerenciar Convites (Admin)
            </h2>

            {/* Formulário para criar novo convite */}
            <div className="mb-8">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Criar Novo Convite
              </h3>
              <form onSubmit={onCreate} className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                    E-mail do cliente
                  </label>
                  <input
                    id="email"
                    type="email"
                    required
                    placeholder="cliente@empresa.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>

                {error && (
                  <div className="rounded-md bg-red-50 p-4">
                    <div className="text-sm text-red-700">{error}</div>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {loading ? "Enviando..." : "Gerar convite"}
                </button>
              </form>

              {/* Link gerado */}
              {inviteLink && (
                <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"/>
                      </svg>
                    </div>
                    <div className="ml-3 flex-1">
                      <h4 className="text-sm font-medium text-blue-800">
                        Link de convite gerado:
                      </h4>
                      <div className="mt-2 text-sm text-blue-700 break-all bg-white p-2 rounded border">
                        {inviteLink}
                      </div>
                      <div className="mt-3 space-x-2">
                        <button
                          onClick={() => copyToClipboard(inviteLink)}
                          className="text-sm bg-blue-100 text-blue-800 rounded-md px-3 py-1 hover:bg-blue-200"
                        >
                          Copiar link
                        </button>
                        <button
                          onClick={() => {
                            const url = new URL(inviteLink);
                            const token = url.searchParams.get("token");
                            if (token) onRevoke(token);
                          }}
                          disabled={revoking}
                          className="text-sm bg-red-100 text-red-800 rounded-md px-3 py-1 hover:bg-red-200 disabled:opacity-50"
                        >
                          {revoking ? "Revogando..." : "Revogar convite"}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Lista de convites existentes */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Convites Existentes
              </h3>
              
              {loadingList ? (
                <div className="text-center py-4">
                  <div className="text-sm text-gray-500">Carregando convites...</div>
                </div>
              ) : invites.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-sm text-gray-500">Nenhum convite encontrado</div>
                </div>
              ) : (
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                  <table className="min-w-full divide-y divide-gray-300">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Email
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Criado em
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Ações
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {invites.map((invite, index) => (
                        <tr key={index}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {invite.email}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(invite.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              invite.used_at 
                                ? 'bg-green-100 text-green-800' 
                                : invite.revoked 
                                ? 'bg-red-100 text-red-800'
                                : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {invite.used_at ? 'Usado' : invite.revoked ? 'Revogado' : 'Pendente'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div className="flex gap-2">
                              {!invite.used_at && !invite.revoked && (
                                <>
                                  <button
                                    onClick={() => {
                                      const inviteUrl = `${window.location.origin}/accept-invite?token=${invite.token_hash}`;
                                      copyToClipboard(inviteUrl);
                                    }}
                                    className="text-blue-600 hover:text-blue-900 font-medium"
                                  >
                                    Copiar Link
                                  </button>
                                  <span className="text-gray-300">|</span>
                                  <button
                                    onClick={() => onRevoke(invite.token_hash)}
                                    disabled={revoking}
                                    className="text-orange-600 hover:text-orange-900 disabled:opacity-50 font-medium"
                                  >
                                    Revogar
                                  </button>
                                  <span className="text-gray-300">|</span>
                                </>
                              )}
                              <button
                                onClick={() => onDelete(invite.token_hash)}
                                className="text-red-600 hover:text-red-900 font-medium"
                              >
                                Excluir
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}