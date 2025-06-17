"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { token, user, logout, isLoading } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout(); // Clears token from context and localStorage
    router.push('/login'); // Redirect to login page
  };

  const linkClassName = "px-3 py-2 rounded-md text-sm font-medium hover:text-gray-300";
  const buttonClassName = "px-3 py-2 rounded-md text-sm font-medium hover:text-gray-300"; // Similar style for button

  if (isLoading) {
    // Optional: Render a loading state or a minimal navbar
    return (
      <nav>
        <ul className="flex space-x-4">
          <li><Link href="/" className={linkClassName}>Home</Link></li>
          <li className="px-3 py-2 rounded-md text-sm font-medium">Loading...</li>
        </ul>
      </nav>
    );
  }

  return (
    <nav>
      <ul className="flex space-x-4 items-center">
        <li>
          <Link href="/" className={linkClassName}>
            Home
          </Link>
        </li>
        {token ? (
          <>
            <li>
              <Link href="/dashboard" className={linkClassName}>
                Dashboard
              </Link>
            </li>
            {user && ( // Display username if user object is available
              <li className="text-sm font-medium">
                Hi, {user.username}
              </li>
            )}
            <li>
              <button onClick={handleLogout} className={buttonClassName}>
                Logout
              </button>
            </li>
          </>
        ) : (
          <>
            <li>
              <Link href="/login" className={linkClassName}>
                Login
              </Link>
            </li>
            <li>
              <Link href="/register" className={linkClassName}>
                Register
              </Link>
            </li>
          </>
        )}
      </ul>
    </nav>
  );
}
