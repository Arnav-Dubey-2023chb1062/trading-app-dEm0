"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation"; // For potential redirection within context

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
  const [isLoading, setIsLoading] = useState(true); // Start true, set false after initial load
  const router = useRouter();

  useEffect(() => {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      setToken(storedToken);
      // TODO (Future Enhancement):
      // Here, you would typically verify the token and fetch user details
      // For example:
      // async function fetchUser() {
      //   try {
      //     // Assume you have an API endpoint like /users/me
      //     // const response = await api.get('/users/me', { headers: { Authorization: `Bearer ${storedToken}` } });
      //     // setUser(response.data);
      //   } catch (error) {
      //     console.error("Failed to fetch user on initial load", error);
      //     localStorage.removeItem('authToken'); // Clear invalid token
      //     setToken(null);
      //   } finally {
      //     setIsLoading(false);
      //   }
      // }
      // fetchUser();
      // For now, just set a placeholder user if token exists or leave user null
      // If you decode the token and it has user info, you can use that:
      // e.g. const decodedUser = jwt_decode(storedToken); setUser(decodedUser);
    }
    setIsLoading(false); // Set loading to false after attempting to load token
  }, []);

  const login = (newToken: string, userData?: User) => {
    localStorage.setItem('authToken', newToken);
    setToken(newToken);
    if (userData) {
      setUser(userData);
    }
    // TODO (Future Enhancement):
    // If userData is not passed, fetch user details from API using newToken
    // Example:
    // async function fetchAndSetUser() {
    //   try {
    //     // const response = await api.get('/users/me', { headers: { Authorization: `Bearer ${newToken}` } });
    //     // setUser(response.data);
    //   } catch (error) {
    //     console.error("Failed to fetch user on login", error);
    //   }
    // }
    // if (!userData) fetchAndSetUser();

    // Redirection could also be handled here globally, or per-page as it is now.
    // router.push('/dashboard');
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setToken(null);
    setUser(null);
    // router.push('/login'); // Optionally redirect to login on logout
  };

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
