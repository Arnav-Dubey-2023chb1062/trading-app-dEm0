"use client"; // Required for hooks

import { useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const { token, isLoading: isAuthLoading } = useAuth(); // Renamed isLoading to avoid conflict if page has its own
  const router = useRouter();

  useEffect(() => {
    // Only redirect if auth loading is complete and there's no token.
    if (!isAuthLoading && !token) {
      router.push('/login');
    }
  }, [isAuthLoading, token, router]); // Dependencies for the effect

  // Render loading state or null while auth is loading or if there's no token (before redirect happens)
  if (isAuthLoading || !token) {
    // You can also return a more sophisticated loading spinner component
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-10rem)]">
        <p className="text-gray-500 dark:text-gray-400">Loading...</p>
      </div>
    );
  }

  // If loading is complete and token exists, render the dashboard content
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-gray-700 dark:text-gray-200">Dashboard</h1>
      <p className="text-gray-800 dark:text-gray-300">
        Welcome to your dashboard. This page is protected.
      </p>
      {/* Placeholder for more dashboard content */}
    </div>
  );
}
