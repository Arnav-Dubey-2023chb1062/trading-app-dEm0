"use client";

import { useEffect, useState, useCallback } from "react"; // Import useCallback
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../../context/AuthContext";
import { Portfolio, Holding, getUserPortfolios, getPortfolioHoldings } from "../../../services/portfolioService";
import TradeForm from "../../../components/TradeForm";
import { TradeResponse } from "../../../services/tradeService"; // For onTradeSuccess type

export default function PortfolioDetailPage() {
  const { token, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const portfolioId = params.portfolioId as string;

  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [isLoadingPageData, setIsLoadingPageData] = useState(true); // Covers both portfolio and holdings initial load
  const [error, setError] = useState<string | null>(null);
  // State to trigger re-fetch of holdings after a trade
  const [refreshHoldingsKey, setRefreshHoldingsKey] = useState(0);


  const fetchPortfolioAndHoldings = useCallback(async () => {
    if (!token || !portfolioId) return;

    setIsLoadingPageData(true);
    setError(null);
    const id = Number(portfolioId);

    try {
      // Fetch portfolio details
      const portfoliosResult = await getUserPortfolios(token); // Assuming this also gets the specific one if already called
      if (portfoliosResult.success) {
        const currentPortfolio = portfoliosResult.data.find(p => p.portfolio_id === id);
        if (currentPortfolio) {
          setPortfolio(currentPortfolio);
        } else {
          setError("Portfolio not found or you do not have access.");
          setIsLoadingPageData(false);
          return;
        }
      } else {
        setError(portfoliosResult.message || "Failed to fetch portfolio details.");
        setIsLoadingPageData(false);
        return;
      }

      // Fetch holdings
      const holdingsResult = await getPortfolioHoldings(token, id);
      if (holdingsResult.success) {
        setHoldings(holdingsResult.data);
      } else {
        setError(holdingsResult.message || "Failed to fetch holdings.");
      }
    } catch (e) {
      console.error("Error fetching portfolio/holdings data", e);
      setError("An unexpected error occurred.");
    } finally {
      setIsLoadingPageData(false);
    }
  }, [token, portfolioId]); // Removed router from here if not directly used for navigation inside

  useEffect(() => {
    if (isAuthLoading) return;

    if (!token) {
      router.push('/login');
      return;
    }
    fetchPortfolioAndHoldings();
  }, [isAuthLoading, token, portfolioId, router, fetchPortfolioAndHoldings, refreshHoldingsKey]); // Added fetchPortfolioAndHoldings and refreshHoldingsKey

  const handleTradeSuccess = (tradeData: TradeResponse) => {
    console.log("Trade successful in page:", tradeData);
    alert(`Trade executed: ${tradeData.trade_type} ${tradeData.quantity} of ${tradeData.ticker_symbol} @ ${tradeData.price}`);
    // Trigger a re-fetch of holdings by changing the key
    setRefreshHoldingsKey(prevKey => prevKey + 1);
  };

  if (isAuthLoading || isLoadingPageData) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-10rem)]">
        <p className="text-gray-500 dark:text-gray-400">Loading data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-10rem)]">
        <h1 className="text-2xl font-semibold mb-4 text-red-600">Error</h1>
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  if (!portfolio) {
    // Should be caught by error state if not found, but as a fallback
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-10rem)]">
        <p className="text-gray-500 dark:text-gray-400">Portfolio not found.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2 text-gray-800 dark:text-gray-100">
        Portfolio: {portfolio.portfolio_name}
      </h1>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
        ID: {portfolio.portfolio_id} | Created: {new Date(portfolio.created_at).toLocaleDateString()}
      </p>

      <section className="my-8 md:flex md:space-x-8">
        <div className="md:w-1/2 lg:w-2/3"> {/* Holdings display area */}
          <h2 className="text-2xl font-semibold mb-4 text-gray-700 dark:text-gray-200">Holdings</h2>
          {holdings.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400">No holdings in this portfolio yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white dark:bg-gray-800 shadow-md rounded-lg">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="py-3 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Ticker</th>
                  <th className="py-3 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Quantity</th>
                  <th className="py-3 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Avg. Buy Price</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {holdings.map((holding) => (
                  <tr key={holding.holding_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="py-4 px-6 text-sm font-medium text-gray-900 dark:text-white">{holding.ticker_symbol}</td>
                    <td className="py-4 px-6 text-sm text-gray-500 dark:text-gray-300">{holding.quantity}</td>
                    <td className="py-4 px-6 text-sm text-gray-500 dark:text-gray-300">${parseFloat(holding.average_buy_price).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          )}
        </div>
        <div className="md:w-1/2 lg:w-1/3 mt-8 md:mt-0"> {/* Trade form area */}
          <TradeForm
            portfolioId={Number(portfolioId)}
            onTradeSuccess={handleTradeSuccess}
          />
        </div>
      </section>
    </div>
  );
}
