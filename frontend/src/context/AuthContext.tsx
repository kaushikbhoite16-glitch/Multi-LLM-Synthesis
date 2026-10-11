import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { apiService } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName?: string) => Promise<void>;
  googleLogin: (credential?: string, email?: string, fullName?: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    const storedToken = localStorage.getItem('access_token');
    if (!storedToken) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const profile = await apiService.getMe();
      setUser(profile);
      setToken(storedToken);
    } catch (err) {
      console.warn('Session expired or invalid token:', err);
      apiService.logout();
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (email: string, password: string) => {
    const authData = await apiService.login({ email, password });
    setToken(authData.access_token);
    setUser(authData.user);
  };

  const signUp = async (email: string, password: string, fullName?: string) => {
    const authData = await apiService.signUp({ email, password, full_name: fullName });
    setToken(authData.access_token);
    setUser(authData.user);
  };

  const googleLogin = async (credential?: string, email?: string, fullName?: string) => {
    const authData = await apiService.googleLogin({
      credential,
      email: email || 'user@gmail.com',
      full_name: fullName || 'Google User'
    });
    setToken(authData.access_token);
    setUser(authData.user);
  };

  const logout = () => {
    apiService.logout();
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        signUp,
        googleLogin,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
