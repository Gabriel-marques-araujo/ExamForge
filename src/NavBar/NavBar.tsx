import "./NavBar.css";
import React from "react";

// falta implementar o on click do modo escuro

const NavBar = () => {
  return (
    <header className="navbar">
        <div className="navbar-list">
            <div className="navbar-title">
                <div className="navbar-title">
                    <img
                    src="/title.svg"
                    alt="ExamForge"
                    className="navbar-logo"
                    />
                </div>
            </div>
            <button className="dark-mode-toggle">                    
                <img
                    src="/darkmode.svg"
                    alt="dark mode"
                    className="navbar-mode"
                />
            </button>
        </div>    
    </header>
  );
};

export default NavBar;
