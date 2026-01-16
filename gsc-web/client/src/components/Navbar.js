import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Home, 
  Wallet, 
  Zap, 
  Search, 
  Network,
  Activity
} from 'lucide-react';

const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/wallet', label: 'Wallet', icon: Wallet },
    { path: '/mining', label: 'Mining', icon: Zap },
    { path: '/explorer', label: 'Explorer', icon: Search },
    { path: '/network', label: 'Network', icon: Network },
  ];

  return (
    <nav className="navbar">
      <Link to="/dashboard" className="navbar-brand">
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          GSC COIN
        </motion.div>
      </Link>

      <ul className="navbar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <li key={item.path}>
              <Link 
                to={item.path} 
                className={`nav-link ${isActive ? 'active' : ''}`}
              >
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="nav-link-content"
                >
                  <Icon size={18} />
                  {item.label}
                </motion.div>
              </Link>
            </li>
          );
        })}
      </ul>

      <div className="navbar-status">
        <div className="status-indicator">
          <div className="status-dot"></div>
          <span>Network Active</span>
        </div>
        <div className="status-indicator">
          <Activity size={16} />
          <span>Live</span>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
