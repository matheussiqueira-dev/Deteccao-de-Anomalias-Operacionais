import React, { useState } from "react";

type Props = {
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  onLogin: (username: string, password: string) => Promise<boolean>;
  onLogout: () => void;
};

const AuthPanel: React.FC<Props> = ({ isAuthenticated, loading, error, onLogin, onLogout }) => {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("radar");

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    await onLogin(username, password);
  };

  return (
    <div className="auth-panel">
      <div className="auth-header">
        <h4>Autenticação</h4>
        <span className={isAuthenticated ? "auth-pill ok" : "auth-pill warn"}>
          {isAuthenticated ? "Conectado" : "Opcional"}
        </span>
      </div>
      {!isAuthenticated ? (
        <form className="auth-form" onSubmit={handleSubmit}>
          <input
            className="auth-input"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="usuário"
            autoComplete="username"
          />
          <input
            className="auth-input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="senha"
            autoComplete="current-password"
          />
          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? "Autenticando..." : "Login"}
          </button>
          {error && <span className="auth-error">{error}</span>}
        </form>
      ) : (
        <div className="auth-actions">
          <span className="auth-info">Token JWT ativo</span>
          <button type="button" className="auth-button ghost" onClick={onLogout}>
            Logout
          </button>
        </div>
      )}
    </div>
  );
};

export default AuthPanel;