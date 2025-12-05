import "./NavBar.css";
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

interface NavBarProps {
  className?: string;
  onThemeChange?: (isDark: boolean) => void;
}

const NavBar: React.FC<NavBarProps> = ({ className, onThemeChange }) => {
  const navigate = useNavigate(); // hook para navegar
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("theme") === "dark";
  });

  useEffect(() => {
    document.body.classList.toggle("dark", darkMode);
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  if (onThemeChange) onThemeChange(darkMode);
  }, [darkMode, onThemeChange]);


  return (
    <header className={`navbar ${className || ""}`}>
      <div className="navbar-list">
        <div
          className="navbar-title"
          style={{ cursor: "pointer" }}
          onClick={() => navigate("/")}
        >
          <img src="/title.svg" alt="ExamForge" className="navbar-logo" />
        </div>

        <button
          className="dark-mode-toggle"
          onClick={() => setDarkMode(!darkMode)}
          aria-label="Alternar modo escuro"
        >
          <img
            src={darkMode ? "/lightmode.svg" : "/darkmode.svg"}
            alt={darkMode ? "Modo claro" : "Modo escuro"}
            className="navbar-mode"
          />
        </button>
      </div>
    </header>
  );
};

export default NavBar;
