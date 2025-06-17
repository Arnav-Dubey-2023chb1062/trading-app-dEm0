"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../../context/AuthContext";
import { Portfolio, Holding, getUserPortfolios, getPortfolioHoldings } from "../../../services/portfolioService";
import { getTickerPrice } from "../../../services/marketService"; // Import market price service
import TradeForm from "../../../components/TradeForm";
import { TradeResponse } from "../../../services/tradeService";
import { formatCurrency } from "../../../utils/formatting"; // Import formatting utility

// Extended Holding type to include market data
interface ExtendedHolding extends Holding {
  current_price?: number | null;
  market_value?: number;
  unrealized_pnl?: number;
  price_source?: string;
}

export default function PortfolioDetailPage() {
  const { token, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const portfolioId = params.portfolioId as string;

  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  // Store original holdings and extended holdings separately or combine them
  const [holdingsWithMarketData, setHoldingsWithMarketData] = useState<ExtendedHolding[]>([]);
  const [isLoadingPageData, setIsLoadingPageData] = useState(true); // For initial portfolio and holdings load
  const [isLoadingMarketPrices, setIsLoadingMarketPrices] = useState(false); // For market price fetching
  const [error, setError] = useState<string | null>(null);
  const [refreshHoldingsKey, setRefreshHoldingsKey] = useState(0); // To trigger re-fetch

  const [totalPortfolioValue, setTotalPortfolioValue] = useState<number>(0);
  const [totalPortfolioPnl, setTotalPortfolioPnl] = useState<number>(0);


  const fetchPortfolioAndHoldings = useCallback(async () => {
    if (!token || !portfolioId) return;

    setIsLoadingPageData(true);
    setError(null);
    const id = Number(portfolioId);

    try {
      // Fetch portfolio details
      const portfoliosResult = await getUserPortfolios(token);
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
        // Now fetch market prices for these holdings
        setIsLoadingMarketPrices(true);
        const uniqueTickers = Array.from(new Set(holdingsResult.data.map(h => h.ticker_symbol)));
        const pricePromises = uniqueTickers.map(ticker => getTickerPrice(ticker)); // Assuming getTickerPrice doesn't need token if endpoint is public

        const priceResults = await Promise.allSettled(pricePromises);
        const pricesMap = new Map<string, { price: number; source: string }>();

        priceResults.forEach((result, index) => {
          const ticker = uniqueTickers[index];
          if (result.status === 'fulfilled' && result.value.success) {
            pricesMap.set(ticker, { price: parseFloat(result.value.data.price), source: result.value.data.source });
          } else {
            pricesMap.set(ticker, { price: NaN, source: result.status === 'fulfilled' ? result.value.message : "Fetch error" });
            console.error(`Failed to fetch price for ${ticker}:`, result.status === 'rejected' ? result.reason : result.value.message);
          }
        });

        let currentTotalValue = 0;
        let currentTotalPnl = 0;

        const extendedHoldings = holdingsResult.data.map((h): ExtendedHolding => {
          const marketData = pricesMap.get(h.ticker_symbol);
          const current_price = marketData && !isNaN(marketData.price) ? marketData.price : null;
          const avgBuyPrice = parseFloat(h.average_buy_price); // Parse string from API

          let market_value: number | undefined = undefined;
          let unrealized_pnl: number | undefined = undefined;

          if (current_price !== null) {
            market_value = h.quantity * current_price;
            unrealized_pnl = market_value - (avgBuyPrice * h.quantity);
            currentTotalValue += market_value;
            currentTotalPnl += unrealized_pnl;
          }

          return {
            ...h,
            average_buy_price: avgBuyPrice.toString(), // Keep as string for consistency if needed, or convert Holding interface
            current_price,
            market_value,
            unrealized_pnl,
            price_source: marketData?.source
          };
        });
        setHoldingsWithMarketData(extendedHoldings);
        setTotalPortfolioValue(currentTotalValue);
        setTotalPortfolioPnl(currentTotalPnl);
        setIsLoadingMarketPrices(false);

      } else {
        setError(holdingsResult.message || "Failed to fetch holdings.");
      }
    } catch (e) {
      console.error("Error fetching portfolio/holdings data", e);
      setError("An unexpected error occurred.");
    } finally {
      setIsLoadingPageData(false); // Initial page data load complete
    }
  }, [token, portfolioId]);

  useEffect(() => {
    if (isAuthLoading) return;

    if (!token) {
      router.push('/login');
      return;
    }
    fetchPortfolioAndHoldings();
  }, [isAuthLoading, token, portfolioId, router, fetchPortfolioAndHoldings, refreshHoldingsKey]);

  const handleTradeSuccess = (tradeData: TradeResponse) => {
    console.log("Trade successful in page:", tradeData);
    alert(`Trade executed: ${tradeData.trade_type} ${tradeData.quantity} of ${tradeData.ticker_symbol} @ ${tradeData.price}`);
    setRefreshHoldingsKey(prevKey => prevKey + 1);
  };

  if (isAuthLoading || isLoadingPageData) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-10rem)]">
        <p className="text-gray-500 dark:text-gray-400">Loading data...</p>
      </div>
    );
  }

  if (error && !portfolio) { // Show general error if portfolio details also failed
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-10rem)]">
        <h1 className="text-2xl font-semibold mb-4 text-red-600">Error</h1>
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-10rem)]">
        <p className="text-gray-500 dark:text-gray-400">Portfolio not found.</p>
      </div>
    );
  }

  const PnlComponent: React.FC<{ pnl: number | undefined | null }> = ({ pnl }) => {
    if (pnl === null || pnl === undefined || isNaN(pnl)) return <span className="text-gray-500 dark:text-gray-400">N/A</span>;
    const pnlColor = pnl >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400";
    return <span className={pnlColor}>{formatCurrency(pnl)}</span>;
  };


  return (
    <div>
      <h1 className="text-3xl font-bold mb-2 text-gray-800 dark:text-gray-100">
        Portfolio: {portfolio.portfolio_name}
      </h1>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
        ID: {portfolio.portfolio_id} | Created: {new Date(portfolio.created_at).toLocaleDateString()}
      </p>
      <p className="text-lg text-gray-700 dark:text-gray-300 mb-6">
        Cash Balance: <span className="font-semibold">{formatCurrency(parseFloat(portfolio.cash_balance))}</span>
      </p>

      <div className="mb-8 p-4 bg-white dark:bg-gray-800 shadow rounded-lg">
        <h2 className="text-xl font-semibold mb-2 text-gray-700 dark:text-gray-200">Portfolio Summary</h2>
        <p className="text-gray-600 dark:text-gray-300">
            Holdings Market Value: <span className="font-semibold">{formatCurrency(totalPortfolioValue)}</span>
        </p>
        <p className="text-gray-600 dark:text-gray-300">
            Total Portfolio Value (Holdings + Cash): <span className="font-semibold">{formatCurrency(totalPortfolioValue + parseFloat(portfolio.cash_balance))}</span>
        </p>
        <p className="text-gray-600 dark:text-gray-300">
            Total Unrealized P&L (Holdings): <PnlComponent pnl={totalPortfolioPnl} />
        </p>
        {isLoadingMarketPrices && <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Updating market values...</p>}
      </div>

      {error && ( // Display error related to holdings/prices if portfolio itself loaded
          <div className="p-3 mb-4 text-sm text-red-700 bg-red-100 rounded-lg dark:bg-red-200 dark:text-red-800" role="alert">
            {error}
          </div>
        )}

      <section className="my-8 md:flex md:space-x-8">
        <div className="md:w-2/3"> {/* Holdings display area */}
          <h2 className="text-2xl font-semibold mb-4 text-gray-700 dark:text-gray-200">Holdings</h2>
          {isLoadingMarketPrices && holdingsWithMarketData.length === 0 && <p className="text-gray-500 dark:text-gray-400">Fetching market prices for holdings...</p>}
          {!isLoadingMarketPrices && holdingsWithMarketData.length === 0 && !error && (
            <p className="text-gray-500 dark:text-gray-400">No holdings in this portfolio yet.</p>
          )}
          {holdingsWithMarketData.length > 0 && (
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white dark:bg-gray-800 shadow-md rounded-lg">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Ticker</th>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Quantity</th>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Avg. Buy Price</th>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Current Price</th>
                    <th className="py-3 px-4 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Market Value</th>
                    <th className="py-3 px-6 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Unrealized P&L</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {holdingsWithMarketData.map((holding) => (
                    <tr key={holding.holding_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="py-4 px-4 text-sm font-medium text-gray-900 dark:text-white">{holding.ticker_symbol}</td>
                      <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{holding.quantity}</td>
                      <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{formatCurrency(parseFloat(holding.average_buy_price))}</td>
                      <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{formatCurrency(holding.current_price)} <span className="text-xs">({holding.price_source || 'N/A'})</span></td>
                      <td className="py-4 px-4 text-sm text-gray-500 dark:text-gray-300">{formatCurrency(holding.market_value)}</td>
                      <td className="py-4 px-6 text-sm"><PnlComponent pnl={holding.unrealized_pnl} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <div className="md:w-1/3 mt-8 md:mt-0"> {/* Trade form area */}
          <TradeForm
            portfolioId={Number(portfolioId)}
            onTradeSuccess={handleTradeSuccess}
          />
        </div>
      </section>
    </div>
  );
}
