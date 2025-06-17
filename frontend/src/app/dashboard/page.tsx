"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { useRouter } from "next/navigation";
import Link from "next/link"; // Import Link
import { getUserPortfolios, Portfolio } from "../../services/portfolioService";
import CreatePortfolioForm from "../../components/CreatePortfolioForm";

export default function DashboardPage() {
  const { token, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();

  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [isLoadingPortfolios, setIsLoadingPortfolios] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthLoading && !token) {
      router.push('/login');
    }

    if (!isAuthLoading && token) {
      const fetchPortfolios = async () => {
        setIsLoadingPortfolios(true);
        setError(null);
        const result = await getUserPortfolios(token);
        if (result.success) {
          setPortfolios(result.data);
        } else {
          setError(result.message);
        }
        setIsLoadingPortfolios(false);
      };
      fetchPortfolios();
    } else if (!isAuthLoading && !token) {
      setIsLoadingPortfolios(false);
    }
  }, [isAuthLoading, token, router]);

  const handlePortfolioCreated = (newPortfolio: Portfolio) => {
    setPortfolios(prevPortfolios => [newPortfolio, ...prevPortfolios]);
    // Optionally, could also add a success message or toggle form visibility here
  };

  if (isAuthLoading || !token) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-10rem)]">
        <p className="text-gray-500 dark:text-gray-400">Loading session...</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-gray-700 dark:text-gray-200">Dashboard</h1>
      <p className="mb-6 text-gray-800 dark:text-gray-300">
        Welcome to your dashboard. This page is protected.
      </p>

      <section className="mb-12">
        {/* Pass the callback function to the form */}
        <CreatePortfolioForm onPortfolioCreated={handlePortfolioCreated} />
      </section>

      <section>
        <h2 className="text-2xl font-semibold mb-4 text-gray-700 dark:text-gray-200">Your Portfolios</h2>
        {isLoadingPortfolios ? (
          <p className="text-gray-500 dark:text-gray-400">Loading portfolios...</p>
        ) : error ? (
          <div className="p-3 text-sm text-red-700 bg-red-100 rounded-lg dark:bg-red-200 dark:text-red-800" role="alert">
            Error fetching portfolios: {error}
          </div>
        ) : portfolios.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400">No portfolios yet. Create one to get started!</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {portfolios.map((portfolio) => (
              <div
                key={portfolio.portfolio_id}
                className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow flex flex-col justify-between"
              >
                <div>
                  <h3 className="text-xl font-semibold mb-2 text-indigo-600 dark:text-indigo-400">{portfolio.portfolio_name}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">ID: {portfolio.portfolio_id}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                    Created: {new Date(portfolio.created_at).toLocaleDateString()}
                  </p>
                </div>
                <Link
                  href={`/portfolios/${portfolio.portfolio_id}`}
                  className="mt-auto inline-block text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 self-start"
                >
                  View Details &rarr;
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
