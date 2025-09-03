import React, { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { inviteHelpers } from "../api";

function useQuery() {
  const { search } = useLocation();
  return useMemo(() => new URLSearchParams(search), [search]);
}

export default function AcceptInvitePage() {
  const q = useQuery();
  const token = q.get("token") || "";
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    if (!token) setError("Token de convite ausente na URL.");
  }, [token]);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const resp = await inviteHelpers.acceptInvite(token, password || undefined);
      setSuccess(resp?.user || { ok: true });
      // Opcional: redirecionar para login
      // setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || "Falha ao aceitar convite";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Aceitar Convite
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Complete o processo para acessar o sistema
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {!success && (
            <form onSubmit={onSubmit} className="space-y-6">
              <div>
                <label htmlFor="token" className="block text-sm font-medium text-gray-700">
                  Token do Convite
                </label>
                <input
                  id="token"
                  type="text"
                  value={token}
                  disabled
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-100 text-sm"
                />
                <p className="mt-1 text-xs text-gray-500">
                  {token ? "Token detectado automaticamente" : "Token não encontrado na URL"}
                </p>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Senha (opcional)
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Defina uma senha (opcional)"
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Se não definir agora, poderá definir mais tarde
                </p>
              </div>

              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <div className="text-sm text-red-700">{error}</div>
                </div>
              )}

              <button
                type="submit"
                disabled={!token || loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Processando..." : "Aceitar convite"}
              </button>
            </form>
          )}

          {success && (
            <div className="rounded-md bg-green-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">
                    Convite aceito com sucesso!
                  </h3>
                  <div className="mt-2 text-sm text-green-700">
                    <p>
                      Usuário criado/vinculado com sucesso. Você já pode fazer login no sistema.
                    </p>
                  </div>
                  <div className="mt-4">
                    <button
                      onClick={() => navigate("/login")}
                      className="text-sm bg-green-100 text-green-800 rounded-md px-3 py-1 hover:bg-green-200"
                    >
                      Ir para login
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}