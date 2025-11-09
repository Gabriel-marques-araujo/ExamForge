import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import NavBar from "../NavBar/NavBar";
import "./ResultsPage.css";

const ResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const {
    score = 10.0,
    totalQuestions = 20,
    correctAnswers = 13,
    wrongAnswers = 7,
  } = location.state || {};

  const percentage = ((correctAnswers / totalQuestions) * 100).toFixed(0);

  const handleBackToStart = () => navigate("/");
  const handleReviewAnswers = () => navigate("/questions", { state: { mode: "review" } });
  const handleRetake = () => navigate("/questions");
  const handleExportPDF = () => {
    alert("Função de exportar PDF será implementada futuramente!");
  };

  return (
    <>
      <NavBar />

      <div className="results-container">
        <div className="results-card">
          <h1 className="results-title">SUA NOTA:</h1>
          <p className="results-score">{score.toFixed(1)}</p>

          <div className="results-summary">
            <div>
              <h3>{percentage}%</h3>
              <p>Completo</p>
            </div>
            <div>
              <h3>{totalQuestions}</h3>
              <p>Questões</p>
            </div>
          </div>

          <div className="results-details">
            <div>
              <h3>{correctAnswers}</h3>
              <p>Corretas</p>
            </div>
            <div>
              <h3>{wrongAnswers}</h3>
              <p>Erradas</p>
            </div>
          </div>

          <div className="results-actions">
            <button className="action-button" onClick={handleReviewAnswers}>
              Revisar Respostas
            </button>
            <button className="action-button" onClick={handleRetake}>
              Refazer Simulado
            </button>
            <button className="action-button" onClick={handleExportPDF}>
              Exportar PDF
            </button>
            <button className="restart-button" onClick={handleBackToStart}>
              Voltar ao Início
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default ResultsPage;
