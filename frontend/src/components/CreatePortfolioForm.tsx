"use client";

import { useState, FormEvent } from "react";
import { createPortfolio, Portfolio, PortfolioCreatePayload } from "../services/portfolioService";
import { useAuth } from "../context/AuthContext";

interface CreatePortfolioFormProps {
  onPortfolioCreated: (newPortfolio: Portfolio) => void;
}

export default function CreatePortfolioForm({ onPortfolioCreated }: CreatePortfolioFormProps) {
  const [portfolioName, setPortfolioName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { token } = useAuth();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token) {
      setError("You must be logged in to create a portfolio.");
      return;
    }
    if (!portfolioName.trim()) {
      setError("Portfolio name cannot be empty.");
      return;
    }

    setIsLoading(true);
    setError(null);

    const payload: PortfolioCreatePayload = { portfolio_name: portfolioName };

    try {
      const result = await createPortfolio(token, payload);
      if (result.success) {
        onPortfolioCreated(result.data);
        setPortfolioName(""); // Clear form
      } else {
        setError(result.message || "Failed to create portfolio.");
      }
    } catch (err) {
      console.error("Create portfolio catch block error:", err);
      setError("An unexpected error occurred while creating the portfolio.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
      <h2 className="text-2xl font-semibold mb-6 text-center text-gray-800 dark:text-gray-100">
        Create New Portfolio
      </h2>
      <form onSubmit={handleSubmit} className="space-y-6 bg-white dark:bg-gray-800 p-8 shadow-xl rounded-lg">
        {error && (
          <div className="p-3 mb-4 text-sm text-red-700 bg-red-100 rounded-lg dark:bg-red-200 dark:text-red-800" role="alert">
            {error}
          </div>
        )}
        <div>
          <label
            htmlFor="portfolioName"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Portfolio Name
          </label>
          <input
            type="text"
            id="portfolioName"
            value={portfolioName}
            onChange={(e) => setPortfolioName(e.target.value)}
            required
            disabled={isLoading}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white disabled:opacity-50"
            placeholder="e.g., My Tech Stocks"
          />
        </div>
        <div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 dark:focus:ring-offset-gray-800 disabled:bg-green-400 disabled:cursor-not-allowed"
          >
            {isLoading ? "Creating..." : "Create Portfolio"}
          </button>
        </div>
      </form>
    </div>
  );
}
