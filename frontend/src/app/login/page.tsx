"use client"; // Required for useState and event handlers

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation"; // Import useRouter
import { loginUser, ApiErrorResponse } from "../../services/authService"; // Import loginUser and error type

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null); // For displaying login errors
  const [isLoading, setIsLoading] = useState(false); // For loading state
  const router = useRouter();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const result = await loginUser({ username, password });

      if (result.success) {
        // Assuming TokenResponse is the type of result.data when success is true
        localStorage.setItem('authToken', result.data.access_token);
        router.push('/dashboard');
      } else {
        // ApiErrorResponse already has a message property
        setError(result.message);
      }
    } catch (err) {
      // This catch block might be redundant if loginUser always returns a structured response
      // However, it's good for unexpected errors during the service call itself.
      setError("An unexpected error occurred. Please try again.");
      console.error("Login page catch block error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-start pt-10 min-h-[calc(100vh-10rem)]">
      <div className="w-full max-w-md">
        <h1 className="text-3xl font-bold mb-8 text-center text-gray-800 dark:text-gray-100">Login</h1>
        <form onSubmit={handleSubmit} className="space-y-6 bg-white dark:bg-gray-800 p-8 shadow-xl rounded-lg">
          {error && (
            <div className="p-3 mb-4 text-sm text-red-700 bg-red-100 rounded-lg dark:bg-red-200 dark:text-red-800" role="alert">
              {error}
            </div>
          )}

          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Username
            </label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={isLoading}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white disabled:opacity-50"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white disabled:opacity-50"
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:focus:ring-offset-gray-800 disabled:bg-indigo-400 disabled:cursor-not-allowed"
            >
              {isLoading ? "Logging in..." : "Login"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
