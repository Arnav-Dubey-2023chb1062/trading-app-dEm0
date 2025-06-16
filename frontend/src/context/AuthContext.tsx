"use client";

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react"; // Added useCallback
import { useRouter } from "next/navigation"; // For potential redirection within context
import { getMe } from "../services/authService"; // Import getMe

// Define User type (consistent with backend Pydantic User model)
export interface User {
  user_id: number; // Matches Pydantic User.user_id
  username: string;
  email: string;
  created_at?: Date | string; // Optional, and can be string if not parsed
}

// Define AuthContextType
interface AuthContextType {
  token: string | null;
  user: User | null;
  isLoading: boolean; // To check if context is still loading token/user from storage/API
  login: (newToken: string, userData?: User) => void; // userData is optional for now
  logout: () => void;
}

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Create AuthProvider component
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter(); // Can be used for global redirects on logout/auth failure

  const fetchUserDetails = useCallback(async (currentToken: string) => {
    setIsLoading(true); // Indicate loading of user details
    const result = await getMe(currentToken);
    if (result.success) {
      setUser(result.data);
    } else {
      // If getMe fails (e.g. token invalid), logout to clear state
      console.error("Failed to fetch user details:", result.message);
      localStorage.removeItem('authToken'); // Ensure token is cleared
      setToken(null);
      setUser(null);
      // Optionally redirect to login if critical, or let components handle it
      // router.push('/login');
    }
    setIsLoading(false);
  }, []); // No dependencies like router if not used inside for now

  useEffect(() => {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      setToken(storedToken);
      fetchUserDetails(storedToken);
    } else {
      setIsLoading(false); // No token, so not loading user details
    }
  }, [fetchUserDetails]); // Include fetchUserDetails in dependency array

  const login = useCallback(async (newToken: string, userData?: User) => {
    localStorage.setItem('authToken', newToken);
    setToken(newToken);
    if (userData) {
      setUser(userData);
      // If user data is provided directly (e.g. from registration response),
      // no need to fetch again immediately.
      // However, typically login response is just a token.
    } else {
      // Fetch user details after setting the new token
      await fetchUserDetails(newToken);
    }
    // Redirection is currently handled by the page component after calling login.
  }, [fetchUserDetails]);

  const logout = useCallback(() => {
    localStorage.removeItem('authToken');
    setToken(null);
    setUser(null);
    router.push('/login'); // Redirect to login on logout for better UX
  }, [router]);

  return (
    <AuthContext.Provider value={{ token, user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Create custom hook useAuth
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
